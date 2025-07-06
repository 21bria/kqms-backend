from celery import shared_task
import os, time
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from kqms.models import taskImports

@shared_task(name='kqms.task.cleanup.clean_temp_duplicates')
def clean_temp_duplicates():
    print("[TASK] Running cleanup of old duplicate files")
    temp_dir = os.path.join(settings.MEDIA_ROOT, 'tmp_duplicates')
    now = time.time()

    if not os.path.exists(temp_dir):
        print("Directory not found:", temp_dir)
        return

    for file in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, file)
        if os.path.isfile(file_path):
            last_modified = os.path.getmtime(file_path)
            if now - last_modified > 86400:  # lebih dari 1 hari
                os.remove(file_path)
                print(f"[Deleted] {file_path}")

@shared_task(name='kqms.task.cleanup.truncate_task_imports')
def truncate_old_task_imports(days=1):
    threshold = timezone.now() - timedelta(days=days)
    deleted, _ = taskImports.objects.filter(created_at__lt=threshold).delete()
    return f"{deleted} taskImports records deleted older than {days} days."