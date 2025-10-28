# 
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import json
from django.http import JsonResponse
from django.shortcuts import render

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
