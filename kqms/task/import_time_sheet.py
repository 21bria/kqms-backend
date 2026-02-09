from celery import shared_task
import pandas as pd
from datetime import datetime, time
from django.utils import timezone
from django.db import transaction
from kqms.models import HmUnit, HmUnitDetail, UnitStatus, UnitActivity, UnitLocation,importTask

def parse_excel_time(value):
    if value is None or value == "":
        return None

    # Kalau sudah datetime / time (Excel sering begini)
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, time):
        return value

    value = str(value).strip()

    # Coba beberapa format
    for fmt in ("%H:%M:%S", "%H:%M", "%H.%M.%S", "%H.%M"):
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue

    raise ValueError(f"Format jam tidak dikenali: {value}")

def calc_duration_min(start_time, end_time):
    start = datetime.combine(datetime.today(), start_time)
    end   = datetime.combine(datetime.today(), end_time)

    diff = (end - start).total_seconds() / 60
    if diff < 0:
        diff += 1440  # lewat tengah malam

    return int(diff)

@shared_task(bind=True, name="kqms.task.import_time_sheet.hm_timesheet_import_task")
def hm_timesheet_import_task(self, path: str, date: str, shift: str, import_task_id: str):
    task = importTask.objects.get(id=import_task_id)

    inserted = 0
    skipped = 0
    errors = []

    try:
        # 🔄 set PROCESSING
        task.status = 'PROCESSING'
        task.save(update_fields=['status'])

        df = pd.read_excel(path)
        task.total_rows = len(df)
        task.save(update_fields=['total_rows'])

        with transaction.atomic():
            for row_no, row in enumerate(df.itertuples(index=False), start=2):
                try:
                    unit_code = str(row.unit_code).strip()

                    hm_unit = HmUnit.objects.filter(
                        unit__unit_code=unit_code,
                        date=date,
                        shift=shift
                    ).first()
                    if not hm_unit:
                        raise ValueError(f'Unit {unit_code} belum di-append')

                    status = UnitStatus.objects.filter(name=row.status).first()
                    if not status:
                        raise ValueError(f'Status "{row.status}" tidak ditemukan')

                    activity = UnitActivity.objects.filter(
                        name=row.activity,
                        status=status
                    ).first()
                    if not activity:
                        raise ValueError(f'Activity "{row.activity}" tidak sesuai status {status.name}')

                    location = UnitLocation.objects.filter(name=row.location).first()
                    if not location:
                        raise ValueError(f'Location "{row.location}" tidak ditemukan')

                    start_time = parse_excel_time(row.start_time)
                    end_time   = parse_excel_time(row.end_time)
                    duration   = calc_duration_min(row.start_time, row.end_time)

                    if duration <= 0:
                        raise ValueError('Durasi tidak valid')

                    # CEK DUPLIKAT SEBELUM CREATE
                    exists = HmUnitDetail.objects.filter(
                        hm_unit=hm_unit,
                        start_time=start_time,
                        end_time=end_time,
                        # status=status,
                        # activity=activity,
                        # location=location
                    ).exists()

                    if exists:
                        skipped += 1
                    else:
                        HmUnitDetail.objects.create(
                            hm_unit=hm_unit,
                            start_time=start_time,
                            end_time=end_time,
                            duration_min=duration,
                            status=status,
                            activity=activity,
                            location=location,
                            category=getattr(row, 'category', None)
                        )
                        inserted += 1

                except Exception as e:
                    skipped += 1
                    errors.append({
                        'row': row_no,
                        'error': str(e)
                    })

        # selesai normal (meskipun ada skipped)
        task.task_id = hm_timesheet_import_task.request.id
        task.status = 'SUCCESS'
        task.inserted = inserted
        task.skipped = skipped
        task.errors = errors
        task.finished_at = timezone.now()
        task.save()

    except Exception as fatal:
        # error besar (file rusak, dll)
        task.status = 'FAILED'
        task.errors = [{'fatal': str(fatal)}]
        task.finished_at = timezone.now()
        task.save()
        raise
