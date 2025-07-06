from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ...models.selling_code import SellingCode
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.shortcuts import render
from django.views.generic import View
from django.db.models import Q
from ...utils.utils import clean_string


@login_required
def code_page(request):

    return render(request, 'master/list-selling-code.html') 

class SaleCodeList(View):

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
        records_total = SellingCode.objects.all().count()
        # Set records filtered
        records_filtered = records_total
        # Ambil semua yang valid
        code = SellingCode.objects.all()

        if search:
            code = SellingCode.objects.filter(
                Q(product_code__icontains=search) |
                Q(type__icontains=search)
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
                "id": item.id,
                "product_code": item.product_code,
                "description" : item.description,
                "active,"     : item.active,
                "type"        : item.type
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
def get_code(request, id):
    allowed_groups = ['superadmin','admin-mgoqa','data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )
    if request.method == 'GET':
        try:
            job = SellingCode.objects.get(id=id)
            data = {
                'id': job.id,
                'product_code': clean_string(job.product_code), 
                'description' : clean_string(job.description),
                'active'      : clean_string(job.active), 
                'type'        : clean_string(job.type), 
                'created_at'  : job.created_at
            }
            return JsonResponse(data)
        except SellingCode.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)
 
@login_required
def insert_code(request):
    allowed_groups = ['superadmin','admin-mgoqa','data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )
    if request.method == 'POST':
        product_code = request.POST.get('product_code')
        description  = request.POST.get('description')
        active       = request.POST.get('active')
        type         = request.POST.get('type')

        try:
            new_job = SellingCode.objects.create(
                                    product_code=product_code, 
                                    description=description, 
                                    active=active,
                                    type=type
                                    )
            return JsonResponse({
                'status' : 'success',
                'message': 'Data berhasil disimpan.',
                'data': {
                    'id'          : new_job.id,
                    'product_code': new_job.product_code,
                    'description' : new_job.description,
                    'active'      : new_job.active,
                    'type'        : new_job.type,
                    'created_at'  : new_job.created_at
                }
            })
        except IntegrityError as e:
            # Check if the error is a duplicate entry error
            if  str(e):
                return JsonResponse({'status': 'error', 'message': 'Data already exists'}, status=400)
            else:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Metode tidak diizinkan'}, status=405)

@login_required
def update_code(request, id):
    allowed_groups = ['superadmin','admin-mgoqa','data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )
    if request.method == 'POST':
        try:
            job = SellingCode.objects.get(id=int(id))
            job.product_code = request.POST.get('product_code')
            job.description  = request.POST.get('description')
            job.type         = request.POST.get('type')
            job.active       = 1
            job.save()

            return JsonResponse({
                'id'          : job.id,
                'product_code': job.product_code,
                'description' : job.description,
                'active'      : job.active,
                'type'        : job.type,
                'created_at'  : job.created_at
            })
        except SellingCode.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
        except IntegrityError as e:
            error_message = str(e)
            return JsonResponse({'error': 'The data already exists', 'message': error_message}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Metode tidak diizinkan'}, status=405)

@login_required
def delete_code(request):
    allowed_groups = ['superadmin']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )
    if request.method == 'DELETE':
        job_id = request.GET.get('id')
        if job_id:
            # Lakukan penghapusan berdasarkan ID di sini
            data = SellingCode.objects.get(id=int(job_id))
            data.delete()
            return JsonResponse({'status': 'deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

