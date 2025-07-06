# 
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ....models.assay_over_release import listOverMral
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import F, Func
from django.views import View


class TimestampDiff(Func):
    function = 'TIMESTAMPDIFF'
    template = "%(function)s(HOUR, %(expressions)s, NOW())"

@login_required
def mral_over_page(request):
    # Cek permission
    return render(request, 'admin-mgoqa/waybills/list-not-ontime-mral.html')
   

class mralOverData(View):

    def post(self, request):
        # Ambil semua data invoice yang valid
        data_waybill = self._datatables(request)
        return JsonResponse(data_waybill, safe=False)

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
        data = listOverMral.objects.all()

        if search:
            data = data.filter(
                Q(waybill_number__icontains=search) |
                Q(sample_id__icontains=search) 
            )
       

        # Filter berdasarkan parameter dari request
        startDate       = request.POST.get('startDate')
        endDate         = request.POST.get('endDate')
        typeFilter      = request.POST.get('typeFilter')
        waybill_number  = request.POST.get('waybill_number')


        if startDate and endDate:
            data = data.filter(tgl_sample__range=[startDate, endDate])

        if typeFilter:
            data = data.filter(type_sample=typeFilter)
          
        if waybill_number:
            data = data.filter(waybill_number=waybill_number)   

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
                "tgl_sample"    : item.tgl_sample,
                "sample_id"     : item.sample_id,
                "type_sample"   : item.type_sample,
                "sample_method" : item.sample_method,
                # "nama_material" : item.nama_material,
                "delivery"      : item.delivery,
                "waybill_number": item.waybill_number,
                "numb_sample"   : item.numb_sample,     
                "mral_order"    : item.mral_order,     
                "release_mral"  : item.release_mral,     
                "time_over"     : item.time_over,     
                "day_over"      : item.day_over,     
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

