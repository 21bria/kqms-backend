import os
import uuid
import pandas as pd
from datetime import datetime
from celery import shared_task
from django.db import transaction
from django.conf import settings
from datetime import datetime
from django.db import transaction
from ..models.task_model import taskImports
from ..models.sample_production import SampleProductions
from ..models.materials import Material
from ..models.sample_type import SampleType
from ..models.sample_method import SampleMethod
from ..models.selling_code import SellingCode

@shared_task(name='kqms.task.import_samples_selling.import_samples_selling')
def import_samples_selling(file_path, original_file_name):
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
    method_dict     = dict(SampleMethod.objects.values_list('sample_method', 'id'))
    type_dict       = dict(SampleType.objects.values_list('type_sample', 'id'))
    code_dict        = dict(SellingCode.objects.values_list('product_code', 'id'))
   

    # Mulai transaksi untuk memastikan rollback jika terjadi error
    try:
        with transaction.atomic():
            # 🔒 Proteksi agar tidak ada tanggal melebihi hari ini
            today = datetime.today().date()
            for idx, row in df.itertuples(index=True):
                date_pds = getattr(row, 'Date_Sample', None)
                if pd.notna(date_pds) and date_pds.date() > today:
                    raise ValueError(
                        f"❌ Import dibatalkan: Baris {idx+2} memiliki Date Sample ({date_pds.date()}) "
                        f"yang melebihi tanggal hari ini ({today})."
                    )
                
            for index, row in df.iterrows():
                date_sale       = row['Date_Sample']
                shift           = row['Shift']
                sample_type     = row['Sample_Type']
                sample_method   = row['Sampling_Method']
                nama_material   = row['Material_Type']
                code_product    = row['Code_Lot']
                batch           = row['Sub_Lot']
                increments      = row['Group']
                fraction        = None
                size            = None
                sample_number   = row['Sample_Number']
                sample_weight   = row['Sample_Weight(Kg)']
                primer_raw      = row['Primer_Raw(Kg)']
                duplicate_raw   = row['Duplicat_Raw(Kg)']
                to_its          = row['To_Lab']
                remark          = row['Remark']

                # Berikan nilai default untuk NaN (misalnya None atau 0)
                increments = 0 if pd.isna(increments) else increments
                sample_weight = 0 if pd.isna(sample_weight) else sample_weight
                primer_raw = 0 if pd.isna(primer_raw) else primer_raw
                duplicate_raw = 0 if pd.isna(duplicate_raw) else duplicate_raw
                batch   = None if pd.isna(batch) else batch
                remark = None if pd.isna(remark) else remark
                sampling_deskripsi = None 
                
                # Cari ID dari Model berdasarkan nama
                id_type      = type_dict.get(sample_type, None)  
                id_method    = method_dict.get(sample_method, None)  
                id_material  = material_dict.get(nama_material, None) 
                code_lot     = code_dict.get(code_product, None) 

                # Menentukan nilai sample_type berdasarkan type Jika sample_type adalah 'LIS' atau 'SAS'
                if sample_type in ['LIS', 'SAS']:
                    # Gabungkan Kode Batch untuk LIS dan SAS
                    kode_batch = f"{str(sample_type or '')}{str(id_material or '')}{str(code_product or '')}{batch or ''}"
                    pulp_batch = f"{str(sample_type or '')}{str(code_product or '')}{batch or ''}"
                    monitoring_batch = None
                    type = sample_type  # Menyimpan LIS atau SAS sesuai datanya
                else:
                    # Untuk selain LIS/SAS, gunakan format biasa
                    # kode_batch = f"{str(sample_type or '')}{str(id_material or '')}{str(code_product or '')}{batch or ''}{increments or ''}"
                    kode_batch = None
                    pulp_batch = None
                    monitoring_batch = f"{str(sample_type or '')}{str(id_material or '')}{str(code_product or '')}{batch or ''}{increments or ''}"
                    type = sample_type


                if date_sale:  # Pastikan tanggal bukan None
                    date_str  = date_sale.strftime('%Y-%m-%d')
                    date_obj  = datetime.strptime(date_str, '%Y-%m-%d')
                    left_date = date_obj.day
                else:
                    left_date = None

                if pd.isna(to_its):
                    to_its = None   

                # Cek duplikat hanya jika sample_number tidak kosong
                if SampleProductions.objects.filter(sample_number=sample_number).exists():
                    duplicates.append(f"Duplicate at row {index}: {sample_number}")
                    duplicate_rows.append(row.to_dict())  # INI WAJIB
                    duplicate_imports += 1
                    continue

                try:
                    data = SampleProductions(
                        tgl_sample=date_sale,
                        shift=shift,
                        id_type_sample=id_type,
                        id_method=id_method,
                        id_material=id_material,
                        product_code=code_lot,
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
                        unit_truck=sample_type,
                        type=type,
                        kode_batch=kode_batch,
                        selling_pulp=pulp_batch,
                        sale_monitoring=monitoring_batch,
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
            task_id=import_samples_selling.request.id,
            successful_imports=successful_imports,
            failed_imports=len(errors),
            duplicate_imports=duplicate_imports,
            errors="\n".join(errors) if errors else None,
            duplicates="\n".join(duplicates) if duplicates else None,
            file_name=original_file_name,
            destination ='Samples Selling',
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

