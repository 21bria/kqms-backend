from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ...models.mine_fuel_consumption import FuelConsumptionView,FuelConsumption
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import datetime
from django.utils.dateparse import parse_date
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
def daily_fuel_page(request):
    today = datetime.today()
    first_day_of_month = today.replace(day=1)  # Tanggal awal bulan berjalan
    context = {
        'start_date' : first_day_of_month.strftime('%Y-%m-%d'),
        'end_date'   : today.strftime('%Y-%m-%d'),
    }

    return render(request, 'admin-mine/fueling/list-daily-fuel.html', context)

class viewDailyFuel(View):

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
        data = FuelConsumptionView.objects.all()

        if search:
            data = data.filter(
                Q(category__icontains=search) |
                Q(vendors__icontains=search) 
            )
       
        # Filter berdasarkan parameter dari request
        startDate = request.POST.get('startDate')
        endDate   = request.POST.get('endDate')
        category  = request.POST.get('category')

        if startDate and endDate:
            data = data.filter(date__range=[startDate, endDate])
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
                "id"            : item.id,
                "date"          : item.date,
                "shift"         : item.shift,
                "unit"          : item.unit,
                "category"      : item.category,
                "hours_metre"   : item.hours_metre,
                "drivers"       : item.drivers,
                "charging_time" : item.charging_time,
                "volume"        : item.volume,
                "storage"       : item.storage,
                "operator"      : item.operator,
                "created_at"    : item.created_at
                
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
def get_fuel_by_unit(request, unit_id):
    allowed_groups = ['superadmin', 'admin-mgoqa', 'data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)

    date_str = request.GET.get('date')

    try:
        fuels = FuelConsumption.objects.filter(unit=unit_id)

        if date_str:
            date_obj = parse_date(date_str)
            fuels = fuels.filter(date=date_obj)

        fuels = fuels.order_by('charging_time')

        day, night = [], []
        total_volume = 0

        for f in fuels:
            shift = (f.shift or '').upper()
            volume = f.volume or 0

            item = {
                "id": f.id,
                "start_time": f.charging_time.strftime("%H:%M"),
                "volume": volume,
                "operator": f.operator,
                "shift": shift,
                "hours_metre": f.hours_metre,
            }

            total_volume += volume

            if shift == 'DAY':
                day.append(item)
            elif shift == 'NIGHT':
                night.append(item)

        return JsonResponse({
            "success": True,
            "unit_id": unit_id,
            "date": date_str,
            "total_volume": total_volume,  
            "day": day,
            "night": night
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=500)
