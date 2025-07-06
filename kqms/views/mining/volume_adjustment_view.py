from django.contrib.auth.decorators import login_required
from django.db import connections
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from ...models.mine_addition_factor import volumeTruckFactorAdjustment,mineVolumeAdjustment
from ...models.mine_productions import mineProductions
from ...models.source_model import SourceMines,SourceMinesLoading
from ...models.materials import Material
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.db.models import F  # Import F for field references
import json
import logging
from ...utils.utils import clean_string
logger = logging.getLogger(__name__)

@login_required
def volume_adjustment_page(request):
    return render(request, 'admin-mine/master/list-volume-adjustment.html')

class volumeAdjustmentList(View):
    def post(self, request):
        data = self._datatables(request)
        return JsonResponse(data, safe=False)
    
    def _datatables(self, request):
        datatables = request.POST
        # Ambil draw
        draw = int(datatables.get('draw'))
        # Ambil start
        start = int(datatables.get('start'))
        # Ambil length (limit)
        length = int(datatables.get('length'))
        # Ambil data search
        search = datatables.get('search[value]')
        # Ambil order column
        order_column = int(datatables.get('order[0][column]'))
        # Ambil order direction
        order_dir = datatables.get('order[0][dir]')

        data = mineVolumeAdjustment.objects.all()

        if search:
            data = data.filter(
                Q(type_truck__icontains=search) |
                Q(category__icontains=search) |
                Q(vendors__icontains=search) |
                Q(material__icontains=search) |
                Q(sources_area__icontains=search) |
                Q(loading_point__icontains=search) 
            )
       
        # Filter berdasarkan parameter dari request
        startDate       = request.POST.get('startDate')
        endDate         = request.POST.get('endDate')
        material_filter = request.POST.get('material_filter')
        type_truck      = request.POST.get('type_truck')
        loading_point   = request.POST.get('loading_point')
        source_filter   = request.POST.get('source_filter')

        if startDate and endDate:
            data = data.filter(date_start__range=[startDate, endDate])

        if material_filter:
            data = data.filter(material=material_filter)

        if type_truck:
            data = data.filter(type_truck=type_truck)


        if loading_point:
            data = data.filter(loading_point=loading_point)

        if source_filter:
            data = data.filter(sources_area=source_filter)

        # Atur sorting
        if order_dir == 'desc':
            order_by = f'-{data.model._meta.fields[order_column].name}'
        else:
            order_by = f'{data.model._meta.fields[order_column].name}'

        data = data.order_by(order_by)

        # Menghitung jumlah total sebelum filter
        records_total = data.count()

        # Menerapkan pagination
        paginator = Paginator(data, length)
        total_pages = paginator.num_pages

        # Menghitung jumlah total setelah filter
        total_records_filtered = paginator.count

        # Atur paginator
        try:
            object_list = paginator.page(start // length + 1).object_list
        except PageNotAnInteger:
            object_list = paginator.page(1).object_list
        except EmptyPage:
            object_list = paginator.page(paginator.num_pages).object_list

        data = [
            {
                "id"            : item.id,
                "date_start"    : item.date_start,
                "date_end"      : item.date_end,
                "category"      : item.category,
                "vendors"       : item.vendors,
                "sources_area"  : item.sources_area,
                "loading_point" : item.loading_point,
                "type_truck"    : item.type_truck,
                "material"      : item.material,
                "bcm_original"  : item.bcm_original,
                "ton_original"  : item.ton_original,
                "bcm_updated"   : item.bcm_updated,
                "ton_updated"   : item.ton_updated,
                "status"        : item.status
                
            } for item in object_list
        ]

        return {
            'draw'           : draw,
            'recordsTotal'   : records_total,
            'recordsFiltered': total_records_filtered,
            'data'           : data,
            'start'          : start,
            'length'         : length,
            'totalPages'     : total_pages,
        }
    
@login_required        
@csrf_exempt
def getIdVolumeAdjusment(request):
    if request.method == 'GET':
        id_get  = request.GET.get('id')

        try:
            items = volumeTruckFactorAdjustment.objects.get(id=id_get)

            # Ambil data sumber (sources) jika ada
            sources_area = None
            if items.sources:
                source = SourceMines.objects.filter(id=items.sources).first()
                if source:
                    sources_area = source.sources_area

            # Ambil data loading point jika ada
            loading_point = None
            if items.loading_point:
                loading = SourceMinesLoading.objects.filter(id=items.loading_point).first()
                if loading:
                    loading_point = loading.loading_point

            # Ambil data material jika ada
            material_id = None
            if items.material:
                material = Material.objects.filter(nama_material=items.material).first()
                if material:
                    material_id = material.id

            data = {
                'id'           : items.id,
                'date_start'   : items.date_start, 
                'date_end'     : items.date_end, 
                'category'     : clean_string(items.category),
                'vendors'      : clean_string(items.vendors), 
                'type_truck'   : clean_string(items.type_truck), 
                'material'     : clean_string(items.material), 
                'material_id'  : material_id, 
                'sources_id'   : items.sources,
                'sources'      : clean_string(sources_area),
                'loading_id'   : items.loading_point,
                'loading_point': clean_string(loading_point),
                'bcm_original' : items.bcm_original,
                'ton_original' : items.ton_original,
                'bcm_updated'  : items.bcm_updated,
                'ton_updated'  : items.ton_updated,
                'status'       : clean_string(items.status), 
                'remarks'      : items.remarks
            }
            return JsonResponse(data)
        except volumeTruckFactorAdjustment.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

# Dinamis by filter
def get_category_mine_volume(request):
    tgl_pertama  = request.GET.get('startDate')
    tgl_terakhir = request.GET.get('endDate')

    if request.method == 'GET':
        try:
            sql_query = """
                SELECT 
                    TRIM(category_mine) as category_mine
                FROM 
                    productions_mines as t1
                WHERE 
                    date_production BETWEEN %s AND %s
                GROUP BY 
                    category_mine
                ORDER BY 
                    category_mine ASC;
            """
            params = [tgl_pertama, tgl_terakhir]
             # Eksekusi query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query,params)
                result = cursor.fetchall()
           
            list=[]
            # Ubah hasil query menjadi list of dictionaries
            list = [{'category_mine': row[0]} for row in result]

            # Buat respons JSON dengan list data
            response_data = {
                'list': list,
            }

            return JsonResponse(response_data)
        except mineProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_vendors_mine_volume(request):
    tgl_pertama  = request.GET.get('startDate')
    tgl_terakhir = request.GET.get('endDate')
    category     = request.GET.get('category')

    if request.method == 'GET':
        try:
            sql_query = """
                SELECT 
                    TRIM(vendors) as vendors
                FROM 
                    productions_mines as t1
                WHERE 
                    date_production BETWEEN %s AND %s AND category_mine = %s
                GROUP BY 
                    vendors
                ORDER BY 
                    vendors ASC;
            """
            params = [tgl_pertama, tgl_terakhir,category]
             # Eksekusi query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query,params)
                result = cursor.fetchall()
           
            list=[]
            # Ubah hasil query menjadi list of dictionaries
            list = [{'vendors': row[0]} for row in result]

            # Buat respons JSON dengan list data
            response_data = {
                'list': list,
            }

            return JsonResponse(response_data)
        except mineProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_sources_mine_volume(request):
    tgl_pertama  = request.GET.get('startDate')
    tgl_terakhir = request.GET.get('endDate')
    category     = request.GET.get('category')
    vendors      = request.GET.get('vendors')

    if request.method == 'GET':
        try:
            sql_query = """
                SELECT 
                    t2.id as id_source,TRIM(t2.sources_area) as sources_area
                FROM productions_mines as t1
                LEFT JOIN mine_sources as t2 ON t2.id=t1.sources_area 
                WHERE 
                    t1.date_production BETWEEN %s AND %s
                    AND t1.category_mine=%s AND t1.vendors=%s
                GROUP BY 
                    t2.id,t2.sources_area
                ORDER BY t2.id,t2.sources_area ASC
            """
            params = [tgl_pertama, tgl_terakhir,category,vendors]
             # Eksekusi query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query,params)
                result = cursor.fetchall()
           
            list=[]
            # Ubah hasil query menjadi list of dictionaries
            list = [{'id_source': row[0], 'sources_area': row[1]} for row in result]

            # Buat respons JSON dengan list data
            response_data = {
                'list': list,
            }

            return JsonResponse(response_data)
        except mineProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_loading_mine_volume(request):
    tgl_pertama  = request.GET.get('startDate')
    tgl_terakhir = request.GET.get('endDate')
    category     = request.GET.get('category')
    vendors      = request.GET.get('vendors')
    sources      = request.GET.get('sources')

    if request.method == 'GET':
        try:
            sql_query = """
                SELECT 
                    t3.id as id_loading,
                    TRIM(t3.loading_point) as loading_point
                FROM productions_mines as t1
                LEFT JOIN mine_sources as t2 ON t2.id=t1.sources_area 
                LEFT JOIN mine_sources_point_loading as t3 ON t3.id = t1.loading_point
                WHERE 
                    t1.date_production BETWEEN %s AND %s
                    AND t1.category_mine=%s AND t1.vendors=%s AND t2.id=%s
                GROUP BY 
                   t3.id,t3.loading_point
                ORDER BY
                    t3.id,t3.loading_point ASC
            """
            params = [tgl_pertama, tgl_terakhir,category,vendors,sources]
             # Eksekusi query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query,params)
                result = cursor.fetchall()
           
            list=[]
            # Ubah hasil query menjadi list of dictionaries
            list = [{'id_loading': row[0], 'loading_point': row[1]} for row in result]

            # Buat respons JSON dengan list data
            response_data = {
                'list': list,
            }

            return JsonResponse(response_data)
        except mineProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_hauler_class_volume(request):
    tgl_pertama   = request.GET.get('startDate')
    tgl_terakhir  = request.GET.get('endDate')
    category      = request.GET.get('category')
    vendors       = request.GET.get('vendors')
    sources       = request.GET.get('sources')
    loading_point = request.GET.get('loading_point')

    if request.method == 'GET':
        try:
            sql_query = """
                SELECT 
                   TRIM(hauler_class) as hauler_class
                FROM productions_mines as t1
                LEFT JOIN mine_sources as t2 ON t2.id=t1.sources_area 
                LEFT JOIN mine_sources_point_loading as t3 ON t3.id = t1.loading_point
                WHERE 
                    t1.date_production BETWEEN %s AND %s
                    AND t1.category_mine=%s AND t1.vendors=%s AND t2.id=%s AND t3.id=%s
                GROUP BY 
                  hauler_class
                ORDER BY
                   hauler_class ASC
            """
            params = [tgl_pertama, tgl_terakhir,category,vendors,sources,loading_point]
             # Eksekusi query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query,params)
                result = cursor.fetchall()
           
            list=[]
            # Ubah hasil query menjadi list of dictionaries
            list = [{'hauler_class': row[0]} for row in result]

            # Buat respons JSON dengan list data
            response_data = {
                'list': list,
            }

            return JsonResponse(response_data)
        except mineProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_material_volume(request):
    tgl_pertama  = request.GET.get('startDate')
    tgl_terakhir = request.GET.get('endDate')
    category     = request.GET.get('category')
    vendors      = request.GET.get('vendors')
    sources      = request.GET.get('sources')
    loading_point = request.GET.get('loading_point')
    hauler_class  = request.GET.get('hauler_class')

    if request.method == 'GET':
        try:
            sql_query = """
                SELECT 
                    t4.id as id_material,
                    TRIM(t4.nama_material) as nama_material,
                    bcm,tonnage
                FROM productions_mines as t1
                LEFT JOIN mine_sources as t2 ON t2.id=t1.sources_area 
                LEFT JOIN mine_sources_point_loading as t3 ON t3.id = t1.loading_point
                LEFT JOIN materials as t4 ON t4.id=t1.id_material
                WHERE 
                    t1.date_production BETWEEN %s AND %s
                    AND t1.category_mine=%s AND t1.vendors=%s AND t2.id=%s AND t3.id=%s AND t1.hauler_class=%s
                GROUP BY 
                  t4.id,t4.nama_material,bcm,tonnage
                ORDER BY
                   t4.nama_material ASC
            """
            params = [tgl_pertama, tgl_terakhir,category,vendors,sources,loading_point,hauler_class]
             # Eksekusi query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query,params)
                result = cursor.fetchall()
           
            list=[]
            # Ubah hasil query menjadi list of dictionaries
            list = [{'id_material': row[0],'nama_material': row[1],'bcm': row[2],'tonnage': row[3]} for row in result]

            # Buat respons JSON dengan list data
            response_data = {
                'list': list,
            }

            return JsonResponse(response_data)
        except mineProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_volume_data(request):
    tgl_pertama  = request.GET.get('startDate')
    tgl_terakhir = request.GET.get('endDate')
    category     = request.GET.get('category')
    vendors      = request.GET.get('vendors')
    sources      = request.GET.get('sources')
    loading_point = request.GET.get('loading_point')
    hauler_class  = request.GET.get('hauler_class')
    nama_material = request.GET.getlist('nama_material')  # Tangkap sebagai list

    if request.method == 'GET':
        try:
            sql_query = """
                  SELECT 
                    t4.id as id_material,
                    t4.nama_material,
                    bcm, tonnage
                FROM productions_mines as t1
                LEFT JOIN mine_sources as t2 ON t2.id=t1.sources_area 
                LEFT JOIN mine_sources_point_loading as t3 ON t3.id=t1.loading_point
                LEFT JOIN materials as t4 ON t4.id=t1.id_material
                WHERE 
                    t1.date_production BETWEEN %s AND %s
                    AND t1.category_mine=%s AND t1.vendors=%s 
                    AND t2.id=%s AND t3.id=%s AND t1.hauler_class=%s
                    {material_filter}
                GROUP BY 
                    t4.id, t4.nama_material, bcm, tonnage
                ORDER BY
                    t4.nama_material ASC
            """
 
            params = [tgl_pertama, tgl_terakhir,category,vendors,sources,loading_point,hauler_class]
           
            # Tambahkan filter `IN` untuk `nama_material`
            if nama_material:
                placeholders = ",".join(["%s"] * len(nama_material))
                material_filter = f"AND t4.id IN ({placeholders})"
                params.extend(nama_material)
            else:
                material_filter = ""

            sql_query = sql_query.format(material_filter=material_filter)
             # Eksekusi query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query, params)
                result = cursor.fetchall()

            list_data = [{'id_material': row[0], 'nama_material': row[1], 'bcm': row[2], 'tonnage': row[3]} for row in result]

            # Buat respons JSON dengan list data
            response_data = {
                'list': list_data,
            }

            return JsonResponse(response_data)
        except mineProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def insert_volume_adjustment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Validasi input
            required_fields = ['date_start', 'date_end', 'category', 'vendors', 'sources', 'loading_point', 'hauler_class', 'materials']
            for field in required_fields:
                if field not in data or not data[field]:
                    return JsonResponse({'error': f'{field} is required'}, status=400)

            materials = data.get('materials', [])
            if not materials:
                return JsonResponse({'error': 'Materials data is empty'}, status=400)

            with transaction.atomic():
                reference_tf = f"{data['date_start']}{data['date_end']}{data['category']}{data['vendors']}{data['sources']}{data['loading_point']}{data['hauler_class']}"

                # Cek apakah data sudah ada??
                # if volumeTruckFactorAdjustment.objects.filter(reference_tf=reference_tf).exists():
                if volumeTruckFactorAdjustment.objects.filter(
                    date_start__gte=data['date_start'],
                    date_end__lte=data['date_end'],
                    category=data['category'],
                    vendors=data['vendors'],
                    sources=data['sources'],
                    loading_point=data['loading_point'],
                    type_truck=data['hauler_class']
                    ).exists():
                     return JsonResponse({'error': f'{reference_tf} already exists'}, status=422)

                # Insert atau update data material
                for material in materials:
                    nama_material = material.get('nama_material')
                    bcm_original  = material.get('bcm_original')
                    ton_original  = material.get('ton_original')
                    bcm_updated   = material.get('bcm_updated')
                    ton_updated   = material.get('ton_updated')

                    # Update atau insert volumeTruckFactorAdjustment
                    obj, created = volumeTruckFactorAdjustment.objects.update_or_create(
                        material = nama_material,
                        defaults={
                            'date_start': data['date_start'],
                            'date_end': data['date_end'],
                            'category': data['category'],
                            'vendors': data['vendors'],
                            'sources': int(data['sources']),
                            'loading_point': int(data['loading_point']),
                            'type_truck': data['hauler_class'],
                            'bcm_original': bcm_original,
                            'ton_original': ton_original,
                            'bcm_updated': bcm_updated,
                            'ton_updated': ton_updated,
                            'status': 'adjustment'
                        }
                    )

                # Update tabel produksi jika diperlukan
                bcm_updated = float(materials[0]['bcm_updated'])  # Contoh: gunakan nilai pertama
                ton_updated = float(materials[0]['ton_updated'])

                mineProductions.objects.filter(
                    date_production__gte=data['date_start'],
                    date_production__lte=data['date_end'],
                    category_mine=data['category'],
                    vendors=data['vendors'],
                    hauler_class=data['hauler_class'],
                    sources_area=data['sources'],
                    loading_point=data['loading_point']
                ).update(
                    bcm     = bcm_updated,
                    tonnage = ton_updated,
                    remarks = 'volume adjustment'
                )


            return JsonResponse({'success': True, 'message': 'Data berhasil disimpan.'})

        except Exception as e:
            return JsonResponse({'error': 'Terjadi kesalahan', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Metode HTTP tidak diizinkan'}, status=405)
   
@login_required
def update_volume_adjustment(request, id):
    if request.method == 'POST':
        try:
            # Validasi menggunakan Django Forms atau manual
            required_fields = {
                'date_start'    : 'Date Start is required.',
                'date_end'      : 'Date End is required.',
                'category'      : 'Category End is required.',
                'vendors'       : 'vendors End is required.',
                'sources'       : 'Sources is required.',
                'loading_point' : 'loading_point is required.',
                'material'      : 'Material is required.',
                'type_truck'    : 'Type Truck is required.',
                'bcm_original'  : 'Bcm Original is required.',
                'ton_original'  : 'Tonnage Original is required.',
                # 'bcm_updated'   : 'Bcm Updated is required.',
                # 'ton_updated'   : 'Tonnage Updated is required.',
            }

            # Validasi request
            for field, message in required_fields.items():
                if not request.POST.get(field):
                    return JsonResponse({'error': message}, status=400)

            # Ambil data dari request
            date_start    = request.POST['date_start']
            date_end      = request.POST['date_end']
            category      = request.POST['category']
            vendors       = request.POST['vendors']
            sources       = int(request.POST['sources'])
            loading_point = int(request.POST['loading_point'])
            material      = int(request.POST['material'])
            type_truck    = request.POST['type_truck']
            bcm_original  = float(request.POST['bcm_original'])
            ton_original  = float(request.POST['ton_original'])

            # Dapatkan objek yang akan diupdate
            data = get_object_or_404(volumeTruckFactorAdjustment, id=id)
            # Update data
            data.status = 'restore'
            data.save()

            # Update mineProductions
            mineProductions.objects.filter(
                    date_production__gte=date_start,
                    date_production__lte=date_end,
                    category_mine=category,
                    vendors=vendors,
                    hauler_class=type_truck,
                    sources_area=sources,
                    loading_point=loading_point,
                    id_material=material
            ).update(
                    bcm     = bcm_original,
                    tonnage = ton_original,
                    remarks = 'volume restore'
            )

            return JsonResponse({'success': True, 'message': 'Data berhasil diupdate.'})

        except IntegrityError as e:
            return JsonResponse({'error': 'Terjadi kesalahan integritas database', 'message': str(e)}, status=400)
        except ValidationError as e:
            return JsonResponse({'error': 'Validasi gagal', 'message': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'Terjadi kesalahan', 'message': str(e)}, status=500)

    return JsonResponse({'error': 'Metode tidak diizinkan'}, status=405)

@login_required
def delete_volume_adjustment(request):
    if request.method == 'DELETE':
        job_id = request.GET.get('id')
        if job_id:
            # Lakukan penghapusan berdasarkan ID di sini
            data = volumeTruckFactorAdjustment.objects.get(id=int(job_id))
            data.delete()
            return JsonResponse({'status': 'deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
