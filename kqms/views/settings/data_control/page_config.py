# 
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from ....utils.utils import generate_dome_merger
from ....utils.utils import generate_stockpile_merger

@login_required
def page_config(request):
    return render(request, 'config/data-home.html')

@login_required
def OreClass_page(request):
    return render(request, 'master/list-ore-class.html')

@login_required
def ore_adjustment_page(request):
    return render(request, 'config/list-ore-adjust.html')

@login_required
def ore_factors_page(request):
    return render(request, 'master/list-truck-factor.html')

@login_required
def dome_merge_page(request):
    dome_merger = generate_dome_merger()
    context = {
        'dome_merger': dome_merger,

    }
    return render(request, 'config/list-merge-dome.html',context)

@login_required
def dome_adjustment_page(request):
    return render(request, 'config/dome-adjustment.html')

@login_required
def dome_close_page(request):
    return render(request, 'config/list-close-dome.html')

@login_required
def dome_finish_page(request):
    return render(request, 'config/list-finish-dome.html')

@login_required
def stockpile_merge_page(request):
    stockpile_merger = generate_stockpile_merger()
    context = {
        'stockpile_merger': stockpile_merger,
    }
    return render(request, 'config/list-merge-stockpile.html',context)

@login_required
def barging_finish_page(request):
    return render(request, 'admin-selling/entry/list-finish-barging.html')

