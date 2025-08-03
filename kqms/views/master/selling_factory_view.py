from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ...models.stock_factories import StockFactories
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.shortcuts import render
from django.views.generic import View
from django.db.models import Q
from ...utils.utils import clean_string


@login_required
def factory_page(request):
    return render(request, 'master/list-selling-factory.html') 

class SaleFactoryList(View):

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
        records_total = StockFactories.objects.all().count()
        # Set records filtered
        records_filtered = records_total
        # Ambil semua yang valid
        code = StockFactories.objects.all()

        if search:
            code = StockFactories.objects.filter(
                Q(factory_stock__icontains=search) 
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
                "id"            : item.id,
                "factory_stock" : item.factory_stock,
                "capacity"      : item.capacity,
                "description"   : item.description,
                "status"        : item.status,
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
def get_factory(request, id):
    allowed_groups = ['superadmin','admin-mgoqa','data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )
    if request.method == 'GET':
        try:
            job = StockFactories.objects.get(id=id)
            data = {
                'id': job.id,
                'factory_stock' : clean_string(job.factory_stock), 
                'capacity'      : clean_string(job.capacity), 
                'description'   : clean_string(job.description),
                'status'        : clean_string(job.status), 
                'created_at'    : job.created_at
            }
            return JsonResponse(data)
        except StockFactories.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def insert_factory(request):
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
        'factory_stock': ['required']
    }

    custom_messages = {
        'factory_stock.required': 'Factory is required.',
    }

    # Validasi input
    cleaned_data = {}
    for field, field_rules in rules.items():
        value = request.POST.get(field, '').strip()
        if 'required' in field_rules and not value:
            return JsonResponse({'error': custom_messages[f'{field}.required']}, status=400)
        cleaned_data[field] = value

    factory_stock   = cleaned_data['factory_stock']
    capacity        = request.POST.get('capacity')
    description     = request.POST.get('description', '').strip()
    status = 1

    # Cek duplikat manual sebelum simpan
    if StockFactories.objects.filter(factory_stock=factory_stock).exists():
        return JsonResponse({'status': 'error', 'message': 'Factory already exists.'}, status=400)

    # Simpan ke database
    try:
        new_data = StockFactories.objects.create(
            factory_stock=factory_stock,
            description=description,
            capacity=capacity,
            status=status
        )
        return JsonResponse({
            'status': 'success',
            'message': 'Data berhasil disimpan.',
            'data': {
                'id': new_data.id,
                'factory_stock' : new_data.factory_stock,
                'description'   : new_data.description,
                'status'        : new_data.status,
                'created_at'    : new_data.created_at
            }
        })
    except IntegrityError:
        # Fallback jika validasi manual gagal mendeteksi duplikat
        return JsonResponse({'status': 'error', 'message': 'Factory already exists (DB constraint).'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
@login_required
def update_factory(request, id):
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
            'factory_stock' : ['required']
        }

        custom_messages = {
            'factory_stock.required': 'Code is required.'
        }

        cleaned_data = {}
        for field, field_rules in rules.items():
            value = request.POST.get(field, '').strip()
            if 'required' in field_rules and not value:
                return JsonResponse({'error': custom_messages[f'{field}.required']}, status=400)
            cleaned_data[field] = value

        # Ambil data yang akan diupdate
        job = StockFactories.objects.get(id=int(id))

        # Cek duplikat factory_stock untuk record lain
        if StockFactories.objects.filter(factory_stock=cleaned_data['factory_stock']).exclude(id=job.id).exists():
            return JsonResponse({'error': 'Factory already exists.'}, status=400)

        # Update field
        job.factory_stock   = cleaned_data['factory_stock']
        job.capacity        = request.POST.get('capacity')
        job.description     = request.POST.get('description', '').strip()
        status_value        = request.POST.get('status')
        job.status          = int(status_value) if status_value is not None else 1
        job.save()

        return JsonResponse({
            'id'            : job.id,
            'factory_stock' : job.factory_stock,
            'capacity'      : job.capacity,
            'description'   : job.description,
            'status'        : job.status,
            'created_at'    : job.created_at
        })

    except StockFactories.DoesNotExist:
        return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
    except IntegrityError:
        return JsonResponse({'error': 'Factory already exists (DB constraint)'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def delete_factory(request):
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
            data = StockFactories.objects.get(id=int(job_id))
            data.delete()
            return JsonResponse({'status': 'deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

