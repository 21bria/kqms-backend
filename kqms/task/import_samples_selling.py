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

    # =========================
    # NORMALIZE KOLOM EXCEL
    # =========================
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace(' ', '_', regex=False)
        .str.replace(r'[^A-Za-z0-9_]', '', regex=True)
    )

    # =========================
    # VALIDASI KOLOM WAJIB
    # =========================
    required_columns = [
        'Date_Sample',
        'Shift',
        'Sample_Type',
        'Sampling_Method',
        'Material_Type',
        'Batch_Code',
        'Increments',
        'Sample_Number',
        'Sample_WeightKg',
        'Primer_RawKg',
        'Duplicat_RawKg',
        'To_ITS',
    ]

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(
            f"Kolom tidak ditemukan: {missing}\n"
            f"Kolom tersedia: {df.columns.tolist()}"
        )

    # =========================
    # PREPROCESS
    # =========================
    df['Date_Sample'] = pd.to_datetime(df['Date_Sample'], errors='coerce')

    errors = []
    duplicates = []
    duplicate_rows = []
    list_objects = []
    successful_imports = 0
    duplicate_imports = 0
    duplicate_file_path = None

    # =========================
    # MASTER LOOKUP
    # =========================
    material_dict = dict(Material.objects.values_list('nama_material', 'id'))
    method_dict   = dict(SampleMethod.objects.values_list('sample_method', 'id'))
    type_dict     = dict(SampleType.objects.values_list('type_sample', 'id'))
    code_dict     = dict(SellingCode.objects.values_list('product_code', 'id'))

    try:
        with transaction.atomic():

            # =========================
            # VALIDASI TANGGAL
            # =========================
            today = datetime.today().date()
            for i, row in enumerate(df.itertuples(index=False), start=2):
                tanggal = getattr(row, 'Date_Sample')
                if pd.notna(tanggal) and tanggal.date() > today:
                    raise ValueError(
                        f"Baris {i}: Date Sample {tanggal.date()} > hari ini ({today})"
                    )

            # =========================
            # LOOP DATA
            # =========================
            for index, row in df.iterrows():
                try:
                    date_sale       = row.get('Date_Sample')
                    shift           = row.get('Shift')
                    sample_type     = row.get('Sample_Type')
                    sample_method   = row.get('Sampling_Method')
                    nama_material   = row.get('Material_Type')

                    batch_code      = row.get('Batch_Code')
                    increments      = row.get('Increments')
                    fraction        = row.get('Fraction')
                    size            = row.get('Size')
                    sample_number   = row.get('Sample_Number')
                    sample_weight   = row.get('Sample_WeightKg')
                    primer_raw      = row.get('Primer_RawKg')
                    duplicate_raw   = row.get('Duplicat_RawKg')
                    to_its          = row.get('To_ITS')
                    remark          = row.get('Remark')
                    sampling_desc   = row.get('Sampling_Desc')

                    batch_code = None if pd.isna(batch_code) else batch_code
                    increments = 0 if pd.isna(increments) else increments
                    fraction = None if pd.isna(fraction) else fraction
                    size = None if pd.isna(size) else size
                    sample_weight = 0 if pd.isna(sample_weight) else sample_weight
                    primer_raw = 0 if pd.isna(primer_raw) else primer_raw
                    duplicate_raw = 0 if pd.isna(duplicate_raw) else duplicate_raw
                    to_its = None if pd.isna(to_its) else to_its
                    remark = None if pd.isna(remark) else remark
                    sampling_desc = None if pd.isna(sampling_desc) else sampling_desc

                    id_type     = type_dict.get(sample_type)
                    id_method   = method_dict.get(sample_method)
                    id_material = material_dict.get(nama_material)

                    if not id_material:
                        raise ValueError(f"Material tidak ditemukan: {nama_material}")
                    if not id_type:
                        raise ValueError(f"Sample_Type tidak ditemukan: {sample_type}")
                    if not id_method:
                        raise ValueError(f"Sampling_Method tidak ditemukan: {sample_method}")

                    if sample_type in ['LIS', 'SAS']:
                        kode_batch = f"{sample_type}{id_material}{batch_code or ''}"
                        pulp_batch = f"{sample_type}{batch_code or ''}"
                        monitoring_batch = None
                        type_val = sample_type
                    else:
                        kode_batch = None
                        pulp_batch = None
                        monitoring_batch = f"{sample_type}{id_material}{batch_code or ''}{increments or ''}"
                        type_val = sample_type

                    left_date = date_sale.day if pd.notna(date_sale) else None

                     # Cek duplikat hanya jika sample_number tidak kosong
                    if SampleProductions.objects.filter(sample_number=sample_number).exists():
                        duplicates.append(f"Duplicate at row {index}: {sample_number}")
                        duplicate_rows.append(row.to_dict())  # INI WAJIB
                        duplicate_imports += 1
                        continue

                    list_objects.append(
                        SampleProductions(
                            tgl_sample=date_sale,
                            shift=shift,
                            id_type_sample=id_type,
                            id_method=id_method,
                            id_material=id_material,
                            product_code=None,  # sementara kosongkan kalau file ini memang tidak punya product_code
                            batch_code=batch_code,
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
                            type=type_val,
                            kode_batch=kode_batch,
                            selling_pulp=pulp_batch,
                            sale_monitoring=monitoring_batch,
                            sampling_deskripsi=sampling_desc,
                            left_date=left_date,
                        )
                    )
                    successful_imports += 1

                except Exception as e:
                    errors.append(f"Error at row {index}: {str(e)}")
                    continue

            # =========================
            # BULK INSERT
            # =========================
            SampleProductions.objects.bulk_create(list_objects, batch_size=1000)

    except Exception as e:
        errors.append(f"Transaction failed: {str(e)}")

    # =========================
    # SAVE DUPLICATE FILE
    # =========================
    if duplicate_rows:
        dup_df = pd.DataFrame(duplicate_rows)
        filename = f"duplicates_{uuid.uuid4().hex}.xlsx"
        duplicate_dir = os.path.join(settings.MEDIA_ROOT, 'tmp_duplicates')
        os.makedirs(duplicate_dir, exist_ok=True)
        duplicate_file_path = os.path.join(duplicate_dir, filename)
        dup_df.to_excel(duplicate_file_path, index=False)

    # =========================
    # LOG TASK
    # =========================
    taskImports.objects.create(
        task_id=import_samples_selling.request.id,
        successful_imports=successful_imports,
        failed_imports=len(errors),
        duplicate_imports=duplicate_imports,
        errors="\n".join(errors) if errors else None,
        duplicates="\n".join(duplicates) if duplicates else None,
        file_name=original_file_name,
        destination='Samples Selling',
        duplicate_file_path=os.path.relpath(duplicate_file_path, settings.MEDIA_ROOT) if duplicate_file_path else None
    )

    return {
        'message': 'Import selesai',
        'successful_imports': successful_imports,
        'failed_imports': len(errors),
        'duplicate_imports': duplicate_imports,
        'errors': errors,
        'duplicates': duplicates,
    }