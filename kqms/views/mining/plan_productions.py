from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ...models.plan_productions import planProductions
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import datetime
import calendar
from django.views.decorators.csrf import csrf_exempt
from django.views import View

def format_angka(jumlah):
    if jumlah >= 1_000_000_000:
        return f"{jumlah / 1_000_000_000:.2f} B"
    elif jumlah >= 1_000_000:
        return f"{jumlah / 1_000_000:.2f} M"
    elif jumlah >= 1_000:
        return f"{jumlah / 1_000:.2f} K"
    else:
        return str(jumlah)
    
@login_required
def plan_mine_production_page(request):
    today = datetime.today()
    first_day_of_month = today.replace(day=1)  # Tanggal awal bulan berjalan
    context = {
        'start_date' : first_day_of_month.strftime('%Y-%m-%d'),
        'end_date'   : today.strftime('%Y-%m-%d'),
    }

    return render(request, 'admin-mine/list-plan-productions.html', context)

class viewPlanMineProduction(View):

    def post(self, request):
        data_mine = self._datatables(request)
        return JsonResponse(data_mine, safe=False)

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

        # Call Data
        data = planProductions.objects.all()

        if search:
            data = data.filter(
                Q(category__icontains=search) |
                Q(sources__icontains=search) |
                Q(vendors__icontains=search) 
            )
       
        # Filter berdasarkan parameter dari request
        startDate = request.POST.get('startDate')
        endDate   = request.POST.get('endDate')
        sources   = request.POST.get('sources')
        vendors   = request.POST.get('vendors')
        category  = request.POST.get('category')

        if startDate and endDate:
            data = data.filter(date_plan__range=[startDate, endDate])
        if sources:
            data = data.filter(sources=sources)
        if vendors:
            data = data.filter(vendors=vendors)
        if category:
            data = data.filter(category=category)

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
            object_list = paginator.page(paginator.num_pages).object_list

        data = [
            {
                "id"       : item.id,
                "date_plan": item.date_plan,
                "category" : item.category,
                "sources"  : item.sources,
                "vendors"  : item.vendors,
                "TopSoil"  : item.topsoil,
                "OB"       : item.ob,
                "LGLO"     : item.lglo,
                "MGLO"     : item.mglo,
                "HGLO"     : item.hglo,
                "Waste"    : item.waste,
                "MWS"      : item.mws,
                "LGSO"     : item.lgso,
                "UGLO"     : item.uglo,
                "MGSO"     : item.mgso,
                "HGSO"     : item.hgso,
                "Lim"     : item.lim,
                "Sap"     : item.sap,
                "Quarry"   : item.quarry,
                "Ballast"  : item.ballast,
                "Biomass"  : item.biomass
                
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
def delete_productions_plan(request):
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
    

            if not month_date:
                return JsonResponse({'status': 'error', 'message': 'Month date required'}, status=400)

            # ambil tahun & bulan
            try:
                year, month = map(int, month_date.split('-'))
            except Exception:
                return JsonResponse({'status': 'error', 'message': 'Invalid month_date format'}, status=400)

            days_in_month = calendar.monthrange(year, month)[1]
            start_date    = datetime(year, month, 1).date()
            end_date      = datetime(year, month, days_in_month).date()

            # filter query
            qs = planProductions.objects.filter(date_plan__range=[start_date, end_date])
        
            deleted_count, _ = qs.delete()

            return JsonResponse({'status': 'deleted', 'message': f'{deleted_count} record(s) deleted'})

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON body'}, status=400)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)