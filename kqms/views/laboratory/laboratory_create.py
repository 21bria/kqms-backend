from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from ...models.laboratory import LaboratorySamples
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.http import JsonResponse
from datetime import datetime
from ...utils.utils import generate_lab_number

@login_required
def laboratory_entry_page(request):
    # Cek permission
    today   = datetime.today()
    context = {
        'day_date'   : today.strftime('%Y-%m-%d'),
    }
    return render(request, 'admin-lab/preparations/create-jobs.html',context)

class laboratoryListTemporary(View):
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
        data = LaboratorySamples.objects.all()

        if search:
            data = data.filter(
                Q(sample_id__icontains=search) |
                Q(waybill_number__icontains=search) |
                Q(status__icontains=search) 
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

def get_lab_number(request):
    date_received   = request.GET.get('date_received', None)
    new_number      = generate_lab_number(date_received)
    return JsonResponse({'new_number': new_number})

    
@login_required
@csrf_exempt
def insert_lab_prep(request):
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
        existing_data = LaboratorySamples.objects.filter(waybill_number=waybill_number).exists()

        if existing_data:
            response = {
                'success': False,
                'message': 'Duplicate Waybill Numbers'
            }
        else:


            # Persiapkan data untuk dimasukkan ke dalam database
          

            # Masukkan data ke dalam database 
            

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

            data = LaboratorySamples.objects.get(sample_id=sample_id)

            data.status_input = 'Batal'
            data.save()

            return JsonResponse({
                'status_input'   : data.status_input
            })
        
        except LaboratorySamples.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Metode tidak diizinkan'}, status=405)
    
@login_required    
def deleteLabsPrep(request):
    user_id = request.user.id  # Mengambil ID pengguna yang sedang login
    if request.method == 'DELETE':
        try:
            data = LaboratorySamples.objects.filter(id_user=user_id)
            
            if data.exists():  # Memeriksa apakah ada objek yang cocok dengan filter
                data.delete()  # Menghapus semua objek yang cocok dengan filter
                return JsonResponse({'status': 'deleted'})
            else:
                return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    else:
        return JsonResponse({'error': 'Metode tidak diizinkan'}, status=405)
    
