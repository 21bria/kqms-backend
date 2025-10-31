# 
from django.contrib.auth.decorators import login_required
import json
from django.http import JsonResponse
from ....models.selling_details_barging import SellingDetailsBargingView
from ....models.selling_barging import SellingBarging
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.views import View
# from ....utils.permissions import get_dynamic_permissions


class bargingDataView(View):
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

        code_lot  = request.POST.get('code_lot')

        data = SellingDetailsBargingView.objects.all()

    
        data = data.filter(code_lot=code_lot)

        if search:
            data = data.filter(Q(nama_material__icontains=search))

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
                "id"              : item.id,
                "date_barge_in"   : item.date_barge_in,
                "date_hauling"    : item.date_hauling,
                "barge_code"      : item.barge_code,
                "shift"           : item.shift,
                "stockpile"       : item.stockpile,
                "dome"            : item.dome,
                "unit_code"       : item.unit_code,
                "material"        : item.material,
                "code_lot"        : item.code_lot,
                "batch"           : item.batch,
                "code_inc"        : item.code_inc,
                "ritase"          : item.ritase,
                "tonnage"         : item.tonnage,
                "sale_adjust"     : item.sale_adjust,
                "date_barge_out"  : item.date_barge_out,
                "status_barging"  : item.status_barging,
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
def delete_barging_bulk(request):
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
                data = SellingBarging.objects.filter(code_lot=job_id)

                if data.exists():
                    data.delete()  # Delete all matching entries
                    return JsonResponse({'status': 'deleted'})
                else:
                    return JsonResponse({'status': 'error', 'message': 'Code not found'})
            else:
                return JsonResponse({'status': 'error', 'message': 'No ID provided'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    
