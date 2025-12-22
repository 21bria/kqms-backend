import os
import uuid
import pandas as pd
from datetime import date
from celery import shared_task
from django.db import transaction
from ..models.task_model import taskImports
from ..models.mine_fuel_consumption import FuelConsumption


@shared_task(name='kqms.task.import_mines_fuel_consumption.import_mines_fuel_consumption')
def import_mines_fuel_consumption(file_path, original_file_name):

    df = pd.read_excel(file_path)

    errors = []
    duplicates = []
    list_objects = []

    successful_imports = 0
    duplicate_imports = 0

    today = date.today()

    # =====================================================
    # NORMALISASI DATA
    # =====================================================
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
    df['Time'] = pd.to_datetime(df['Time'], format='%H:%M:%S').dt.time

    df['Shift'] = df['Shift'].astype(str).str.strip()
    df['Unit Code'] = df['Unit Code'].astype(str).str.strip()
    df['Hours Metre'] = df['Hours Metre'].astype(str).str.strip()
    df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce').fillna(0)
    
    # =====================================================
    # AMBIL DATA EXISTING (SEKALI SAJA)
    # =====================================================
    existing_keys = set(
        FuelConsumption.objects.values_list(
            'date', 'shift', 'unit',
            'hours_metre', 'charging_time', 'volume'
        )
    )

    seen_keys = set()

    try:
        with transaction.atomic():

            # =====================================================
            # PRE-CHECK TANGGAL (BATALKAN SEMUA JIKA SALAH)
            # =====================================================

            for excel_row, row in enumerate(df.itertuples(index=False), start=2):

                raw_date = row.Date

                #  Tanggal kosong / NaT
                if pd.isna(raw_date):
                    raise ValueError(
                        f"❌ Import dibatalkan: Baris {excel_row} "
                        f"tanggal kosong / tidak valid"
                    )

                # Pastikan bertipe date (bukan string / Timestamp / dll)
                if not isinstance(raw_date, date):
                    raise ValueError(
                        f"❌ Import dibatalkan: Baris {excel_row} "
                        f"format tanggal tidak valid ({raw_date})"
                    )

                # Tanggal melebihi hari ini
                if raw_date > today:
                    raise ValueError(
                        f"❌ Import dibatalkan: Baris {excel_row} "
                        f"memiliki tanggal ({raw_date}) "
                        f"melebihi hari ini ({today})"
                    )


            # PROSES DATA (SETELAH LOLOS PRE-CHECK)
            # =====================================================
            for excel_row, (_, row) in enumerate(df.iterrows(), start=2):

                key = (
                    row['Date'],
                    row['Shift'],
                    row['Unit Code'],
                    row['Hours Metre'],
                    row['Time'],
                    row['Volume'],
                )

                #  Duplikat dalam file
                if key in seen_keys:
                    duplicate_imports += 1
                    raise ValueError(
                        f"❌ Import dibatalkan: Duplikat dalam file "
                        f"pada baris {excel_row}"
                    )

                #  Duplikat di database
                if key in existing_keys:
                    duplicate_imports += 1
                    raise ValueError(
                        f"❌ Import dibatalkan: Data sudah ada di database "
                        f"pada baris {excel_row}"
                    )

                seen_keys.add(key)

                list_objects.append(
                    FuelConsumption(
                        date=row['Date'],
                        shift=row['Shift'],
                        unit=row['Unit Code'],
                        drivers=row['Drivers'],
                        charging_time=row['Time'],
                        hours_metre=row['Hours Metre'],
                        volume=row['Volume'],
                        storage=row['Storage'],
                        operator=row['Fuelman'],
                        remark=row['Description'],
                    )
                )

                successful_imports += 1

            # =====================================================
            # SIMPAN JIKA SEMUA DATA AMAN
            # =====================================================
            FuelConsumption.objects.bulk_create(list_objects, batch_size=200)

    except Exception as e:
        errors.append(str(e))
        successful_imports = 0

    # =====================================================
    #  LOGGING TASK
    # =====================================================
    taskImports.objects.create(
        task_id=import_mines_fuel_consumption.request.id,
        successful_imports=successful_imports if not errors else 0,
        failed_imports=len(errors),
        duplicate_imports=duplicate_imports,
        errors="\n".join(errors) if errors else None,
        duplicates=None,
        file_name=original_file_name,
        destination='Fuel Consumption',
    )

    # =====================================================
    # RESPONSE
    # =====================================================
    if errors:
        return {
            'message': '❌ Import dibatalkan karena kesalahan data',
            'errors': errors
        }

    return {
        'message': '✅ Import Fuel Consumption berhasil',
        'successful_imports': successful_imports
    }
