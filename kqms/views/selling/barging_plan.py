from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ...models.selling_plan_barging import SellingPlanBarging
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.views import View
import calendar
from datetime import datetime, timedelta
from django.db.models import Case, When, Value, IntegerField

@login_required
def sale_barge_plan_page(request):
    today = datetime.today()
    first_day_of_month = today.replace(day=1)  # Tanggal awal bulan berjalan
    context = {
        'start_date' : first_day_of_month.strftime('%Y-%m-%d'),
        'end_date'   : today.strftime('%Y-%m-%d'),
    }

    return render(request, 'admin-selling/plan/list-plan-barging.html', context)

class bargingDataPlan(View):
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

        # get Data
        data = SellingPlanBarging.objects.all()

        if search:
            data = data.filter(
                Q(type_ore__icontains=search)
            )
       

        # Filter berdasarkan parameter dari request
        startDate  = request.POST.get('startDate')
        endDate    = request.POST.get('endDate')
        materialFilter  = request.POST.get('materialFilter')

        if startDate and endDate:
            data = data.filter(plan_date__range=[startDate, endDate])

        if materialFilter:
            data = data.filter(type_ore=materialFilter)

        # Atur sorting
        # if order_dir == 'desc':
        #     order_by = f'-{data.model._meta.fields[order_column].name}'
        # else:
        #     order_by = f'{data.model._meta.fields[order_column].name}'

        # data = data.order_by(order_by)


        # mapping order column datatables
        columns_map = {
            0: 'plan_date',
            1: 'type_ore',
            2: 'tonnage_plan',
            3: 'ni_plan',
            4: 'co_plan',
            5: 'fe_plan',
            6: 'sio2_plan',
            7: 'al2o3_plan',
            8: 'mgo_plan',
            9: 'sm_plan',
        }

        order_column = int(datatables.get('order[0][column]', -1))
        order_dir = datatables.get('order[0][dir]', 'asc')

        if order_column in columns_map:
            field_name = columns_map[order_column]
            order_by = f'-{field_name}' if order_dir == 'desc' else field_name
            data = data.order_by(order_by)
        else:
            data = data.annotate(
                material_order=Case(
                    When(type_ore="LIM", then=Value(1)),
                    When(type_ore="SAP", then=Value(2)),
                    default=Value(3),
                    output_field=IntegerField(),
                )
            ).order_by('-plan_date', 'material_order')

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
                "id"          : item.id,
                "plan_date"   : item.plan_date,
                "type_ore"    : item.type_ore,
                "tonnage_plan": f"{item.tonnage_plan:.2f}",
                "ni_plan"     : f"{item.ni_plan:.2f}",
                "co_plan"     : f"{item.co_plan:.2f}",
                "fe_plan"     : f"{item.fe_plan:.2f}",
                "sio2_plan"   : f"{item.sio2_plan:.2f}",
                "al2o3_plan"  : f"{item.al2o3_plan:.2f}",
                "mgo_plan"    : f"{item.mgo_plan:.2f}",
                "sm_plan"     : f"{item.sm_plan:.2f}",
                "created_at"  : item.created_at.strftime('%Y-%m-%d %H:%M:%S')
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
def delete_barging_plan(request):
    allowed_groups = ['superadmin','data-control','admin-mining','admin-mgoqa']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
        )

    if request.method == 'DELETE':
        try:
            import json
            body = json.loads(request.body.decode('utf-8'))
            month_date = body.get('month_date')   # format: YYYY-MM
            materials  = body.get('materials')    # bisa kosong / null / string

            if not month_date:
                return JsonResponse({'status': 'error', 'message': 'Month date required'}, status=400)

            # ambil tahun & bulan
            try:
                year, month = map(int, month_date.split('-'))
            except Exception:
                return JsonResponse({'status': 'error', 'message': 'Invalid month_date format'}, status=400)

            days_in_month = calendar.monthrange(year, month)[1]
            start_date = datetime(year, month, 1).date()
            end_date   = datetime(year, month, days_in_month).date()

            # filter query
            qs = SellingPlanBarging.objects.filter(plan_date__range=[start_date, end_date])
            if materials:
                qs = qs.filter(type_ore=materials)

            deleted_count, _ = qs.delete()

            return JsonResponse({'status': 'deleted', 'message': f'{deleted_count} record(s) deleted'})

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON body'}, status=400)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)