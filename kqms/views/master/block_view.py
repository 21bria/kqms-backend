from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ...models.block_model import Block  # Sesuaikan dengan path yang benar
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.shortcuts import render
from django.views.generic import View
from django.db.models import Q

@login_required
def block_page(request):
    return render(request, 'master/list-block.html') 


class AjaxBlockList(View):
    def post(self, request):
        # Ambil semua data invoice yang valid
        block = self._datatables(request)
        return JsonResponse(block, safe=False)
        
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
        records_total = Block.objects.all().count()
        # Set records filtered
        records_filtered = records_total
        # Ambil semua yang valid
        block = Block.objects.all()

        if search:
            block = Block.objects.filter(
                Q(mine_block__icontains=search) |
                Q(keterangan__icontains=search)
            )
            records_total = block.count()
            records_filtered = records_total

        # Atur sorting
        if order_dir == 'desc':
            order_by = f'-{block.model._meta.fields[order_column].name}'
        else:
            order_by = f'{block.model._meta.fields[order_column].name}'

        block = block.order_by(order_by)

        # Atur paginator
        paginator = Paginator(block, length)

        try:
            object_list = paginator.page(start // length + 1).object_list
        except PageNotAnInteger:
            object_list = paginator.page(1).object_list
        except EmptyPage:
            object_list = paginator.page(paginator.num_pages).object_list

        data = [
            {
                "id": item.id,
                "mine_block": item.mine_block,
                "keterangan": item.keterangan,
                "status": item.status
            } for item in object_list
        ]

        return {
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        }

@csrf_exempt 
def get_block(request, id):
    # allowed_groups = ['superadmin', 'admin-mgoqa']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'GET':
        try:
            job = Block.objects.get(id=id)
            data = {
                'id': job.id,
                'mine_block': job.mine_block, 
                'keterangan': job.keterangan,
                'status': job.status, 
                'created_at': job.created_at
            }
            return JsonResponse(data)
        except Block.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def insert_block(request):
    # allowed_groups = ['superadmin', 'admin-mgoqa']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'POST':
        mine_block = request.POST.get('mine_block')
        keterangan = request.POST.get('keterangan')
        status     = request.POST.get('status')

        try:
            new_job = Block.objects.create(mine_block=mine_block, keterangan=keterangan, status=status)
            return JsonResponse({
                'status': 'success',
                'message': 'Data berhasil disimpan.',
                'data': {
                    'id'        : new_job.id,
                    'mine_block': new_job.mine_block,
                    'keterangan': new_job.keterangan,
                    'status'    : new_job.status,
                    'created_at': new_job.created_at
                }
            })
        except IntegrityError as e:
            # Check if the error is a duplicate entry error
            if 'Duplicate entry' in str(e):
                return JsonResponse({'status': 'error', 'message': 'Mine block sudah ada'}, status=403)
            else:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Metode tidak diizinkan'}, status=405)
    
@login_required
def update_block(request, id):
    # allowed_groups = ['superadmin', 'admin-mgoqa']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'POST':
        try:
            job = Block.objects.get(id=id)
            job.mine_block  = request.POST.get('mine_block')
            job.keterangan  = request.POST.get('keterangan')
            job.status      = 1
            job.save()

            return JsonResponse({
                'id'        : job.id,
                'mine_block': job.mine_block,
                'keterangan': job.keterangan,
                'status'    : job.status,
                'created_at': job.created_at
            })
        except Block.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
        except IntegrityError as e:
            error_message = str(e)
            if 'Duplicate entry' in error_message:
                 return JsonResponse({'error': 'Duplikat data: mine_block sudah digunakan', 'message': error_message}, status=400)
            else:
                 return JsonResponse({'error': 'Error pada operasi database', 'message': error_message}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Metode tidak diizinkan'}, status=405)

@login_required
def delete_block(request):
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
            block = Block.objects.get(id=int(job_id))
            block.delete()
            return JsonResponse({'status': 'deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

