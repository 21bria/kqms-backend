from django_celery_beat.models import PeriodicTask, CrontabSchedule
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@method_decorator(csrf_exempt, name='dispatch')
class PeriodicTaskListView(View):
    def post(self, request):
        return JsonResponse(self._datatables(request), safe=False)

    def _datatables(self, request):
        datatables = request.POST
        draw = int(datatables.get("draw", 1))
        start = int(datatables.get("start", 0))
        length = int(datatables.get("length", 10))
        search = datatables.get("search[value]", "")
        order_column = int(datatables.get("order[0][column]", 0))
        order_dir = datatables.get("order[0][dir]", "asc")

        # Kolom yang digunakan di tabel
        columns = ['name', 'task', 'enabled', 'last_run_at', 'interval', 'crontab']
        order_field = columns[order_column] if order_column < len(columns) else 'name'
        order_by = f"-{order_field}" if order_dir == 'desc' else order_field

        queryset = PeriodicTask.objects.all()

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(task__icontains=search)
            )

        records_total = PeriodicTask.objects.count()
        records_filtered = queryset.count()

        queryset = queryset.order_by(order_by)
        paginator = Paginator(queryset, length)

        try:
            page = paginator.page(start // length + 1)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)

        data = []
        for task in page.object_list:
            data.append({
                "id": task.id,
                "name": task.name,
                "task": task.task,
                "enabled": task.enabled,
                "last_run": task.last_run_at.isoformat() if task.last_run_at else None,
                "interval": str(task.interval) if task.interval else '',
                "crontab": str(task.crontab) if task.crontab else '',
            })

        return {
            "draw": draw,
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,
            "data": data,
        }

@csrf_exempt
def schedule_task(request):
    if request.method == "POST":
        data = json.loads(request.body)

        # Nama unik agar bisa dicari & diedit
        task_name = data.get("name", "Clean duplicate files")

        # Waktu schedule dari frontend atau default jam 2 pagi
        minute = data.get("minute", "0")
        hour = data.get("hour", "2")
        day_of_week = data.get("day_of_week", "*")
        day_of_month = data.get("day_of_month", "*")
        month_of_year = data.get("month_of_year", "*")

        # Cari atau buat crontab
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=minute,
            hour=hour,
            day_of_week=day_of_week,
            day_of_month=day_of_month,
            month_of_year=month_of_year,
        )

        # Cek jika task sudah ada → update jadwalnya
        task, created = PeriodicTask.objects.update_or_create(
            name=task_name,
            defaults={
                "crontab": schedule,
                "task": "kqms.task.cleanup.clean_temp_duplicates",
                "enabled": True,
            }
        )

        return JsonResponse({
            "message": "Task created" if created else "Task updated",
            "name": task.name,
            "schedule": f"{hour}:{minute} daily"
        })

    return JsonResponse({"error": "Invalid method"}, status=405)
