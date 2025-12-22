import os
import uuid
import pandas as pd
from celery import shared_task
from django.db.models.functions import Trim
from django.db import transaction
from django.conf import settings
from ..models.task_model import taskImports
from ..models.mine_units import MineUnits, unitsCategories
from ..models.vendors import Vendors

@shared_task(name='kqms.task.import_mines_equipments.import_mines_equipments')
def import_mines_equipments(file_path, original_file_name):
    df = pd.read_excel(file_path)

    errors = []
    duplicates = []
    duplicate_rows = []
    list_objects = []

    successful_imports = 0
    duplicate_imports = 0
    duplicate_file_path = None

    # =====================================================
    # KONVERSI KOLON TANGGAL DAN ATASI NaT
    # =====================================================
    # Konversi tanggal
    for col in ['commisioning_date', 'on_hire', 'off_hire']:
        df[col] = pd.to_datetime(df[col], errors='coerce')  # auto-detect format
        df[col] = df[col].apply(lambda x: x.date() if pd.notna(x) else None)

     # MAPPING VENDOR DAN KATEGORI
    # =====================================================
    vendors_dict = dict(Vendors.objects.annotate(trimmed=Trim('vendor_name')).values_list('trimmed', 'id'))
    category_dict = dict(unitsCategories.objects.annotate(trimmed=Trim('category')).values_list('trimmed', 'id'))

    # =====================================================
    # AMBIL EXISTING KEYS (sekali saja)
    # =====================================================
    existing_keys = set(MineUnits.objects.values_list('unit_code', flat=True))
    seen_keys = set()  # untuk deteksi duplikat dalam file yang sama

    try:
        with transaction.atomic():
            for index, row in df.iterrows():
                unit_code = row['unit_code']
                unit_model = row.get('unit_model')
                unit_class = row.get('unit_type')
                brand = row.get('brand')
                category = row.get('category')
                vendors = row.get('vendors')
                commisioning_date = row.get('commisioning_date')
                on_hire = row.get('on_hire')
                off_hire = row.get('off_hire')
                description = row.get('description')

                # Mapping kategori & vendor, fallback None jika kosong
                id_category = category_dict.get(str(category).strip()) if pd.notna(category) else None
                id_vendor = vendors_dict.get(str(vendors).strip()) if pd.notna(vendors) else None

                # Key untuk duplikat
                key = unit_code

                # Deteksi duplikat dalam file
                if key in seen_keys:
                    duplicates.append(f"Duplicate in file at row {index}: {unit_code}")
                    duplicate_rows.append(row.to_dict())
                    duplicate_imports += 1
                    continue

                # Deteksi duplikat di DB
                if key in existing_keys:
                    duplicates.append(f"Duplicate in DB at row {index}: {unit_code}")
                    duplicate_rows.append(row.to_dict())
                    duplicate_imports += 1
                    continue

                seen_keys.add(key)

                # Buat objek
                try:
                    obj = MineUnits(
                        unit_code=unit_code,
                        unit_model=unit_model,
                        unit_class=unit_class,
                        brand=brand,
                        id_category=id_category,
                        id_vendor=id_vendor,
                        commisioning_date=commisioning_date,
                        on_hire=on_hire,
                        off_hire=off_hire,
                        description=description,
                        status=1,
                    )
                    list_objects.append(obj)
                    successful_imports += 1
                except Exception as e:
                    errors.append(f"Error at row {index}: {str(e)}")

            # Bulk insert data valid
            if list_objects:
                MineUnits.objects.bulk_create(list_objects, batch_size=200)

            # Simpan file Excel duplikat jika ada
            if duplicate_rows:
                dup_df = pd.DataFrame(duplicate_rows)
                filename = f"duplicates_{uuid.uuid4().hex}.xlsx"
                duplicate_dir = os.path.join(settings.MEDIA_ROOT, 'tmp_duplicates')
                os.makedirs(duplicate_dir, exist_ok=True)
                duplicate_file_path = os.path.join(duplicate_dir, filename)
                dup_df.to_excel(duplicate_file_path, index=False)

    except Exception as e:
        errors.append(f"Transaction failed: {str(e)}")

    # =====================================================
    # LOGGING TASK
    # =====================================================
    try:
        taskImports.objects.create(
            task_id=import_mines_equipments.request.id,
            successful_imports=successful_imports,
            failed_imports=len(errors),
            duplicate_imports=duplicate_imports,
            errors="\n".join(errors) if errors else None,
            duplicates="\n".join(duplicates) if duplicates else None,
            file_name=original_file_name,
            destination='Mine Equipments',
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
        result['duplicate_file'] = os.path.relpath(duplicate_file_path, settings.MEDIA_ROOT)

    return result
