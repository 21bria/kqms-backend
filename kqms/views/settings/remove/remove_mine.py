# 
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import json
from django.http import JsonResponse
from datetime import datetime
from ....models.mine_productions import mineProductions
from ....models.mine_productions_view import mineProductionsView
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.views import View


class mineRemoveView(View):
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
        data = mineProductionsView.objects.all()

        if search:
            data = data.filter(
                Q(shift__icontains=search) |
                Q(loading_point__icontains=search) |
                Q(dumping_point__icontains=search) |
                Q(nama_material__icontains=search) 
            )
       
        # Filter berdasarkan parameter dari request
        start_date = request.POST.get('start_date')
        end_date   = request.POST.get('end_date')
 
        if start_date and end_date:
            data = data.filter(date_production__range=[start_date, end_date])


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
                "id"                : item.id,
                "date_production"   : item.date_production,
                "shift"             : item.shift,
                "loader"            : item.loader,
                "bucket"            : item.bucket,
                "hauler"            : item.hauler,
                "hauler_class"      : item.hauler_class,
                "sources_area"      : item.sources_area,
                "loading_point"     : item.loading_point,
                "dumping_point"     : item.dumping_point,
                "dome_id"           : item.dome_id,
                "category_mine"     : item.category_mine,
                "time_loading"      : item.time_loading,
                "nama_material"     : item.nama_material,
                "ritase"            : item.ritase,
                "tonnage"           : round(item.tonnage,2) 
                
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

@login_required
@csrf_exempt
def delete_mine_bulk(request):
    allowed_groups = ['superadmin','admin-mining']
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

            if not start_date or not end_date:
                return JsonResponse(
                    {'status': 'error', 'message': 'Start and End date required'},
                    status=400
                )

            # pastikan format tanggal sesuai
            try:
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_date   = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Invalid date format'}, status=400)

            # filter data di rentang tanggal
            data = mineProductions.objects.filter(date_production__range=[start_date, end_date])

            if data.exists():
                deleted_count = data.count()
                data.delete()
                return JsonResponse({
                    'status': 'deleted',
                    'message': f'{deleted_count} records between {start_date} - {end_date} deleted'
                })
            else:
                return JsonResponse({'status': 'error', 'message': 'No records found in this range'}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
