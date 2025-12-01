# 
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from datetime import datetime

@login_required
def remove_page(request):
    return render(request, 'remove/data-home.html')

@login_required
def remove_waybills_page(request):
    return render(request, 'remove/data-waybills.html')

@login_required
def remove_mral_page(request):
    return render(request, 'remove/data-mral.html')

@login_required
def remove_roa_page(request):
    return render(request, 'remove/data-roa.html')

@login_required
def remove_barging_page(request):
    return render(request, 'remove/data-barging.html')

@login_required
def remove_selling_temp_page(request):
    today = datetime.today()
    first_day_of_month = today.replace(day=1) 
    context = {
        'start_date' : first_day_of_month.strftime('%Y-%m-%d'),
        'end_date'   : today.strftime('%Y-%m-%d'),
    }
    return render(request, 'remove/data-barging-temp.html',context)

@login_required
def remove_gc_bulk_page(request):
    today = datetime.today()
    first_day_of_month = today.replace(day=1) 
    context = {
        'start_date' : first_day_of_month.strftime('%Y-%m-%d'),
        'end_date'   : today.strftime('%Y-%m-%d'),
    }
    return render(request, 'remove/data-gc.html',context)

@login_required
def remove_mine_bulk_page(request):
    today = datetime.today()
    first_day_of_month = today.replace(day=1) 
    context = {
        'start_date' : first_day_of_month.strftime('%Y-%m-%d'),
        'end_date'   : today.strftime('%Y-%m-%d'),
    }
    return render(request, 'remove/remove-mine.html',context)

@login_required
def batch_double_page(request):
    return render(request, 'remove/list-double-batch.html')
