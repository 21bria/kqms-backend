# 
from django.http import JsonResponse
from ....models.ore_production_view import batchStatusView
from django.shortcuts import render
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Sum
from datetime import datetime
from django.db import transaction,connections
from django.db.models import Q
from django.utils.timezone import now, timedelta
from django.http import JsonResponse
import json
from django.views import View

def ore_batch_status_page(request):
    # Cek permission
    return render(request, 'admin-mgoqa/production-ore/list-ore-batch.html')

class OrePdsBatch(View):

    def post(self, request):
        # Ambil semua data invoice yang valid
        data_ore = self._datatables(request)
        return JsonResponse(data_ore, safe=False)

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

        # Gunakan fungsi get_joined_data
        data = batchStatusView.objects.all()

        if search:
            data = data.filter(
                Q(shift__icontains=search) |
                Q(prospect_area__icontains=search) |
                Q(mine_block__icontains=search) |
                Q(nama_material__icontains=search) |
                Q(ore_class__icontains=search) |
                Q(unit_truck__icontains=search) |
                Q(stockpile__icontains=search) |
                Q(pile_id__icontains=search) |
                Q(batch_code__icontains=search) |
                Q(batch_status__icontains=search) |
                Q(sample_number__icontains=search) |
                Q(username__icontains=search) 
            )
       

        # Filter berdasarkan parameter dari request
        startDate       = request.POST.get('startDate')
        endDate         = request.POST.get('endDate')
        material_filter = request.POST.get('material_filter')
        area_filter     = request.POST.get('area_filter')
        point_filter    = request.POST.get('point_filter')
        source_filter   = request.POST.get('source_filter')

        if startDate and endDate:
            data = data.filter(tgl_production__range=[startDate, endDate])

        if material_filter:
            data = data.filter(nama_material=material_filter)

        if area_filter:
            data = data.filter(stockpile=area_filter)

        if point_filter:
            data = data.filter(pile_id=point_filter)

        if source_filter:
            data = data.filter(prospect_area=source_filter)

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
                "tgl_production": item.tgl_production,
                "shift"         : item.shift,
                "prospect_area" : item.prospect_area,
                "mine_block"    : item.mine_block,
                "from_rl"       : item.from_rl,
                "to_rl"         : item.to_rl,
                "nama_material" : item.nama_material,
                "ore_class"     : item.ore_class,
                "unit_truck"    : item.unit_truck,
                "stockpile"     : item.stockpile,
                "pile_id"       : item.pile_id,
                "batch_code"    : item.batch_code,
                "increment"     : item.increment,
                "batch_status"  : item.batch_status,
                "ritase"        : item.ritase,
                "tonnage"       : round(item.tonnage, 2),
                "sample_number" : item.sample_number,
                "ni"            : item.ni,
                "limits"        : item.limits
                
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
    
def total_ore_batch(request):
    # queryset = OreProductions.objects.exclude(id_stockpile=66)
    queryset = batchStatusView.objects.all()

    start_date      = request.GET.get('startDate')
    end_date        = request.GET.get('endDate')
    material_filter = request.GET.get('material_filter')
    area_filter     = request.GET.get('area_filter')
    point_filter    = request.GET.get('point_filter')
    source_filter   = request.GET.get('source_filter')

    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date   = datetime.strptime(end_date, '%Y-%m-%d').date()
        queryset   = queryset.filter(tgl_production__range=[start_date, end_date])

    if material_filter:
        queryset = queryset.filter(nama_material=material_filter)

    if area_filter:
        queryset = queryset.filter(stockpile=area_filter)
    if point_filter:
        queryset = queryset.filter(pile_id=point_filter)
    if source_filter:
        queryset = queryset.filter(prospect_area=source_filter)    

    result      = queryset.aggregate(
        qty     = Count('*'),
        tonnage = Sum('tonnage', default=0)
    )

    return JsonResponse({
        'Qty': result['qty'],
        'Tonnage': result['tonnage']
    })

def total_lim_batch(request):
    # queryset = OreProductions.objects.exclude(id_stockpile=66)
    queryset        = batchStatusView.objects.filter(nama_material="LIM")
  
    start_date      = request.GET.get('startDate')
    end_date        = request.GET.get('endDate')
    area_filter     = request.GET.get('area_filter')
    point_filter    = request.GET.get('point_filter')
    source_filter   = request.GET.get('source_filter')
    material_filter = request.GET.get('material_filter')

    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date   = datetime.strptime(end_date, '%Y-%m-%d').date()
        queryset   = queryset.filter(tgl_production__range=[start_date, end_date])

    if material_filter:
        queryset = queryset.filter(nama_material=material_filter)    
    if area_filter:
        queryset = queryset.filter(stockpile=area_filter)
    if point_filter:
        queryset = queryset.filter(pile_id=point_filter)
    if source_filter:
        queryset = queryset.filter(prospect_area=source_filter)    

    result      = queryset.aggregate(
        qty     = Count('*'),
        tonnage = Sum('tonnage', default=0)
    )

    return JsonResponse({
        'Qty'    : result['qty'],
        'Tonnage': result['tonnage']
    })

