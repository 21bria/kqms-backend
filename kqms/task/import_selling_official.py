import os
import uuid
import pandas as pd
from celery import shared_task
from django.db import transaction
from django.conf import settings
from ..models.selling_official import SellingOfficial,SellingSurveyor
from ..models.stock_factories import StockFactories
from ..models.task_model import taskImports
import re
from django.db.models.functions import Trim
from django.db import transaction


# Fungsi untuk membersihkan data numerik
def clean_numeric(value):
    try:
        if pd.isna(value):
            return 0
        if isinstance(value, str):
            value = value.strip()
            value = value.replace(',', '')  # hapus ribuan separator
            if value == '':
                return 0
            # hapus karakter selain angka dan titik
            value = re.sub(r"[^0-9.<>]", "", value)
            if value.startswith('<') or value.startswith('>'):
                value = value[1:]
            if re.match(r"^\d+(\.\d+)?$", value):
                return float(value)
            return 0
        return value if isinstance(value, (int, float)) else 0
    except Exception as e:
        print(f"Error processing value: {value}, Error: {e}")
        return 0

@shared_task(name='kqms.task.import_selling_official.import_selling_official')
def import_selling_official(file_path, original_file_name):
    print(f"[TASK] Processing: {original_file_name}")
    errors = []
    duplicates = []
    duplicate_rows = []
    list_objects = []
    successful_imports = 0
    duplicate_imports = 0
    duplicate_file_path = None

    try:
        df = pd.read_excel(file_path)


        df['start_date'] = pd.to_datetime(df['Start Loading']).dt.date
        df['end_date']   = pd.to_datetime(df['Complete Loading']).dt.date

        surveyor_dict    = dict(SellingSurveyor.objects.annotate(trimmed=Trim('code_surveyor')).values_list('trimmed', 'id'))
        buyer_dict       = dict(StockFactories.objects.annotate(trimmed=Trim('factory_stock')).values_list('trimmed', 'id'))

        df['tonnage'] = df['Tonnage'].fillna(0).astype(float)
        # Bersihkan semua kolom numerik di DataFrame
        numeric_columns = [
                'Ni', 'Fe', 'Al2O3', 'Co', 'MgO', 'SiO2', 'CaO', 'MnO', 'Cr2O3', 'MC'
        ]

        for col in numeric_columns:
            df[col] = df[col].apply(clean_numeric)
                
        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    surveyor     = row.get('Surveyor')
                    so_number    = None if pd.isna(row.get('So Number')) else str(row.get('So Number')).strip()
                    buyer        = None if pd.isna(row.get('Buyer')) else str(row.get('Buyer')).strip()
                    product_code = None if pd.isna(row.get('Code Lot')) else str(row.get('Code Lot')).strip()
                    type_selling = None if pd.isna(row.get('Type Selling')) else str(row.get('Type Selling')).strip()
                    start_date   = row.get('start_date')
                    end_date     = row.get('end_date')
                    barge_code   = None if pd.isna(row.get('Barge Code')) else str(row.get('Barge Code')).strip()
                    tonnage      = row.get('tonnage')
                    ni           = row.get('Ni', 0) 
                    fe           = row.get('Fe', 0)
                    al2o3        = row.get('Al2O3', 0)
                    co           = row.get('Co', 0)
                    mgo          = row.get('MgO', 0)
                    sio2         = row.get('SiO2', 0)
                    cao          = row.get('CaO', 0)
                    mno          = row.get('MnO', 0)
                    cr2o3        = row.get('Cr2O3', 0)
                    mc           = row.get('MC', 0)

                    id_surveyor  = surveyor_dict.get(surveyor)
                    id_buyer     = buyer_dict.get(buyer)

                   # Ambil re_assay terakhir dari database, pastikan default 0 jika None
                    last_obj = SellingOfficial.objects.filter(product_code=product_code).order_by('-re_assay').first()
                    last_re_assay = last_obj.re_assay if last_obj and last_obj.re_assay is not None else 0
                    re_assay = last_re_assay + 1

                    obj = SellingOfficial(
                        id_surveyor=id_surveyor,
                        id_factory=id_buyer,
                        so_number=so_number,
                        product_code=product_code,
                        type_selling=type_selling,
                        barge_code=barge_code,
                        start_date=start_date,
                        end_date=end_date,
                        tonnage=tonnage,
                        ni=ni,
                        fe=fe,
                        al2o3=al2o3,
                        co=co,
                        mgo=mgo,
                        sio2=sio2,
                        cao=cao,
                        mno=mno,
                        cr2o3=cr2o3,
                        mc=mc,
                        re_assay=re_assay  # ← ini kolom baru
                    )
                    list_objects.append(obj)
                    successful_imports += 1

                except Exception as e:
                    errors.append(f"Error at row {index}: {str(e)}")


            if list_objects:
                SellingOfficial.objects.bulk_create(list_objects, batch_size=200)

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

    try:
            taskImports.objects.create(
            task_id=import_selling_official.request.id,
            successful_imports=successful_imports,
            failed_imports=len(errors),
            duplicate_imports=duplicate_imports,
            errors="\n".join(errors) if errors else None,
            duplicates="\n".join(duplicates) if duplicates else None,
            file_name=original_file_name,
            destination='Official Selling',
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