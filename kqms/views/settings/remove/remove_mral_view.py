# 
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import json
from django.http import JsonResponse
from ....models.assay_mral_model import AssayMral
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.views import View


class mralDataView(View):
    def post(self, request):
        # Ambil semua data invoice yang valid
        data_mral = self._datatables(request)
        return JsonResponse(data_mral, safe=False)

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

        job_number  = request.POST.get('job_number')
        from_sample = request.POST.get('from_sample')
        to_sample   = request.POST.get('to_sample')

        # --- Kondisi agar data awal kosong ---
        if not job_number and not (from_sample and to_sample):
            return {
                'draw'           : draw,
                'recordsTotal'   : 0,
                'recordsFiltered': 0,
                'data'           : [],
                'start'          : start,
                'length'         : length,
                'totalPages'     : 0
            }

        # --- Jika filter diisi, baru ambil data ---
        data = AssayMral.objects.all()

        if job_number:
            data = data.filter(job_number=job_number)

        if from_sample and to_sample:
            data = data.filter(sample_id__range=[from_sample, to_sample])

        if search:
            data = data.filter(Q(sample_id__icontains=search))

        # Atur sorting
        if order_dir == 'desc':
            order_by = f'-{data.model._meta.fields[order_column].name}'
        else:
            order_by = f'{data.model._meta.fields[order_column].name}'

        data = data.order_by(order_by)

        # Menghitung jumlah total sebelum filter
        records_total = data.count()

        # Menerapkan pagination
        paginator = Paginator(data, length)
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
                "release_mral": item.release_mral.strftime("%Y-%m-%d %H:%M:%S"),
                "job_number": item.job_number,
                "sample_id": item.sample_id,
                "ni": item.ni,
                "co": item.co,
                "fe2o3": item.fe2o3,
                "fe": item.fe,
                "mgo": item.mgo,
                "sio2": item.sio2
                } for item in object_list
        ]

        return {
            'draw'           : draw,
            'recordsTotal'   : records_total,
            'recordsFiltered': total_records_filtered,
            'data'           : data,
            'start'          : start,
            'length'         : length,
            'totalPages'     : total_pages
        }

@login_required    
@csrf_exempt       
def delete_mral_number(request):
    allowed_groups = ['superadmin','admin-mgoqa','data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )
    if request.method == 'DELETE':
        try:
            body = json.loads(request.body)
            job_id = body.get('id')

            if job_id:
                # Use filter() instead of get()
                data = AssayMral.objects.filter(job_number=job_id)

                if data.exists():
                    data.delete()  # Delete all matching entries
                    return JsonResponse({'status': 'deleted'})
                else:
                    return JsonResponse({'status': 'error', 'message': 'Job numbers not found'})
            else:
                return JsonResponse({'status': 'error', 'message': 'No ID provided'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
@csrf_exempt
def delete_mral_by_checked(request):
    allowed_groups = ['superadmin', 'admin-mgoqa', 'data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse({'status': 'error', 'message': 'You do not have permission'}, status=403)

    if request.method == 'DELETE':
        try:
            body = json.loads(request.body)
            ids = body.get('ids', [])  # Ambil array sample_id

            if not ids:
                return JsonResponse({'status': 'error', 'message': 'No IDs provided'})

            # Hapus semua record dengan sample_id dalam daftar
            deleted_count, _ = AssayMral.objects.filter(sample_id__in=ids).delete()

            if deleted_count > 0:
                return JsonResponse({'status': 'deleted', 'deleted_count': deleted_count})
            else:
                return JsonResponse({'status': 'error', 'message': 'No matching data found'})

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
