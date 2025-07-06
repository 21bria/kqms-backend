from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from ....models.waybill_model import Waybills
from ....models.waybill_temp import WaybillsTemporary
from ....models.waybill_view import listTemporary
from ....models.sample_production import SampleProductions
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.http import JsonResponse
from datetime import datetime
from ....utils.utils import generate_waybill_number

@login_required
def waybill_entry_page(request):
    # Cek permission
    today   = datetime.today()
    context = {
        'day_date'   : today.strftime('%Y-%m-%d'),
    }
    return render(request, 'admin-mgoqa/waybills/create-waybills.html',context)

class waybillsListTemporary(View):
    def post(self, request):
        # Ambil semua data invoice yang valid
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

        # Gunakan fungsi get_joined_data
        data = listTemporary.objects.all()

        if search:
            data = data.filter(
                Q(sample_id__icontains=search) |
                Q(type_sample__icontains=search) |
                Q(sample_method__icontains=search) |
                Q(nama_material__icontains=search) |
                Q(status_input__icontains=search) 
            )


        # Atur sorting
        if order_dir == 'desc':
            order_by = f'-{data.model._meta.fields[order_column].name}'
        else:
            order_by = f'{data.model._meta.fields[order_column].name}'

        data = data.order_by(order_by)

        # Menghitung jumlah total sebelum filter
        records_total = data.count()

        # Menerapkan pagination
        paginator   = Paginator(data, length)
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
                "sample_id"     : item.sample_id,
                "type_sample"   : item.type_sample,
                "sample_method" : item.sample_method,
                "nama_material" : item.nama_material,
                "sampling_area" : item.sampling_area,
                "sampling_point": item.sampling_point,
                "batch_code"    : item.batch_code,
                "no_save"       : item.no_save,
                "status_input"  : item.status_input,
                "id_user"       : item.id_user
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

def get_waybill_number(request, team):
    date_delivery   = request.GET.get('date_delivery', None)
    new_number      = generate_waybill_number(team, date_delivery)
    return JsonResponse({'new_number': new_number})

@login_required
def addItem(request):
    if request.method == 'POST':
        sample_id = request.POST.get('sample_id')
        
        # Ambil satu data dari model SampleProductions berdasarkan sample_id
        data = SampleProductions.objects.filter(sample_number=sample_id).first()
        
        if not data:
            return JsonResponse({'status': False, 'message': 'Data Not Found'})

        # Periksa duplikat di Waybills
        if Waybills.objects.filter(sample_id =data.sample_number).exists():
            return JsonResponse({'status': False, 'message': 'Data Already Exists in Waybiils'})

        # Memeriksa apakah data sudah ada di WaybillsTemporary sebelum insert
        if not WaybillsTemporary.objects.filter(sample_id=data.sample_number).exists():
            insert_obj = WaybillsTemporary(
                sample_id       = data.sample_number,
                id_type_sample  = data.id_type_sample,
                id_method       = data.id_method,
                id_material     = data.id_material,
                sampling_area   = data.sampling_area,
                sampling_point  = data.sampling_point,
                batch_code      = data.batch_code,
                status_input    = '',
                no_save         = '',
                id_user         = request.user.id  # Pastikan user sudah login sebelumnya
            )
            insert_obj.save()
            
            response = {
                'status': True,
                'message': 'Data Inserted Successfully',
            }
        else:
            response = {
                'status': False,
                'message': 'Data Already Exists in WaybillsTemporary',
            }

        return JsonResponse(response)

    else:
        return JsonResponse({'status': False, 'message': 'Metode HTTP tidak diizinkan'})
    
