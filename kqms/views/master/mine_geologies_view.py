from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ...models.mine_geologies import MineGeologies
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from ...utils.utils import clean_string


@login_required
def geologies_page(request):
    return render(request, 'master/list-geologies.html')

class MineGeologiesList(View):

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
        records_total = MineGeologies.objects.all().count()
        # Set records filtered
        records_filtered = records_total
        # Ambil semua yang valid
        data = MineGeologies.objects.all()

        if search:
            data = MineGeologies.objects.filter(
                Q(mg_code__icontains=search) |
                Q(mg_name__icontains=search)
            )
            records_total = data.count()
            records_filtered = records_total

        # Atur sorting
        if order_dir == 'desc':
            order_by = f'-{data.model._meta.fields[order_column].name}'
        else:
            order_by = f'{data.model._meta.fields[order_column].name}'

        data = data.order_by(order_by)

        # Atur paginator
        paginator = Paginator(data, length)

        try:
            object_list = paginator.page(start // length + 1).object_list
        except PageNotAnInteger:
            object_list = paginator.page(1).object_list
        except EmptyPage:
            object_list = paginator.page(paginator.num_pages).object_list

        data = [
            {
                "id"      : item.id,
                "mg_code" : item.mg_code,
                "mg_name" : item.mg_name,
                "status"  : item.status,
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
def get_geologies(request, id):
    # allowed_groups = ['superadmin','admin-mgoqa']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'GET':
        try:
            job = MineGeologies.objects.get(id=id)
            data = {
                'id'      : job.id,
                'mg_code' : clean_string(job.mg_code), 
                'mg_name' : clean_string(job.mg_name),
                'status'  : clean_string(job.status)
            }
            return JsonResponse(data)
        except MineGeologies.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required    
def insert_geologies(request):
    # allowed_groups = ['superadmin','admin-mgoqa']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'POST':
        mg_code = request.POST.get('mg_code')
        mg_name = request.POST.get('mg_name') 
        status  = 1

        try:
            new_job = MineGeologies.objects.create(
                      mg_code=mg_code,
                      mg_name=mg_name,
                      status=status)
            
            return JsonResponse({
                'status' : 'success',
                'message': 'Data berhasil disimpan.',
                'data': {
                    'id'         : new_job.id,
                    'mg_code'    : new_job.mg_code,
                    'mg_name'    : new_job.mg_name,
                    'status'     : new_job.status,
                    'created_at' : new_job.created_at
                }
            })
        except IntegrityError as e:
            # Check if the error is a duplicate entry error
            if  str(e):
                return JsonResponse({'status': 'error', 'message': 'The data already exists'}, status=400)
            else:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Metode tidak diizinkan'}, status=405)
    
@login_required
def update_geologies(request, id):
    # allowed_groups = ['superadmin','admin-mgoqa']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'POST':
        try:
            job = MineGeologies.objects.get(id=int(id))
            job.mg_code = request.POST.get('mg_code')
            job.mg_name = request.POST.get('mg_name')
            job.save()

            return JsonResponse({
                'id'         : job.id,
                'mg_name'    : job.mg_name,
                'mg_name'    : job.mg_name,
                'created_at' : job.created_at,
                'updated_at' : job.updated_at
            })
        
        except MineGeologies.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
        except IntegrityError as e:
            error_message = str(e)
            return JsonResponse({'error': 'The data already exists', 'message': error_message}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Metode tidak diizinkan'}, status=405)
    
@login_required
def delete_geologies(request):
    # allowed_groups = ['superadmin']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'DELETE':
        job_id = request.GET.get('id')
        if job_id:
            # Lakukan penghapusan berdasarkan ID di sini
            data = MineGeologies.objects.get(id=int(job_id))
            data.delete()
            return JsonResponse({'status': 'deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    