def total_sap_batch(request):
    # queryset = OreProductions.objects.exclude(id_stockpile=66)
    queryset        = batchStatusView.objects.filter(nama_material="SAP")
  
    start_date      = request.GET.get('startDate')
    end_date        = request.GET.get('endDate')
    area_filter     = request.GET.get('area_filter')
    point_filter    = request.GET.get('point_filter')
    source_filter   = request.GET.get('source_filter')
    material_filter = request.GET.get('material_filter')

    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date   = datetime.strptime(end_date, '%Y-%m-%d').date()
        queryset   = queryset.filter(tgl_production__range=[start_date, end_date])
    if material_filter:
        queryset = queryset.filter(nama_material=material_filter)    

    if area_filter:
        queryset = queryset.filter(stockpile=area_filter)
    if point_filter:
        queryset = queryset.filter(pile_id=point_filter)
    if source_filter:
        queryset = queryset.filter(prospect_area=source_filter)    

    result      = queryset.aggregate(
        qty     = Count('*'),
        tonnage = Sum('tonnage', default=0)
    )

    return JsonResponse({
        'Qty'    : result['qty'],
        'Tonnage': result['tonnage']
    })

# def getIdBatch(request, id):
#     if request.method == 'GET':
#         try:
#             items = batchStatusView.objects.get(id=id)
#             data = {
#                 'id'              : items.id,
#                 'tgl_production'  : items.tgl_production, 
#                 'batch_status'    : items.batch_status,
#                 'ritase'          : items.ritase,
#                 'tonnage'         : items.tonnage,
#                 'pile_status'     : items.pile_status,
#                 'ore_class'       : items.ore_class
#             }
#             return JsonResponse(data)
#         except batchStatusView.DoesNotExist:
#             return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

#     return JsonResponse({'error': 'Invalid request method'}, status=400)

def update_batch_status(request):
    response_data = {'success': False, 'message': ''}
    
    try:
        with transaction.atomic():
            # Mendapatkan tanggal 3 hari yang lalu
            three_days_ago = now() - timedelta(days=3)

            query = """
                UPDATE ore_productions
                SET batch_status = 'Complete'
                WHERE batch_status = 'Incomplete'
                AND tgl_production < %s
                AND EXISTS (
                    SELECT 1 FROM samples_productions
                    WHERE samples_productions.kode_batch = ore_productions.kode_batch
                    AND samples_productions.sample_number IS NOT NULL
                )
            """
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(query, [three_days_ago])

            response_data['success'] = True
            response_data['message'] = 'Data berhasil diupdate.'

    except Exception as e:
        response_data['message'] = f'Terjadi kesalahan: {str(e)}'
    
    return JsonResponse(response_data)

def update_batch_multi(request):
    response_data = {'success': False, 'message': ''}

    if request.method == 'POST':
        try:
            data = json.loads(request.body)  # Ambil data dari request (harus JSON)
            selected_ids = data.get('ids', [])  # Dapatkan daftar ID yang dikirim dari AJAX

            if not selected_ids:
                return JsonResponse({'success': False, 'message': 'No IDs provided'}, status=400)

            with transaction.atomic():
                query = """
                    UPDATE ore_productions
                    SET batch_status = 'Complete'
                    WHERE batch_status = 'Incomplete'
                    AND id IN ({})
                    AND EXISTS (
                        SELECT 1 FROM samples_productions
                        WHERE samples_productions.kode_batch = ore_productions.kode_batch
                        AND samples_productions.sample_number IS NOT NULL
                    )
                """.format(','.join(['%s'] * len(selected_ids)))  # Menyusun query dengan jumlah placeholder yang sesuai

                with connections['kqms_db'].cursor() as cursor:
                    cursor.execute(query, selected_ids)  # Eksekusi query dengan daftar ID

            response_data['success'] = True
            response_data['message'] = 'Data berhasil diupdate.'

        except Exception as e:
            response_data['message'] = f'Terjadi kesalahan: {str(e)}'
            return JsonResponse(response_data, status=500)

    return JsonResponse(response_data)