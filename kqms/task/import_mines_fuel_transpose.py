import os
import uuid
from datetime import time
import pandas as pd
from datetime import date
from celery import shared_task
from django.db import transaction
from ..models.task_model import taskImports
from ..models.mine_fuel_consumption import FuelConsumption

def safe_float(val):
    if pd.isna(val):
        return 0.0
    try:
        return float(str(val).replace(',', '').strip())
    except ValueError:
        return 0.0

@shared_task(bind=True, name='kqms.task.import_mines_fuel_transpose.import_mines_fuel_transpose')
def import_mines_fuel_transpose(self, file_path, original_file_name):
    errors = []
    duplicates = 0
    successful_imports = 0
    list_objects = []
    today = date.today()

    try:
        # 1. READ EXCEL (MULTI HEADER)
        df_raw = pd.read_excel(file_path, header=[0, 1])

        # 1a. FLATTEN COLUMNS
        df_raw.columns = [
            f"{str(c[0]).strip()}_{str(c[1]).strip()}" if str(c[1]).strip() else str(c[0]).strip()
            for c in df_raw.columns
        ]

        # 1b. DETEKSI KOLOM TANGGAL (fleksibel)
        date_col = None
        for col in df_raw.columns:
            if 'Tanggal' in col or 'Date' in col:
                date_col = col
                break

        if not date_col:
            raise ValueError("Kolom tanggal tidak ditemukan di Excel")

        df_raw = df_raw.rename(columns={date_col: 'Date'})
        df_raw['Date'] = pd.to_datetime(df_raw['Date'], errors='coerce').dt.date

        # 2. TRANSPOSE + MERGE SHIFT I & II
        rows = []
        for _, row in df_raw.iterrows():
            raw_date = row['Date']

            # Validasi tanggal
            if pd.isna(raw_date):
                errors.append("Tanggal kosong / invalid")
                continue
            if not isinstance(raw_date, date):
                errors.append(f"Format tanggal tidak valid: {raw_date}")
                continue
            if raw_date > today:
                errors.append(f"Tanggal {raw_date} melebihi hari ini ({today})")
                continue

            # Loop unit untuk merge _I dan _II
            for col in df_raw.columns:
                if col == 'Date':
                    continue
                if col.endswith('_I'):
                    unit = col[:-2].strip()
                    vol_i = safe_float(row.get(f"{unit}_I"))
                    vol_ii = safe_float(row.get(f"{unit}_II"))
                    volume = vol_i + vol_ii

                    if volume > 0:
                        rows.append({
                            'date': raw_date,
                            'unit': unit,
                            'volume': volume
                        })

        if not rows:
            raise ValueError("Tidak ada data valid untuk di-import")

        df = pd.DataFrame(rows)

        # 3. LOAD EXISTING DATA (ONCE)
        existing_keys = set(FuelConsumption.objects.values_list('date', 'unit', 'volume'))
        seen_keys = set()

        # 4. INSERT DATA (ATOMIC)
        with transaction.atomic():
            for _, row in df.iterrows():
                key = (row['date'], row['unit'], row['volume'])

                if key in seen_keys:
                    duplicates += 1
                    errors.append(f"Duplikat dalam file: {row['date']} - {row['unit']}")
                    continue

                if key in existing_keys:
                    duplicates += 1
                    errors.append(f"Data sudah ada di database: {row['date']} - {row['unit']}")
                    continue

                seen_keys.add(key)
                list_objects.append(
                    FuelConsumption(
                        date=row['date'],
                        shift='All',  # hasil merge I + II
                        unit=row['unit'],
                        drivers=None,
                        charging_time=time(0, 0),  # default 00:00
                        hours_metre=None,
                        volume=row['volume'],
                        storage='SOLAR',
                        operator=None,
                        remark='Import Excel Fuel'
                    )
                )
                successful_imports += 1

            if list_objects:
                FuelConsumption.objects.bulk_create(list_objects, batch_size=200)

    except Exception as e:
        errors.append(str(e))
        successful_imports = 0

    # 5. LOG TASK
    taskImports.objects.create(
        task_id=self.request.id,
        successful_imports=successful_imports,
        failed_imports=len(errors),
        duplicate_imports=duplicates,
        errors="\n".join(errors) if errors else None,
        duplicates=None,
        file_name=original_file_name,
        destination='Fuel Consumption'
    )

    # 6. RESPONSE
    return {
        'message': 'Import Fuel Consumption selesai' if not errors else 'Import dibatalkan',
        'successful_imports': successful_imports,
        'errors': errors
    }
