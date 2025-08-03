from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ...models.master_barge import BargePort
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.shortcuts import render
from django.views.generic import View
from django.db.models import Q
from ...utils.utils import clean_string


@login_required
def port_page(request):
    return render(request, 'master/list-selling-port.html') 

class SalePortList(View):

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
        records_total = BargePort.objects.all().count()
        # Set records filtered
        records_filtered = records_total
        # Ambil semua yang valid
        code = BargePort.objects.all()

        if search:
            code = BargePort.objects.filter(
                Q(port_name__icontains=search) |
                Q(port_type__icontains=search)
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
                "id"         :item.id,
                "port_name"  : item.port_name,
                "port_type"  : item.port_type,
                "description": item.description,
                "active"     : item.active,
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
def get_port(request, id):
    allowed_groups = ['superadmin','admin-mgoqa','data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )
    if request.method == 'GET':
        try:
            job = BargePort.objects.get(id=id)
            data = {
                'id': job.id,
                'port_name'   : clean_string(job.port_name), 
                'port_type'   : clean_string(job.port_type), 
                'description' : clean_string(job.description),
                'active'      : clean_string(job.active), 
                'created_at'  : job.created_at
            }
            return JsonResponse(data)
        except BargePort.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def insert_port(request):
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
        'port_name' : ['required'],
        'port_type' : ['required'],
    }

    custom_messages = {
        'port_name.required': 'Name is required.',
        'port_type.required': 'Type is required.',
    }

    # Validasi input
    cleaned_data = {}
    for field, field_rules in rules.items():
        value = request.POST.get(field, '').strip()
        if 'required' in field_rules and not value:
            return JsonResponse({'error': custom_messages[f'{field}.required']}, status=400)
        cleaned_data[field] = value

    port_name   = cleaned_data['port_name']
    port_type   = cleaned_data['port_type']
    description = request.POST.get('description', '').strip()
    active = 1

    # Cek duplikat manual sebelum simpan
    if BargePort.objects.filter(port_name=port_name).exists():
        return JsonResponse({'status': 'error', 'message': 'Name already exists.'}, status=400)

    # Simpan ke database
    try:
        new_data = BargePort.objects.create(
            port_name=port_name,
            port_type=port_type,
            description=description,
            active=active
        )
        return JsonResponse({
            'status': 'success',
            'message': 'Data berhasil disimpan.',
            'data': {
                'id': new_data.id,
                'port_name'  : new_data.port_name,
                'description': new_data.description,
                'active'     : new_data.active,
                'created_at' : new_data.created_at
            }
        })
    except IntegrityError:
        # Fallback jika validasi manual gagal mendeteksi duplikat
        return JsonResponse({'status': 'error', 'message': 'Name already exists (DB constraint).'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
@login_required
def update_port(request, id):
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
            'port_name' : ['required'],
            'port_type' : ['required'],
        }

        custom_messages = {
            'port_name.required': 'Name is required.',
            'port_type.required': 'Type is required.',
        }

        cleaned_data = {}
        for field, field_rules in rules.items():
            value = request.POST.get(field, '').strip()
            if 'required' in field_rules and not value:
                return JsonResponse({'error': custom_messages[f'{field}.required']}, status=400)
            cleaned_data[field] = value

        # Ambil data yang akan diupdate
        job = BargePort.objects.get(id=int(id))

        # Cek duplikat port_name untuk record lain
        if BargePort.objects.filter(port_name=cleaned_data['port_name']).exclude(id=job.id).exists():
            return JsonResponse({'error': 'Name already exists.'}, status=400)

        # Update field
        job.port_name  = cleaned_data['port_name']
        job.port_type  = cleaned_data['port_type']
        job.description = request.POST.get('description', '').strip()
        active_value    = request.POST.get('active')
        job.active      = int(active_value) if active_value is not None else 1
        job.save()

        return JsonResponse({
            'id'          : job.id,
            'port_name'  : job.port_name,
            'port_type'  : job.port_type,
            'description' : job.description,
            'active'      : job.active,
            'created_at'  : job.created_at
        })

    except BargePort.DoesNotExist:
        return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
    except IntegrityError:
        return JsonResponse({'error': 'Name already exists (DB constraint)'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def delete_port(request):
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
            data = BargePort.objects.get(id=int(job_id))
            data.delete()
            return JsonResponse({'status': 'deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

