import os
from django.conf import settings
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from kqms.task.import_time_sheet import hm_timesheet_import_task
from kqms.task.import_units_activity import import_units_activity
from kqms.models import importTask
from celery.app.task import Task
from typing import cast
from django.utils.dateparse import parse_date
from django.shortcuts import render
from datetime import datetime
from django.contrib.auth.decorators import login_required


@login_required
def import_timesheet_page(request):
    today = datetime.today()
    context = {
        'day_date' : today.strftime('%Y-%m-%d'),
    }
    return render(request, 'admin-mine/list-timesheet-import.html', context)

def handle_uploaded_file(file):
    upload_dir = "tmp/hm_import"
    os.makedirs(
        os.path.join(settings.MEDIA_ROOT, upload_dir),
        exist_ok=True
    )

    file_path = default_storage.save(
        f"{upload_dir}/{file.name}",
        file
    )

    return os.path.join(settings.MEDIA_ROOT, file_path)

@require_POST
def import_hm_excel_view(request):
    file  = request.FILES.get("file")
    date  = request.POST.get("date")
    shift = request.POST.get("shift")

    if not file:
        return JsonResponse({"success": False, "message": "File wajib diisi"})
    if not date:
        return JsonResponse({"success": False, "message": "Date wajib diisi"})
    if not shift:
        return JsonResponse({"success": False, "message": "Shift wajib diisi"})

    path = handle_uploaded_file(file)


    import_task = importTask.objects.create(
        file_name=file.name,
        task_type='HM Timesheet Import',
        status='PENDING'
    )

    task = cast(Task, hm_timesheet_import_task)
    task.delay(path, date, shift, str(import_task.id))

    return JsonResponse({
        "success": True,
        "message": "Import sedang diproses ⏳ "
    })

def hm_timesheet_import_logs(request):
    date = request.GET.get("date")

    qs = importTask.objects.filter(
        task_type='HM Timesheet Import'
    ).order_by('-created_at')

    if date:
        qs = qs.filter(created_at__date=parse_date(date))

    data = []
    for task in qs:
        data.append({
            "id": str(task.id),
            "file_name": task.file_name,
            "status": task.status,
            "inserted": task.inserted,
            "skipped": task.skipped,
            "errors": task.errors or [],
            "created_at": task.created_at.strftime('%Y-%m-%d %H:%M'),
        })

    return JsonResponse(data, safe=False)


@login_required
def import_timesheet_range_page(request):
    today = datetime.today()
    context = {
        'day_date' : today.strftime('%Y-%m-%d'),
    }
    return render(request, 'admin-mine/list-timesheet-import-range.html', context)

@require_POST
def import_hm_excel_range(request):
    file  = request.FILES.get("file")

    if not file:
        return JsonResponse({"success": False, "message": "File wajib diisi"})

    path = handle_uploaded_file(file)


    import_task = importTask.objects.create(
        file_name=file.name,
        task_type='HM Timesheet Import Range',
        status='PENDING'
    )

    task = cast(Task, import_units_activity)
    task.delay(path, str(import_task.id))

    return JsonResponse({
        "success": True,
        "message": "Import sedang diproses ⏳ "
    })


def hm_timesheet_import_range_logs(request):
    date = request.GET.get("date")

    qs = importTask.objects.filter(
        task_type='HM Timesheet Import Range'
    ).order_by('-created_at')

    if date:
        qs = qs.filter(created_at__date=parse_date(date))

    data = []
    for task in qs:
        data.append({
            "id": str(task.id),
            "file_name": task.file_name,
            "status": task.status,
            "inserted": task.inserted,
            "skipped": task.skipped,
            "errors": task.errors or [],
            "created_at": task.created_at.strftime('%Y-%m-%d %H:%M'),
        })

    return JsonResponse(data, safe=False)

