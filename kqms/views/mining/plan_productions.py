from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ...models.plan_productions import planProductions
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404
from django.db.models import Count, Sum
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
from django.http import HttpResponse
from django.views import View
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter


def format_angka(jumlah):
    if jumlah >= 1_000_000_000:
        return f"{jumlah / 1_000_000_000:.2f} B"
    elif jumlah >= 1_000_000:
        return f"{jumlah / 1_000_000:.2f} M"
    elif jumlah >= 1_000:
        return f"{jumlah / 1_000:.2f} K"
    else:
        return str(jumlah)

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
def plan_mine_production_page(request):
    return render(request, 'admin-mine/list-plan-productions.html')