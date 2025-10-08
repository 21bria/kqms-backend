from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection
from datetime import datetime
import calendar
from django.utils.timezone import now, timedelta



# @login_required
def geology_home(request):
    context = {
    }
    return render(request, 'dashboard/geology.html', context)
