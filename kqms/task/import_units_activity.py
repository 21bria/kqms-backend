from celery import shared_task
import pandas as pd
from datetime import datetime, time
from django.utils import timezone
from django.db import transaction
import re
from kqms.models import HmUnit, HmUnitDetail, UnitStatus, UnitActivity, UnitLocation,importTask, MineUnits

def normalize_text(val):
    return re.sub(r'\s+', ' ', str(val)).strip()

def clean_text(val):
    if val is None:
        return ''
    return str(val).replace('\xa0', ' ').strip()

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

@shared_task(bind=True, name="kqms.task.import_units_activity.import_units_activity")
def import_units_activity(self, path: str, import_task_id: str):
    task = importTask.objects.get(id=import_task_id)
    inserted = 0
    skipped = 0
    errors = []

    try:
        task.status = 'PROCESSING'
        task.save(update_fields=['status'])

        df = pd.read_excel(path)
        task.total_rows = len(df)
        task.save(update_fields=['total_rows'])

        # ================= Preload master data =================
        units = {u.unit_code.strip(): u for u in MineUnits.objects.all()}
        statuses = {s.name.lower(): s for s in UnitStatus.objects.all()}
        locations = {l.name.lower(): l for l in UnitLocation.objects.all()}
        activities = {(a.name.lower(), a.status_id): a for a in UnitActivity.objects.all()}

        # Preload HmUnit
        existing_hm_units = {
            (h.unit_id, h.date, h.shift): h
            for h in HmUnit.objects.all()
        }
        hm_units_to_create = []

        to_create_details = []

        with transaction.atomic():
            for row_no, row in enumerate(df.itertuples(index=False), start=2):
                try:
                    # ================= UNIT =================
                    unit = units.get(str(row.unit_code).strip())
                    if not unit:
                        skipped += 1
                        errors.append({'row': row_no, 'error': f'Unit {row.unit_code} tidak ditemukan'})
                        continue

                    date = row.date
                    shift = str(row.shift).strip()

                    # ================= HM UNIT =================
                    key = (unit.id, date, shift)
                    hm_unit = existing_hm_units.get(key)
                    if not hm_unit:
                        hm_unit = HmUnit(
                            unit=unit,
                            date=date,
                            shift=shift,
                            hm_start=0,
                            hm_end=0,
                            status='DRAFT'
                        )
                        hm_units_to_create.append(hm_unit)
                        existing_hm_units[key] = hm_unit

                    # ================= MASTER DETAIL =================
                    status_name = clean_text(row.status).lower()
                    status = statuses.get(status_name)
                    if not status:
                        skipped += 1
                        errors.append({'row': row_no, 'error': f'Status "{row.status}" tidak ditemukan'})
                        continue

                    activity_name = clean_text(row.activity).lower()
                    activity = activities.get((activity_name, status.id))
                    if not activity:
                        skipped += 1
                        errors.append({
                            'row': row_no,
                            'error': f'Activity "{row.activity}" tidak sesuai dengan status "{status.name}"'
                        })
                        continue

                    location_name = clean_text(row.location).lower()
                    location = locations.get(location_name)
                    if not location:
                        skipped += 1
                        errors.append({'row': row_no, 'error': f'Location "{row.location}" tidak ditemukan'})
                        continue

                    # ================= TIME & DURATION =================
                    start_time = parse_excel_time(row.start_time)
                    end_time   = parse_excel_time(row.end_time)
                    duration   = calc_duration_min(start_time, end_time)
                    if duration <= 0:
                        skipped += 1
                        errors.append({'row': row_no, 'error': 'Durasi tidak valid'})
                        continue

                    # ================= CEK DUPLIKAT DETAIL =================
                    # untuk cek duplikat, bisa pakai dict atau query filter per hm_unit
                    exists = HmUnitDetail.objects.filter(
                        hm_unit=hm_unit,
                        start_time=start_time,
                        end_time=end_time
                    ).exists()
                    if exists:
                        skipped += 1
                        continue

                    # ================= PREPARE INSERT =================
                    to_create_details.append(HmUnitDetail(
                        hm_unit=hm_unit,
                        start_time=start_time,
                        end_time=end_time,
                        duration_min=duration,
                        status=status,
                        activity=activity,
                        location=location,
                        category=getattr(row, 'category', None),
                        remark=getattr(row, 'remark', '')
                    ))
                    inserted += 1

                except Exception as e:
                    skipped += 1
                    errors.append({'row': row_no, 'error': str(e)})

            # ================= BULK CREATE =================
            if hm_units_to_create:
                HmUnit.objects.bulk_create(hm_units_to_create)

            if to_create_details:
                HmUnitDetail.objects.bulk_create(to_create_details, batch_size=1000)

        # ================= UPDATE TASK =================
        task.task_id = import_units_activity.request.id
        task.status = 'SUCCESS'
        task.inserted = inserted
        task.skipped = skipped
        task.errors = errors
        task.finished_at = timezone.now()
        task.save()

    except Exception as fatal:
        task.status = 'FAILED'
        task.errors = [{'fatal': str(fatal)}]
        task.finished_at = timezone.now()
        task.save()
        raise
