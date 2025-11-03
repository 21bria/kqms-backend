# 
from django.contrib.auth.decorators import login_required
import json
from django.http import JsonResponse
from datetime import datetime
from ....models.ore_productions import OreProductions
from ....models.selling_barging import SellingBarging
from ....models.ore_production_view import OreProductionsView
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.views import View


class gcDataDeleteView(View):
    def post(self, request):
        # Ambil semua data invoice yang valid
        data_pds = self._datatables(request)
        return JsonResponse(data_pds, safe=False)

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
        data = OreProductionsView.objects.all()

        if search:
            data = data.filter(
                Q(shift__icontains=search) |
                Q(prospect_area__icontains=search) |
                Q(mine_block__icontains=search) |
                Q(nama_material__icontains=search) |
                Q(ore_class__icontains=search) |
                Q(grade_control__icontains=search) |
                Q(unit_truck__icontains=search) |
                Q(stockpile__icontains=search) |
                Q(pile_id__icontains=search) |
                Q(sample_number__icontains=search)
            )
       
        # Filter berdasarkan parameter dari request
        start_date = request.POST.get('start_date')
        end_date   = request.POST.get('end_date')
        shift      = request.POST.get('shift')
 
        if start_date and end_date:
            data = data.filter(tgl_production__range=[start_date, end_date])

        if shift:
            data = data.filter(shift=shift)

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
            object_list = paginator.page(paginator.num_pages).object_lis

        
        data = [
            {
                "id"            : item.id,
                "tgl_production": item.tgl_production,
                "category"      : item.category,
                "shift"         : item.shift,
                "prospect_area" : item.prospect_area,
                "mine_block"    : item.mine_block,
                "rl"            : (str(item.from_rl) if item.from_rl is not None else '') + '-' + (str(item.to_rl) if item.to_rl is not None else ''),
                "nama_material" : item.nama_material,
                "ore_class"     : item.ore_class,
                "ni_grade"      : item.ni_grade,
                "grade_control" : item.grade_control,
                "unit_truck"    : item.unit_truck,
                "stockpile"     : item.stockpile,
                "pile_id"       : item.pile_id,
                "batch_code"    : item.batch_code,
                "increment"     : item.increment,
                "batch_status"  : item.batch_status,
                "ritase"        : item.ritase,
                "tonnage"       : round(item.tonnage, 2),
                "pile_status"   : item.pile_status,
                "truck_factor"  : item.truck_factor,
                "remarks"       : item.remarks,
                "sample_number" : item.sample_number
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

# @login_required
# @csrf_exempt
# def delete_data_gc_bulk(request):
#     allowed_groups = ['superadmin', 'data-control', 'admin-mgoqa']
#     if not request.user.groups.filter(name__in=allowed_groups).exists():
#         return JsonResponse(
#             {'status': 'error', 'message': 'You do not have permission'}, 
#             status=403
#         )

#     if request.method == 'DELETE':
#         try:
#             body = json.loads(request.body)
#             start_date = body.get('start_date')
#             end_date   = body.get('end_date')
#             shift      = body.get('shift')

#             if not start_date or not end_date:
#                 return JsonResponse(
#                     {'status': 'error', 'message': 'Start and End date required'},
#                     status=400
#                 )

#             try:
#                 start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
#                 end_date   = datetime.strptime(end_date, "%Y-%m-%d").date()
#             except ValueError:
#                 return JsonResponse({'status': 'error', 'message': 'Invalid date format'}, status=400)

#             # filter data
#             data = OreProductions.objects.filter(
#                 tgl_production__range=[start_date, end_date]
#             )
#             if shift:
#                 data = data.filter(shift=shift)

#             if data.exists():
#                 deleted_count, _ = data.delete()
#                 return JsonResponse({
#                     'status' : 'deleted',
#                     'message': f'{deleted_count} records between {start_date} - {end_date} deleted'
#                 })
#             else:
#                 return JsonResponse({'status': 'error', 'message': 'No records found in this range'}, status=404)

#         except json.JSONDecodeError:
#             return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
#     else:
#         return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@login_required
@csrf_exempt
def delete_data_gc_bulk(request):
    allowed_groups = ['superadmin', 'data-control', 'admin-mgoqa']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
        )

    if request.method == 'DELETE':
        try:
            body = json.loads(request.body)
            start_date = body.get('start_date')
            end_date   = body.get('end_date')
            shift      = body.get('shift')

            if not start_date or not end_date:
                return JsonResponse(
                    {'status': 'error', 'message': 'Start and End date required'},
                    status=400
                )

            try:
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_date   = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Invalid date format'}, status=400)

            # filter data OreProductions sesuai tanggal dan shift
            data = OreProductions.objects.filter(
                tgl_production__range=[start_date, end_date]
            )
            if shift:
                data = data.filter(shift=shift)

            if not data.exists():
                return JsonResponse({'status': 'error', 'message': 'No records found in this range'}, status=404)

            # ambil semua id_pile unik dari data ini
            ore_pile_ids = list(data.values_list('id_pile', flat=True).distinct())

            # cari id_pile yang dipakai di SellingBarging
            used_pile_ids = list(SellingBarging.objects.filter(id_pile__in=ore_pile_ids).values_list('id_pile', flat=True).distinct())

            # pisahkan data yang boleh dan tidak boleh dihapus
            allowed_to_delete = data.exclude(id_pile__in=used_pile_ids)
            protected_data    = data.filter(id_pile__in=used_pile_ids)

            deleted_count, _ = allowed_to_delete.delete()
            protected_count  = protected_data.count()

            message = f"{deleted_count} records deleted"
            if protected_count > 0:
                message += f", {protected_count} skipped (id_pile linked to SellingBarging)"

            return JsonResponse({
                'status'    : 'success',
                'message'   : message,
                'deleted_count': deleted_count,
                'skipped_count': protected_count
            })

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
