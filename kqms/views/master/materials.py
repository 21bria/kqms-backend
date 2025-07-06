# 
from django.contrib.auth.decorators import login_required
from ...models.materials import Material
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied


@login_required(login_url='/sqms_apps/login/')
def material_page(request):

    return render(request, 'master/list-materials.html')

class Materials_List(View):
    def post(self, request):
        # Ambil semua data invoice yang valid
        material = self._datatables(request)
        return JsonResponse(material, safe=False)

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
        records_total = Material.objects.all().count()
        # Set records filtered
        records_filtered = records_total
        # Ambil semua yang valid
        data = Material.objects.all()

        if search:
            data = Material.objects.filter(
                Q(nama_material__icontains=search) |
                Q(keterangan__icontains=search)
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
                "id": item.id,
                "nama_material": item.nama_material,
                "keterangan": item.keterangan,
            } for item in object_list
        ]

        return {
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        }

@csrf_exempt
@login_required
def get_material(request, id):
    # allowed_groups = ['superadmin', 'admin-mgoqa']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission get data.'}, 
    #         status=403
    # )
    if request.method == 'GET':
        try:
            job = Material.objects.get(id=id)
            data = {
                'id'            : job.id,
                'nama_material' : job.nama_material, 
                'keterangan'    : job.keterangan,
                'created_at'    : job.created_at
            }
            return JsonResponse(data)
        except Material.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required(login_url='/sqms_apps/login/')
def insert_material(request):
    # allowed_groups = ['superadmin', 'admin-mgoqa']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission to insert data.'}, 
    #         status=403
    # )
    
    if request.method == 'POST':
        nama_material = request.POST.get('nama_material')
        keterangan    = request.POST.get('keterangan')

        try:
            new_job = Material.objects.create(nama_material=nama_material, keterangan=keterangan)
            return JsonResponse({
                'status' : 'success',
                'message': 'Data berhasil disimpan.',
                'data': {
                    'id'            : new_job.id,
                    'nama_material' : new_job.nama_material,
                    'keterangan'    : new_job.keterangan,
                    'created_at'    : new_job.created_at
                }
            })
        except IntegrityError as e:
            # Check if the error is a duplicate entry error
            if 'Duplicate entry' in str(e):
                return JsonResponse({'status': 'error', 'message': 'The data already exists'}, status=404)
            else:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Metode tidak diizinkan'}, status=405)

@login_required
def update_material(request, id):
    # allowed_groups = ['superadmin', 'admin-mgoqa']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission to edit data.'}, 
    #         status=403
    # )

    if request.method == 'POST':
        try:
            job = Material.objects.get(id=id)
            job.nama_material  = request.POST.get('nama_material')
            job.keterangan     = request.POST.get('keterangan')
            job.save()

            return JsonResponse({
                'id'            : job.id,
                'nama_material' : job.nama_material,
                'keterangan'    : job.keterangan,
                'created_at'    : job.created_at
            })
        
        except Material.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
        except IntegrityError as e:
            error_message = str(e)
            if 'Duplicate entry' in error_message:
                 return JsonResponse({'error': 'Duplikat data: Data sudah digunakan', 'message': error_message}, status=400)
            else:
                 return JsonResponse({'error': 'Error pada operasi database', 'message': error_message}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Metode tidak diizinkan'}, status=405)

@login_required
def delete_material(request):
    # allowed_groups = ['superadmin']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission to delete data.'}, 
    #         status=403
    #     )

    if request.method == 'DELETE':
        job_id = request.GET.get('id')
        if job_id:
            try:
                data = Material.objects.get(id=int(job_id))
                data.delete()
                return JsonResponse({'status': 'success', 'message': 'Data successfully deleted.'})
            except Material.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Data not found.'}, status=404)
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided.'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)
    
