# core/celery.py
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# SET ENV DJANGO_SETTINGS_MODULE
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Buat Celery instance
app = Celery('core')

# Load config dari Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover semua tasks.py
app.autodiscover_tasks()

# Baru di sini import task spesifik
# Karena semua Django app sudah di-load
import django
django.setup()  # ✅ WAJIB sebelum import model jika celery dijalankan mandiri

import kqms.task  # ⬅️ TEMPATKAN SETELAH django.setup()

# Set zona waktu
app.conf.timezone = settings.TIME_ZONE
app.conf.enable_utc = True

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# ✅ Tambahkan beat schedule di bagian bawah

app.conf.beat_schedule = {
    # Hapus file duplikat
    'clean-duplicate-files-daily': {
        'task': 'kqms.task.cleanup.clean_temp_duplicates',
        'schedule': crontab(hour=2, minute=0),
    },
    # Truncate taskImports setiap hari
    'truncate-task-imports-daily': {
        'task': 'kqms.task.cleanup.truncate_task_imports',
        'schedule': crontab(hour=2, minute=30),
        'args': (1,),  # umur data yang dihapus > 1 hari
    },
}