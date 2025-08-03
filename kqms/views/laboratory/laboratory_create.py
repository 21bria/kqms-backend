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
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from datetime import datetime
from ...utils.utils import generate_lab_number
from ...utils.utils import clean_string

@login_required
def laboratory_entry_page(request):
    # Cek permission
    today   = datetime.today()
    context = {
        'day_date'   : today.strftime('%Y-%m-%d'),
    }
    return render(request, 'admin-lab/preparations/create-jobs.html',context)


def get_lab_number(request):
    date_received   = request.GET.get('date_received', None)
    new_number      = generate_lab_number(date_received)
    return JsonResponse({'new_number': new_number})

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
                Q(sections__icontains=search) 
            )

        
        # Filter berdasarkan parameter dari request
        job_number   = request.POST.get('job_number')

        data = data.filter(job_number=job_number)

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
                "id"             : item.id,
                "date_received"  : item.date_received,
                "shift"          : item.shift,
                "priority"       : item.priority,
                "waybill_number" : item.waybill_number,
                "sections"       : item.sections,
                "sample_id"      : item.sample_id,
                "mral_order"     : item.mral_order,
                "roa_order"      : item.roa_order,
                "job_number"     : item.job_number,
                "sample_wet"     : item.sample_wet,
                "status"         : item.status,
                "remarks"        : item.remarks
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
def insert_lab_prep(request):

    if request.method == 'POST':

        try:
            # Aturan validasi
            rules = {
                'date_received' : ['required'],
                'shift'         : ['required'],
                'time_received' : ['required'],
                'priority'      : ['required'],
                'sections'      : ['required'],
                'mral_order'    : ['required'],
                'roa_order'     : ['required'],
                'sample_id'     : ['required'],
                'sample_wet'    : ['required'],
            }

            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'date_received.required'  : 'Date is required.',
                'shift.required'          : 'Shift is required.',
                'time_received.required'  : 'Time is required.',
                'priority.required'       : 'Priority is required.',
                'sections.required'       : 'Sections is required.',
                'mral_order.required'     : 'Order mral is required.',
                'roa_order.required'      : 'Order roa is required.',
                'sample_id.required'      : 'Sample Id is required.',
                'sample_wet.required'     : 'Sample Wet is required.',
            }

            # Validasi request
            for field, field_rules in rules.items():
                for rule in field_rules:
                    if rule == 'required':
                        if not request.POST.get(field):
                            return JsonResponse({'error': custom_messages[f'{field}.required']}, status=400)
                    elif rule.startswith('min_length'):
                        min_length = int(rule.split(':')[1])
                        if len(request.POST.get(field, '')) < min_length:
                            return JsonResponse({'error': custom_messages[f'{field}.min_length']}, status=400)
                    elif rule.startswith('max_length'):
                        max_length = int(rule.split(':')[1])
                        if len(request.POST.get(field, '')) > max_length:
                            return JsonResponse({'error': custom_messages[f'{field}.max_length']}, status=400)
                    elif rule == 'regex':
                        import re
                        pattern = re.compile(r'^[a-zA-Z0-9]*$')
                        if not pattern.match(request.POST.get(field, '')):
                            return JsonResponse({'error': custom_messages[f'{field}.regex']}, status=400)

                
            # Gunakan transaksi database untuk memastikan integritas data
            with transaction.atomic():
                job_number   = request.POST.get('job_number')
                date_received   = request.POST.get('date_received')
                time_received   = request.POST.get('time_received')
                shift           = request.POST.get('shift')
                priority        = request.POST.get('priority')
                waybill_number  = request.POST.get('waybill_number')
                sections        = request.POST.get('sections')
                mral_order      = request.POST.get('mral_order').strip()
                roa_order       = request.POST.get('roa_order').strip()
                sample_id       = request.POST.get('sample_id')
                sample_wet      = request.POST.get('sample_wet')
                remarks         = request.POST.get('remarks')


                if LaboratorySamples.objects.filter(sample_id=sample_id).exists():
                        return JsonResponse({'message': f'{sample_id} : already exists.'}, status=422)
    
                # Create new data
                LaboratorySamples.objects.create(
                    date_received=date_received,
                    time_received=time_received,
                    shift=shift,
                    priority=priority,
                    job_number=job_number,
                    waybill_number=waybill_number,
                    sections=sections,
                    mral_order=mral_order,
                    roa_order=roa_order,
                    sample_id=sample_id,
                    sample_wet=sample_wet,
                    remarks=remarks,
                    status='Waiting Final',
                    id_user=request.user.id
                )

            # Kembalikan respons JSON sukses
            return JsonResponse({'success': True, 'message': 'Data saved successfully.'})

        except IntegrityError as e:
            return JsonResponse({'error': 'A database integrity error occurred', 'message': str(e)}, status=400)

        except ValidationError as e:
            return JsonResponse({'error': 'Validation failed', 'message': str(e)}, status=400)

        except Exception as e:
            return JsonResponse({'error': 'There is an error', 'message': str(e)}, status=500)

    else:
        return JsonResponse({'error': 'HTTP method not allowed'}, status=405)

