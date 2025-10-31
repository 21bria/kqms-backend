from django.shortcuts import render
from datetime import datetime

def sale_analysis_page(request):
    return render(request, 'admin-selling/data-home.html')

def monitoringSamplePage(request):
    today = datetime.today()
    first_day_of_month = today.replace(day=1)  # Tanggal awal bulan berjalan

    context = {
        'start_date'  : first_day_of_month.strftime('%Y-%m-%d'),
        'end_date'    : today.strftime('%Y-%m-%d'),
    }
    return render(request, 'admin-selling/split/list-monitoring.html',context)

def monitoringChartPage(request):
    today = datetime.today()
    first_day_of_month = today.replace(day=1)  # Tanggal awal bulan berjalan

    context = {
        'start_date'  : first_day_of_month.strftime('%Y-%m-%d'),
        'end_date'    : today.strftime('%Y-%m-%d'),
    }
    return render(request, 'admin-selling/split/chart-monitoring.html',context)