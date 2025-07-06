from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection
from datetime import datetime
import calendar
from django.utils.timezone import now, timedelta



# @login_required
def geology_home(request):
    # total_employees = count_total_employees()
    # total_male = count_male_employees()
    # total_female = count_female_employees()
    # total_department = count_department()

    context = {
        # 'total_employees': total_employees,
        # 'total_male': total_male,
        # 'total_female': total_female,
        # 'total_department': total_department,
    }
    return render(request, 'dashboard/geology.html', context)
