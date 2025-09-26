from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ...models.selling_barging import SellingBarging
from ...models.selling_details_barging_view import SellingDetailsBargingView
from django.db.models import Sum, Count
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.views import View
from openpyxl import Workbook
from openpyxl.styles import Font
from datetime import datetime
from openpyxl.utils import get_column_letter
from django.db.models import Case, When, Value, IntegerField

@login_required
def export_excel_page(request):
    today = datetime.today()
    first_day_of_month = today.replace(day=1)  # Tanggal awal bulan berjalan

    context = {
        'start_date' : first_day_of_month.strftime('%Y-%m-%d'),
        'end_date'   : today.strftime('%Y-%m-%d'),
    }
    return render(request, 'export/form-export.html',context)
