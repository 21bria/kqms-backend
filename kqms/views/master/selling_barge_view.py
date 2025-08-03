from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ...models.master_barge import BargeUnits
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.shortcuts import render
from django.views.generic import View
from django.db.models import Q
from ...utils.utils import clean_string


@login_required
def barge_page(request):
    return render(request, 'master/list-selling-barge.html') 

class SaleBargeList(View):

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

        # Set record total
        records_total = BargeUnits.objects.all().count()
        # Set records filtered
        records_filtered = records_total
        # Ambil semua yang valid
        code = BargeUnits.objects.all()

        if search:
            code = BargeUnits.objects.filter(
                Q(barge_code__icontains=search) |
                Q(barge_name__icontains=search)
            )
            records_total = code.count()
            records_filtered = records_total

        # Atur sorting
        if order_dir == 'desc':
            order_by = f'-{code.model._meta.fields[order_column].name}'
        else:
            order_by = f'{code.model._meta.fields[order_column].name}'

        code = code.order_by(order_by)

        # Atur paginator
        paginator = Paginator(code, length)

        try:
            object_list = paginator.page(start // length + 1).object_list
        except PageNotAnInteger:
            object_list = paginator.page(1).object_list
        except EmptyPage:
            object_list = paginator.page(paginator.num_pages).object_list

        data = [
            {
                "id"          : item.id,
                "barge_code"  : item.barge_code,
                "barge_name"  : item.barge_name,
                "capacity"    : item.capacity,
                "description" : item.description,
                "active"      : item.active,
            } for item in object_list
        ]

        return {
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        }

@login_required
@csrf_exempt 
def get_barge(request, id):
    allowed_groups = ['superadmin','admin-mgoqa','data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )
    if request.method == 'GET':
        try:
            job = BargeUnits.objects.get(id=id)
            data = {
                'id': job.id,
                'barge_code'  : clean_string(job.barge_code), 
                'barge_name'  : clean_string(job.barge_name), 
                'capacity'    : clean_string(job.capacity), 
                'description' : clean_string(job.description),
                'active'      : clean_string(job.active), 
                'created_at'  : job.created_at
            }
            return JsonResponse(data)
        except BargeUnits.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def insert_barge(request):
    allowed_groups = ['superadmin', 'admin-mgoqa', 'data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'},
            status=403
        )

    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Metode tidak diizinkan'}, status=405)

    # Aturan dan pesan validasi
    rules = {
        'barge_code': ['required'],
        'barge_name'      : ['required'],
    }

    custom_messages = {
        'barge_code.required': 'Code is required.',
        'barge_name.required': 'Name is required.',
    }

    # Validasi input
    cleaned_data = {}
    for field, field_rules in rules.items():
        value = request.POST.get(field, '').strip()
        if 'required' in field_rules and not value:
            return JsonResponse({'error': custom_messages[f'{field}.required']}, status=400)
        cleaned_data[field] = value

    barge_code  = cleaned_data['barge_code']
    barge_name  = cleaned_data['barge_name']
    capacity    = request.POST.get('capacity')
    description = request.POST.get('description', '').strip()
    active = 1

    # Cek duplikat manual sebelum simpan
    if BargeUnits.objects.filter(barge_code=barge_code).exists():
        return JsonResponse({'status': 'error', 'message': 'Barge already exists.'}, status=400)

    # Simpan ke database
    try:
        new_data = BargeUnits.objects.create(
            barge_code=barge_code,
            barge_name=barge_name,
            description=description,
            capacity=capacity,
            active=active
        )
        return JsonResponse({
            'status': 'success',
            'message': 'Data berhasil disimpan.',
            'data': {
                'id': new_data.id,
                'barge_code' : new_data.barge_code,
                'barge_name' : new_data.barge_name,
                'description': new_data.description,
                'active'     : new_data.active,
                'created_at' : new_data.created_at
            }
        })
    except IntegrityError:
        # Fallback jika validasi manual gagal mendeteksi duplikat
        return JsonResponse({'status': 'error', 'message': 'Barge already exists (DB constraint).'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
@login_required
def update_barge(request, id):
    allowed_groups = ['superadmin', 'admin-mgoqa', 'data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'},
            status=403
        )

    if request.method != 'POST':
        return JsonResponse({'error': 'Metode tidak diizinkan'}, status=405)

    try:
        rules = {
            'barge_code' : ['required'],
            'barge_name' : ['required'],
        }

        custom_messages = {
            'barge_code.required': 'Code is required.',
            'barge_name.required': 'Name is required.',
        }

        cleaned_data = {}
        for field, field_rules in rules.items():
            value = request.POST.get(field, '').strip()
            if 'required' in field_rules and not value:
                return JsonResponse({'error': custom_messages[f'{field}.required']}, status=400)
            cleaned_data[field] = value

        # Ambil data yang akan diupdate
        job = BargeUnits.objects.get(id=int(id))

        # Cek duplikat barge_code untuk record lain
        if BargeUnits.objects.filter(barge_code=cleaned_data['barge_code']).exclude(id=job.id).exists():
            return JsonResponse({'error': 'Barge already exists.'}, status=400)

        # Update field
        job.barge_code  = cleaned_data['barge_code']
        job.barge_name  = cleaned_data['barge_name']
        job.capacity    = request.POST.get('capacity')
        job.description = request.POST.get('description', '').strip()
        active_value    = request.POST.get('active')
        job.active      = int(active_value) if active_value is not None else 1
        job.save()

        return JsonResponse({
            'id'          : job.id,
            'barge_code'  : job.barge_code,
            'barge_name'  : job.barge_name,
            'capacity'    : job.capacity,
            'description' : job.description,
            'active'      : job.active,
            'created_at'  : job.created_at
        })

    except BargeUnits.DoesNotExist:
        return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
    except IntegrityError:
        return JsonResponse({'error': 'Barge already exists (DB constraint)'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def delete_barge(request):
    allowed_groups = ['superadmin', 'data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )
    if request.method == 'DELETE':
        job_id = request.GET.get('id')
        if job_id:
            # Lakukan penghapusan berdasarkan ID di sini
            data = BargeUnits.objects.get(id=int(job_id))
            data.delete()
            return JsonResponse({'status': 'deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