@login_required
def get_lab_prep(request, id):
    allowed_groups = ['superadmin','data-control','admin-mgoqa','admin-lab']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )
    if request.method == 'GET':
        try:
            items = LaboratorySamples.objects.get(id=id)
            data = {
                'id'            : items.id,
                'date_received' : items.date_received, 
                'shift'         : items.shift, 
                'time_received' : items.time_received,
                'priority'      : items.priority,
                'waybill_number': clean_string(items.waybill_number),
                'sections'      : items.sections,
                'sample_wet'    : clean_string(items.sample_wet),
                'sample_final'  : clean_string(items.sample_final),
                'sample_press'  : clean_string(items.sample_press),
                'sample_analysis'  : clean_string(items.sample_analysis),
                'sample_id'     : clean_string(items.sample_id),
                'mral_order'    : clean_string(items.mral_order),
                'roa_order'     : clean_string(items.roa_order),
                'remarks'       : clean_string(items.remarks)
            }
            return JsonResponse(data)
        except LaboratorySamples.DoesNotExist:
            return JsonResponse({'error': 'Data not found'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def update_lab_prep(request, id):
    allowed_groups = ['superadmin', 'data-control', 'admin-mgoqa','admin-lab']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
        )
    if request.method == 'POST':
        try:
            job = LaboratorySamples.objects.get(id=id)

              # Aturan validasi
            rules = {
                'date_received' : ['required'],
                'shift'         : ['required'],
                'time_received' : ['required'],
                'priority'      : ['required'],
                'sections'      : ['required'],
                'mral_order'    : ['required'],
                'roa_order'     : ['required'],
                'sample_id'     : ['required'],
                'sample_wet'    : ['required'],
            }

            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'date_received.required'  : 'Date is required.',
                'shift.required'          : 'Shift is required.',
                'time_received.required'  : 'Time is required.',
                'priority.required'       : 'Priority is required.',
                'sections.required'       : 'Sections is required.',
                'mral_order.required'     : 'Order mral is required.',
                'roa_order.required'      : 'Order roa is required.',
                'sample_id.required'      : 'Sample Id is required.',
                'sample_wet.required'     : 'Sample Wet is required.',
            }

            # Validasi request
            for field, field_rules in rules.items():
                for rule in field_rules:
                    if rule == 'required':
                        if not request.POST.get(field):
                            return JsonResponse({'error': custom_messages[f'{field}.required']}, status=400)
                    elif rule.startswith('min_length'):
                        min_length = int(rule.split(':')[1])
                        if len(request.POST.get(field, '')) < min_length:
                            return JsonResponse({'error': custom_messages[f'{field}.min_length']}, status=400)
                    elif rule.startswith('max_length'):
                        max_length = int(rule.split(':')[1])
                        if len(request.POST.get(field, '')) > max_length:
                            return JsonResponse({'error': custom_messages[f'{field}.max_length']}, status=400)
                    elif rule == 'regex':
                        import re
                        pattern = re.compile(r'^[a-zA-Z0-9]*$')
                        if not pattern.match(request.POST.get(field, '')):
                            return JsonResponse({'error': custom_messages[f'{field}.regex']}, status=400)


            # Cek Duplikat Data
            sample_id = request.POST.get('sample_id')

            if LaboratorySamples.objects.filter(sample_id=sample_id).exclude(id=job.id).exists():
                return JsonResponse({'message': f'{sample_id} : already exists.'}, status=422)



            # Menyimpan data ke dalam database
            job.date_received   = request.POST.get('date_received')
            job.time_received   = request.POST.get('time_received')
            job.shift           = request.POST.get('shift')
            job.priority        = request.POST.get('priority')
            job.waybill_number  = request.POST.get('waybill_number')
            job.sample_wet      = request.POST.get('sample_wet')
            job.sample_id       = sample_id
            job.sections        = request.POST.get('sections')
            job.mral_order      = request.POST.get('mral_order')
            job.roa_order       = request.POST.get('roa_order')
            job.remarks         = request.POST.get('remarks')
            
            job.save()

            return JsonResponse({
                'id': job.id,
                'date_received' : job.date_received,
                'time_received' : job.time_received,
                'shift'         : job.shift,
                'waybill_number': job.waybill_number,
                'sections'      : job.sections,
                'sample_wet'    : job.sample_wet,
                'sample_id'     : job.sample_id,
                'mral_order'    : job.mral_order,
                'roa_order'     : job.roa_order,
                'remarks'       : job.remarks
                
            })

        except LaboratorySamples.DoesNotExist:
            return JsonResponse({'error': 'Data not found'}, status=404)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required    
def delete_lab_prep(request):
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
    
