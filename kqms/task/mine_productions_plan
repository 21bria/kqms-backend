import os
import uuid
import pandas as pd
from datetime import datetime
from celery import shared_task
from django.db import transaction
from django.conf import settings
from ..models.task_model import taskImports
from ..models.plan_productions import planProductions

@shared_task(name='kqms.task.import_plan_mine_productions.import_plan_mine_productions')
def import_plan_mine_productions(file_path, original_file_name):
    df = pd.read_excel(file_path)
    errors = []
    duplicates = []
    duplicate_rows = []
    list_objects = []
    successful_imports = 0
    duplicate_imports = 0
    duplicate_file_path = None

    #Konversi kolom ke datetime dengan format yang sesuai
    df['Date Plan'] = pd.to_datetime(df['Date Plan'], format='%Y-%m-%d', errors='coerce')

    # Ambil hanya tanggal (tanpa waktu)
    df['Date Plan'] = df['Date Plan'].dt.date

    # Mulai transaksi untuk memastikan rollback jika terjadi error
    try:
        with transaction.atomic():
            for index, row in df.iterrows():
                date_plan = row['Date Plan']
                category  = row['Category']
                sources   = row['Sources']
                vendors   = row['Vendors']
                Topsoil   = row['Top Soil']
                OB        = row['OB']
                LGLO      = row['LGLO']
                MGLO      = row['MGLO']
                HGLO      = row['HGLO']
                Waste     = row['Waste']
                MWS       = row['MWS']
                LGSO      = row['LGSO']
                MGSO      = row['MGSO']
                HGSO      = row['HGSO']
                Quarry    = row['Quarry']
                Ballast   = row['Ballast']
                Biomass   = row['Biomass']

                category = None if pd.isna(category) else category
                sources  = None if pd.isna(sources) else sources
                vendors  = None if pd.isna(vendors) else vendors

                # Gabungkan Refrensi Plan
                ref_plan = f"{date_plan}{category}{sources}{vendors}".replace(" ", "")

                 # Cek duplikat berdasarkan kriteria
                if planProductions.objects.filter(ref_plan=ref_plan).exists():
                    duplicates.append(f"Duplicate at row {index}: {date_plan}")
                    duplicate_imports += 1
                    continue

                try:
                    data = planProductions(
                        date_plan=date_plan,
                        category=category,
                        sources=sources,
                        vendors=vendors,
                        topsoil=Topsoil,
                        ob=OB,
                        lglo=LGLO,
                        mglo=MGLO,
                        hglo=HGLO,
                        waste=Waste,
                        mws=MWS,
                        lgso=LGSO,
                        mgso=MGSO,
                        hgso=HGSO,
                        quarry=Quarry,
                        ballast=Ballast,
                        biomass=Biomass,
                        ref_plan=ref_plan,
                        task_id=import_plan_mine_productions.request.id,
                    )

                    list_objects.append(data)
                    successful_imports += 1
                except Exception as e:
                    errors.append(f"Error at row {index}: {str(e)}")
                    continue
            
            # Menggunakan bulk_create untuk menyimpan objek dalam batch
            planProductions.objects.bulk_create(list_objects, batch_size=200)
    
    # Simpan file Excel untuk duplikat jika ada
        if duplicate_rows:
            dup_df = pd.DataFrame(duplicate_rows)
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
            task_id=import_plan_mine_productions.request.id,
            successful_imports=successful_imports,
            failed_imports=len(errors),
            duplicate_imports=duplicate_imports,
            errors="\n".join(errors) if errors else None,
            duplicates="\n".join(duplicates) if duplicates else None,
            file_name=original_file_name,
            destination ='Plan Mine Productions',
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