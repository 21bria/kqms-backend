# 
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import json
from django.http import JsonResponse
from django.shortcuts import render

@login_required
def page_config(request):
    return render(request, 'config/data-home.html')