@login_required   
def add_multi(request):
    if request.method == 'POST':
        sample_from = request.POST.get('sampleFrom')
        sample_to   = request.POST.get('sampleTo')

        # Misalnya, pengambilan data dari model SampleProductions
        get_data = SampleProductions.get_samples(sample_from, sample_to)

        insert_data    = []
        duplicate_data = []

        # Memproses data
        for data in get_data:
            if Waybills.is_duplicate_data(data.sample_number):
                duplicate_data.append(data)
            else:
                insert_data.append(data)

        # Memeriksa duplikat lagi sebelum memasukkan ke dalam database
        bulk_insert_data = []
        for data in insert_data:
            # Memeriksa apakah data sudah ada di tabel temporary sebelum insert
            if not WaybillsTemporary.objects.filter(sample_id=data.sample_number).exists():
                insert_array = WaybillsTemporary(
                    sample_id       = data.sample_number,
                    id_type_sample  = data.id_type_sample,
                    id_method       = data.id_method,
                    id_material     = data.id_material,
                    sampling_area   = data.sampling_area,
                    sampling_point  = data.sampling_point,
                    batch_code      = data.batch_code,
                    status_input    ='',
                    no_save         ='',
                    id_user         = request.user.id  # Pastikan user sudah login sebelumnya
                )
                bulk_insert_data.append(insert_array)

        # Memasukkan data menggunakan bulk_create
        if bulk_insert_data:
            WaybillsTemporary.objects.bulk_create(bulk_insert_data)

        # Menyiapkan respons JSON
        if insert_data:
            response = {
                'status'        : True,
                'message'       : 'Insert',
                'duplicate'     : len(duplicate_data),
                'insert_count'  : len(insert_data),
                'insert_data'   : [data.sample_number for data in insert_data]
            }
        else:
            response = {
                'status'     : False,
                'message'    : 'Data Not Found',
                'insert_data': len(insert_data)
            }

        return JsonResponse(response)

    else:
        return JsonResponse({'status': False, 'message': 'Metode HTTP tidak diizinkan'})
    
@login_required
@csrf_exempt
def insert_waybill(request):
    # id_user = request.user.id  # Mengambil id user dari session login
    if request.method == 'POST':
        # Ambil data dari request
        tgl_deliver     = request.POST.get('tgl_deliver')
        delivery_time   = request.POST.get('delivery_time')
        waybill_number  = request.POST.get('waybill_number')
        numb_sample     = request.POST.get('numb_sample')
        mral_order      = request.POST.get('mral_order').strip()
        roa_order       = request.POST.get('roa_order').strip()
        remarks         = request.POST.get('remarks')

        # Cek apakah waybill number sudah ada
        existing_data = Waybills.objects.filter(waybill_number=waybill_number).exists()

        if existing_data:
            response = {
                'success': False,
                'message': 'Duplicate Waybill Number'
            }
        else:
            # Ubah format waktu
            try:
                delivery = datetime.strptime(tgl_deliver + ' ' + delivery_time, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                delivery = datetime.strptime(tgl_deliver + ' ' + delivery_time, '%Y-%m-%d %H:%M')
                
            left_date  = delivery.day  # Ambil hari dari tanggal pengiriman

            # Ambil data dari waybill temp dengan filter dan exclude
            waybill_temp = WaybillsTemporary.objects.filter(id_user=request.user.id).exclude(status_input='Batal')

            # Persiapkan data untuk dimasukkan ke dalam database
            insert_data = []
            for data in waybill_temp:
                insert_data.append(Waybills(
                    tgl_deliver    = tgl_deliver,
                    delivery_time  = delivery_time,
                    waybill_number = waybill_number,
                    numb_sample    = numb_sample,
                    sample_id      = data.sample_id,
                    mral_order     = mral_order,
                    roa_order      = roa_order,
                    remarks        = remarks,
                    delivery       = delivery,
                    left_date      = left_date,
                    id_user       = request.user.id
                ))

            # Masukkan data ke dalam database menggunakan bulk_create
            Waybills.objects.bulk_create(insert_data)

            # Catat aktivitas pengguna

            response = {
                'success': True,
                'message': 'Waybill data inserted successfully'
            }

        return JsonResponse(response)

    return JsonResponse({'success': False, 'message': 'Invalid Request'})

@login_required
def update_waybill_status(request):
    if request.method == 'POST':
        try:
            sample_id   = request.POST.get('sample_id')

            data = WaybillsTemporary.objects.get(sample_id=sample_id)

            data.status_input = 'Batal'
            data.save()

            return JsonResponse({
                'status_input'   : data.status_input
            })
        
        except WaybillsTemporary.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Metode tidak diizinkan'}, status=405)
    
@login_required    
def deleteTmpWaybill(request):
    user_id = request.user.id  # Mengambil ID pengguna yang sedang login
    if request.method == 'DELETE':
        try:
            data = WaybillsTemporary.objects.filter(id_user=user_id)
            
            if data.exists():  # Memeriksa apakah ada objek yang cocok dengan filter
                data.delete()  # Menghapus semua objek yang cocok dengan filter
                return JsonResponse({'status': 'deleted'})
            else:
                return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    else:
        return JsonResponse({'error': 'Metode tidak diizinkan'}, status=405)
    
