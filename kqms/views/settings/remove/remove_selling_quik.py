# 
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import json
from django.http import JsonResponse
from django.db.models import Case, When, Value, IntegerField
from datetime import datetime
from ....models.selling_barging_temp import SellingBargingTemp
from ....models.selling_details_barging import SellingDetailsBargingTempView
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.views import View



class saleTempRemoveView(View):
    def post(self, request):
        # Ambil semua data invoice yang valid
        data_ore = self._datatables(request)
        return JsonResponse(data_ore, safe=False)

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
        data = SellingDetailsBargingTempView.objects.all()

        if search:
            data = data.filter(
                Q(shift__icontains=search) |
                Q(dome__icontains=search) |
                Q(unit_code__icontains=search) |
                Q(material__icontains=search) |
                Q(code_lot__icontains=search) 
            )

        data = data.filter(status=0)
        # Filter berdasarkan parameter dari request
        from_date  = request.POST.get('start_date')
        to_date    = request.POST.get('end_date')
        code_lot   = request.POST.get('code_lot')

        if from_date and to_date:
            data = data.filter(date_hauling__range=[from_date, to_date])


        if code_lot:
            data = data.filter(code_lot=code_lot)

        columns_map = {
            1: 'date_hauling',
            2: 'time_hauling',
            3: 'barge_code',
            4: 'shift',
            5: 'dome',
            6: 'stockpile',
            7: 'material',
            8: 'unit_code',
            9: 'tonnage',
            10: 'code_lot',
            11: 'code_inc',
            12: 'code_sub',
            13: 'type_selling',
            14: 'no_urut',
        }


        order_column = int(datatables.get('order[0][column]', -1))
        order_dir = datatables.get('order[0][dir]', 'asc')

        if order_column in columns_map:
            field_name = columns_map[order_column]
            order_by = f'-{field_name}' if order_dir == 'desc' else field_name
            data = data.order_by(order_by)
        else:
            data = data.annotate(
                shift_order=Case(
                    When(shift="Day", then=Value(1)),
                    When(shift="Night", then=Value(2)),
                    default=Value(3),
                    output_field=IntegerField(),
                )
            ).order_by('-date_hauling', 'shift_order', 'time_hauling', 'no_urut')

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
            object_list = paginator.page(paginator.num_pages).object_list

        data = [
            {
                "id"           : item.id,
                "date_hauling" : item.date_hauling,
                "time_hauling" : item.time_hauling,
                "barge_code"   : item.barge_code,
                "shift"        : item.shift,
                "dome"         : item.dome,
                "stockpile"    : item.stockpile,
                "material"     : item.material,
                "unit_code"    : item.unit_code,
                "tonnage"      : item.tonnage,
                "code_lot"     : item.code_lot,
                "code_inc"     : item.code_inc,
                "code_sub"     : item.code_sub,
                "type_selling" : item.type_selling,
                "no_urut"      : item.no_urut
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

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from datetime import datetime
import json

@login_required
@csrf_exempt
def update_sale_temp_bulk(request):
    allowed_groups = ['superadmin','data-control','admin-mgoqa','admin-selling']
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
            code_lot   = body.get('code_lot')

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

            # filter data
            data = SellingBargingTemp.objects.filter(
                date_hauling__range=[start_date, end_date]
            )
            if code_lot:
                data = data.filter(code_lot=code_lot)

            if data.exists():
                updated_count = data.update(status=1)  # ubah status sesuai kebutuhan
                return JsonResponse({
                    'status': 'updated',
                    'message': f'{updated_count} records between {start_date} - {end_date} updated (status=1)'
                })
            else:
                return JsonResponse({'status': 'error', 'message': 'No records found in this range'}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
