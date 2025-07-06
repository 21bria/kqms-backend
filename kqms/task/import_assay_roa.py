import os
import uuid
import pandas as pd
from celery import shared_task
from django.conf import settings
import re
from ..models.assay_roa_model import AssayRoa
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
    

@shared_task(name='kqms.task.import_assay_roa.import_assay_roa')
def import_assay_roa(file_path, original_file_name):
    df = pd.read_excel(file_path)
    errors = []
    duplicates = []
    duplicate_rows = []
    list_objects = []
    successful_imports = 0
    duplicate_imports = 0
    duplicate_file_path = None

    # Format 'Release Date' dan 'Release Time'
    df['release_date'] = pd.to_datetime(df['release_date']).dt.date
    df['release_time'] = pd.to_datetime(df['release_time'], format='%H:%M:%S').dt.time

    # Gabungkan kolom Release Date dan Release Time menjadi datetime tanpa timezone
    # df['release_roa'] = df.apply(lambda row: datetime.combine(row['release_date'], row['release_time']), axis=1)
    df['release_roa'] = df.apply(lambda row: timezone.make_aware(datetime.combine(row['release_date'], row['release_time'])), axis=1)
    # df['release_roa'] = df['release_roa'].apply(lambda x: x.replace(tzinfo=None))

    # Bersihkan semua kolom numerik di DataFrame
    numeric_columns = [
        'ni', 'co', 'al2o3', 'cao', 'cr2o3', 'fe2o3', 'fe', 'k2o', 'mgo', 'mno', 'na2o',
        'p2o5', 'p', 'sio2', 'tio2', 's', 'cu', 'zn', 'ci', 'so3', 'loi','total',
        'wt_wet', 'wt_dry', 'mc', 'p75um', '5mm','problem'
    ]


    for col in numeric_columns:
        df[col] = df[col].apply(clean_numeric)

    try:
        with transaction.atomic():
            for index, row in df.iterrows():
                release_date = row['release_date']
                release_time = row['release_time']
                release_roa  = row['release_roa']
                job_number   = row['job_number']
                sample_id    = row['sample_id']

                # Ambil data numerik yang telah dibersihkan
                release_date = row['release_date']
                release_time = row['release_time']
                release_roa  = row['release_roa']
                job_number   = row['job_number']
                sample_id    = row['sample_id']
                ni           = row.get('ni', 0)  # Gantikan dengan 0 jika kolom tidak ada
                co           = row.get('co', 0)
                al2o3        = row.get('al2o3', 0)
                cao          = row.get('cao', 0)
                cr2o3        = row.get('cr2o3', 0)
                fe2o3        = row.get('fe2o3', 0)
                fe           = row.get('fe', 0)
                k2o          = row.get('k2o', 0)
                mgo          = row.get('mgo', 0)
                mno          = row.get('mno', 0)
                na2o         = row.get('na2o', 0)
                p2o5         = row.get('p2o5', 0)
                p            = row.get('p', 0)
                sio2         = row.get('sio2', 0)
                tio2         = row.get('tio2', 0)
                s            = row.get('s', 0)
                cu           = row.get('cu', 0)
                zn           = row.get('zn', 0)
                ci           = row.get('ci', 0)
                so3          = row.get('so3', 0)
                loi          = row.get('loi', 0)
                total        = row['total']
                wt_wet       = row.get('wt_wet', 0)
                wt_dry       = row.get('wt_dry', 0)
                mc           = row.get('mc', 0)
                p75um        = row.get('p75um', 0)
                _5mm         = row.get('5mm', 0)
                problem      = row['problem']

                # Cek duplikat berdasarkan sample_id
                if AssayRoa.objects.filter(sample_id=sample_id).exists():
                    duplicates.append(f"Duplicate at row {index}: {sample_id}")
                    duplicate_rows.append(row.to_dict())  # ⬅️ INI WAJIB
                    duplicate_imports += 1
                    continue

                try:
                    data = AssayRoa(
                        release_date=release_date ,
                        release_time=release_time,
                        release_roa=release_roa,
                        job_number=job_number,
                        sample_id=sample_id,
                        ni=ni,
                        co=co,
                        al2o3=al2o3,
                        cao=cao,
                        cr2o3=cr2o3,
                        fe2o3=fe2o3,
                        fe=fe,
                        k2o=k2o,
                        mgo=mgo,
                        mno=mno,
                        na2o=na2o,
                        p2o5=p2o5,
                        p=p,
                        sio2=sio2,
                        tio2=tio2,
                        s=s,
                        cu=cu,
                        zn=zn,
                        ci=ci,
                        so3=so3,
                        loi=loi,
                        total=total,
                        wt_wet=wt_wet,
                        wt_dry=wt_dry,
                        mc=mc,
                        p75um=p75um,
                        _5mm=_5mm,
                        problem=problem,
                    )
                    list_objects.append(data)
                    successful_imports += 1
                except Exception as e:
                    errors.append(f"Error at row {index}: {str(e)}")
                    continue

        # Simpan batch data
        AssayRoa.objects.bulk_create(list_objects, batch_size=200)

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
            task_id=import_assay_roa.request.id,
            successful_imports=successful_imports,
            failed_imports=len(errors),
            duplicate_imports=duplicate_imports,
            errors="\n".join(errors) if errors else None,
            duplicates="\n".join(duplicates) if duplicates else None,
            file_name=original_file_name,
            destination ='Assay Roa',
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


