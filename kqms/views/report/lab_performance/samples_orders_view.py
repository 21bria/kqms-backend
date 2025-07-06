from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
# import datetime
from datetime import datetime, timedelta
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import logging
from django.db.models import Q
from ....models.lab_performance_view import laboratoryPerformanceView
logger = logging.getLogger(__name__)

@login_required
def sampleTatOrders(request):
    today = datetime.today()
    last_monday = today - timedelta(days=today.weekday())
    context = {
        'start_date': last_monday.strftime('%Y-%m-%d'),
        'end_date'  : today.strftime('%Y-%m-%d'),
    }
    return render(request, 'admin-mgoqa/report-qa/sample-tat-orders.html',context)


#List Data Tables:
class samplesOrders(View):
    
    def post(self, request):
        # Ambil semua data invoice yang valid
        data_orders = self._datatables(request)
        return JsonResponse(data_orders, safe=False)

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
        data = laboratoryPerformanceView.objects.all()

        if search:
            data = data.filter(
                Q(waybill_number__icontains=search) |
                Q(sample_id__icontains=search) |
                Q(job_number_mral__icontains=search) |
                Q(job_number_roa__icontains=search) 
            )
       
        # Filter berdasarkan parameter dari request
        startDate = request.POST.get('startDate')
        endDate   = request.POST.get('endDate')

        if startDate and endDate:
            data = data.filter(tgl_deliver__range=[startDate, endDate])

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
                "id"            : item.id,
                "tgl_deliver"   : item.tgl_deliver,
                "delivery_time" : item.delivery_time,
                "waybill_number": item.waybill_number,
                "numb_sample"   : item.numb_sample,
                "sample_id"     : item.sample_id,
                "mral_order"    : item.mral_order,
                "roa_order"     : item.roa_order,
                "job_mral"      : item.job_number_mral,
                "release_mral"  : item.release_mral.strftime("%Y-%m-%d %H:%M:%S") if item.release_mral else None,
                "day_mral"      : item.day_mral,
                "time_mral"     : item.time_mral,
                "job_roa"       : item.job_number_roa,
                "release_roa"   : item.release_roa.strftime("%Y-%m-%d %H:%M:%S") if item.release_roa else None,
                # "release_roa"   : item.release_roa.strftime("%Y-%m-%d %H:%M:%S"),
                "day_roa"       : item.day_roa,
                "time_roa"      : item.time_roa

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




