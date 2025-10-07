import os
import uuid
import pandas as pd
from celery import shared_task
from django.conf import settings
import re
from ..models.selling_plan_barging import SellingPlanBarging
from ..models.task_model import taskImports
from datetime import datetime
from django.utils import timezone
from django.db import transaction

# Fungsi untuk membersihkan data numerik
def clean_numeric(value):
    try:
        if pd.isna(value):  # Cek jika NaN atau None
            return 0
        if isinstance(value, str):
            value = value.strip()  # Menghapus spasi di awal dan akhir
            if value == '':  # Jika string kosong
                return None
            # Menghapus karakter selain angka dan titik desimal
            value = re.sub(r"[^0-9.<>]", "", value)
            if value.startswith('<') or value.startswith('>'):
                value = value[1:]  # Menghapus tanda '<' atau '>'
            if re.match(r"^\d+(\.\d+)?$", value):  # Cek jika angka valid
                return float(value)
            return 0  # Jika tidak valid, kembalikan 0
        return value if isinstance(value, (int, float)) else 0
    except Exception as e:
        print(f"Error processing value: {value}, Error: {e}")
        return 0  # Kembalikan 0 jika terjadi error
    

@shared_task(name='kqms.task.import_plan_barging.import_plan_barging')
def import_plan_barging(file_path, original_file_name):
    df = pd.read_excel(file_path)
    errors = []
    duplicates = []
    duplicate_rows = []
    list_objects = []
    successful_imports = 0
    duplicate_imports = 0
    duplicate_file_path = None

    # Format 'Plan Date' 
    df['Plan Date'] = pd.to_datetime(df['Plan Date']).dt.date

    # Bersihkan semua kolom numerik di DataFrame
    numeric_columns = [ 'Ni (%)', 'Co (%)', 'Fe (%)', 'SiO2 (%)', 'MgO (%)', 'Al2O3 (%)', 'SM (%)' ]


    for col in numeric_columns:
        df[col] = df[col].apply(clean_numeric)

    try:
        with transaction.atomic():
            for index, row in df.iterrows():
                plan_date   = row['Plan Date']
                type_ore    = row['Type Ore']
                # Ambil data numerik yang telah dibersihkan
                ni_plan      = row.get('Ni (%)', 0) 
                co_plan      = row.get('Co (%)', 0)
                fe_plan      = row.get('Fe (%)', 0)
                sio2_plan    = row.get('SiO2 (%)', 0)  
                mgo_plan     = row.get('MgO (%)', 0)
                al2o3_plan   = row.get('Al2O3 (%)', 0)
                sm_plan      = row.get('SM (%)', 0)
                tonnage_plan = row.get('Tonnage (WMT)', 0)

                 # Mapping  material ke type_selling
                if row['Type Ore'] == 'SAP':
                    type_selling  = 'SAS'
                elif row['Type Ore'] == 'LIM':
                    type_selling  = 'LIS'
                else:
                    type_selling = None

                # Cek duplikat berdasarkan sample_id
                if SellingPlanBarging.objects.filter(plan_date=plan_date,type_ore=type_ore).exists():
                    duplicates.append(f"Duplicate at row {index}: {plan_date} - {type_ore}")
                    duplicate_rows.append(row.to_dict())  # Ini_plan WAJIB
                    duplicate_imports += 1
                    continue

                try:
                    data = SellingPlanBarging(
                        plan_date=plan_date ,
                        type_ore=type_ore,
                        type_selling=type_selling,
                        tonnage_plan=tonnage_plan,
                        ni_plan=ni_plan,
                        co_plan=co_plan,
                        fe_plan=fe_plan,
                        sio2_plan=sio2_plan,
                        mgo_plan=mgo_plan,
                        al2o3_plan=al2o3_plan, 
                        sm_plan=sm_plan,
                        check_duplicated=f"{plan_date}-{type_ore}",
                    )
                    list_objects.append(data)
                    successful_imports += 1
                except Exception as e:
                    errors.append(f"Error at row {index}: {str(e)}")
                    continue

        # Simpan batch data
        SellingPlanBarging.objects.bulk_create(list_objects, batch_size=200)

     # Simpan file Excel untuk duplikat jika ada
        if duplicate_rows:
            dup_df = pd.DataFrame(duplicate_rows)
            # Hapus timezone dari semua kolom datetime (jika ada)
            for col in dup_df.select_dtypes(include=['datetimetz']).columns:
                dup_df[col] = dup_df[col].dt.tz_localize(None)
            filename = f"duplicates_{uuid.uuid4().hex}.xlsx"
            duplicate_dir = os.path.join(settings.MEDIA_ROOT, 'tmp_duplicates')
            os.makedirs(duplicate_dir, exist_ok=True)
            duplicate_file_path = os.path.join(duplicate_dir, filename)
            dup_df.to_excel(duplicate_file_path, index=False)
    
    except Exception as e:
        errors.append(f"Transaction failed: {str(e)}")

    # Buat laporan import
    try:
            taskImports.objects.create(
            task_id=import_plan_barging.request.id,
            successful_imports=successful_imports,
            failed_imports=len(errors),
            duplicate_imports=duplicate_imports,
            errors="\n".join(errors) if errors else None,
            duplicates="\n".join(duplicates) if duplicates else None,
            file_name=original_file_name,
            destination ='Plan Barging',
            duplicate_file_path=os.path.relpath(duplicate_file_path, settings.MEDIA_ROOT) if duplicate_file_path else None
        )

    except Exception as e:
        errors.append(f"Error while logging import task: {str(e)}")

    result = {
        'message': 'Import completed with some errors or duplicates' if errors or duplicates else 'Import successful',
        'successful_imports': successful_imports,
        'failed_imports': len(errors),
        'duplicate_imports': duplicate_imports,
        'errors': errors,
        'duplicates': duplicates,
    }

    if duplicate_file_path:
        # Kembalikan path relatif supaya bisa diakses frontend
        result['duplicate_file'] = os.path.relpath(duplicate_file_path, settings.MEDIA_ROOT)

    return result


