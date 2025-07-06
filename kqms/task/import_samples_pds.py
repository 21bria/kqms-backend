import os
import uuid
import pandas as pd
from datetime import datetime
from celery import shared_task
from django.db import transaction
from django.conf import settings
import re
from datetime import datetime
from django.db import transaction
from ..models.task_model import taskImports
from ..models.sample_production import SampleProductions
from ..models.materials import Material
from ..models.sample_type import SampleType
from ..models.sample_method import SampleMethod
from ..models.source_model import SourceMinesDumping,SourceMinesDome

@shared_task(name='kqms.task.import_samples_pds.import_sample_GcQa')
def import_sample_GcQa(file_path, original_file_name):
    df = pd.read_excel(file_path)
    errors = []
    duplicates = []
    duplicate_rows = []
    list_objects = []
    successful_imports = 0
    duplicate_imports = 0
    duplicate_file_path = None

    # Konversi kolom ke datetime dengan format yang sesuai
    df['Date_Sample'] = pd.to_datetime(df['Date_Sample'], format='%Y-%m-%d', errors='coerce')
    # df['To_ITS']      = df['To_ITS'].dt.strftime('%H:%M:%S')

   
    # Buat dictionary dari Tabel untuk pencarian ID berdasarkan nama
    material_dict   = dict(Material.objects.values_list('nama_material', 'id'))
    stockpile_dict  = dict(SourceMinesDumping.objects.values_list('dumping_point', 'id'))
    dome_dict       = dict(SourceMinesDome.objects.values_list('pile_id', 'id'))
    method_dict     = dict(SampleMethod.objects.values_list('sample_method', 'id'))
    type_dict       = dict(SampleType.objects.values_list('type_sample', 'id'))
   

    # Mulai transaksi untuk memastikan rollback jika terjadi error
    try:
        with transaction.atomic():
            for index, row in df.iterrows():
                date_pds        = row['Date_Sample']
                shift           = row['Shift']
                sample_type     = row['Sample_Type']
                sample_method   = row['Sampling_Method']
                nama_material   = row['Material_Type']
                stockpile       = row['Sampling_Area']
                dome            = row['Sampling_Point']
                rl_from         = row['From']
                rl_to           = row['To']
                batch           = row['Batch_Code']
                increments      = row['Increments']
                fraction        = row['Fraction']
                size            = row['Size']
                sample_weight   = row['Sample_Weight(Kg)']
                sample_number   = row['Sample_Number']
                remark          = row['Remark']
                primer_raw      = row['Primer_Raw(Kg)']
                duplicate_raw   = row['Duplicat_Raw(Kg)']
                to_its          = row['To_ITS']
                sampling_deskripsi = row['Sampling_Desc']

                # Berikan nilai default untuk NaN (misalnya None atau 0)
                increments = 0 if pd.isna(increments) else increments
                sample_weight = 0 if pd.isna(sample_weight) else sample_weight
                primer_raw = 0 if pd.isna(primer_raw) else primer_raw
                duplicate_raw = 0 if pd.isna(duplicate_raw) else duplicate_raw
                rl_from = None if pd.isna(rl_from) else rl_from
                rl_to = None if pd.isna(rl_to) else rl_to
                batch = None if pd.isna(batch) else batch
                remark = None if pd.isna(remark) else remark
                sampling_deskripsi = None if pd.isna(sampling_deskripsi) else sampling_deskripsi

                
                # Cari ID dari Model berdasarkan nama
                id_type         = type_dict.get(sample_type, None)  
                id_method       = method_dict.get(sample_method, None)  
                id_material     = material_dict.get(nama_material, None) 
                sampling_point  = dome_dict.get(dome, None) 
                sampling_area   = stockpile_dict.get(stockpile, None)  

                # Hilangkan awalan "TS_" atau "GRB_" pada sample_method
                truck = re.sub(r'^(TS_|GRB_)', '', sample_method)
               

                # Menentukan nilai sample_type berdasarkan type
                if sample_type == 'PDS':
                    # Gabungkan Kode Batch
                    # kode_batch   = 'PDS' + str(id_material) + truck + str(sampling_area) + str(sampling_point) + batch
                    kode_batch = f"PDS{str(id_material or '')}{truck or ''}{sampling_area or ''}{sampling_point or ''}{batch or ''}"
                    type = 'PDS'
                else:
                    kode_batch = None  # Atau bisa set default value lainnya
                    type = ''

                if date_pds:  # Pastikan tanggal bukan None
                    date_str  = date_pds.strftime('%Y-%m-%d')
                    date_obj  = datetime.strptime(date_str, '%Y-%m-%d')
                    left_date = date_obj.day
                else:
                    left_date = None

                if pd.isna(to_its):
                    to_its = None   

                # Cek duplikat hanya jika sample_type = 'PDS'
                # if sample_type == 'PDS' and SampleProductions.objects.filter(kode_batch=kode_batch).exists():
                #     duplicates.append(f"Duplicate at row {index}: {sample_number}")
                #     duplicate_imports += 1
                #     continue

                if SampleProductions.objects.filter(sample_number=sample_number).exists():
                    duplicates.append(f"Duplicate at row {index}: {sample_number}")
                    duplicate_rows.append(row.to_dict())  # ⬅️ INI WAJIB
                    duplicate_imports += 1
                    continue

                try:
                    data = SampleProductions(
                        tgl_sample=date_pds,
                        shift=shift,
                        id_type_sample=id_method,
                        id_method=id_type,
                        id_material=id_material,
                        sampling_area=sampling_area,
                        sampling_point=sampling_point,
                        from_rl =rl_from,
                        to_rl=rl_to,
                        batch_code=batch,
                        increments=increments,
                        fraction=fraction,
                        size=size,
                        sample_weight=sample_weight,
                        sample_number=sample_number,
                        remark=remark,
                        primer_raw=primer_raw,
                        duplicate_raw=duplicate_raw,
                        to_its=to_its,
                        unit_truck=truck,
                        type=type,
                        kode_batch=kode_batch,
                        sampling_deskripsi=sampling_deskripsi,
                        left_date=left_date,
                    )
                    list_objects.append(data)
                    successful_imports += 1
                except Exception as e:
                    errors.append(f"Error at row {index}: {str(e)}")
                    continue
            
            # Menggunakan bulk_create untuk menyimpan objek dalam batch
            SampleProductions.objects.bulk_create(list_objects, batch_size=1000)
    
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
            task_id=import_sample_GcQa.request.id,
            successful_imports=successful_imports,
            failed_imports=len(errors),
            duplicate_imports=duplicate_imports,
            errors="\n".join(errors) if errors else None,
            duplicates="\n".join(duplicates) if duplicates else None,
            file_name=original_file_name,
            destination ='Samples Productions',
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

