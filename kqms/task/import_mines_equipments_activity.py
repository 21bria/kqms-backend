import os
import uuid
import pandas as pd
from celery import shared_task
from django.db.models.functions import Trim
from django.db import transaction
from django.conf import settings
from ..models.task_model import taskImports
from ..models.mine_status_units import UnitStatus, UnitActivity

@shared_task(name='kqms.task.import_mines_equipments_activity.import_mines_equipments_activity')
def import_mines_equipments_activity(file_path, original_file_name):
    df = pd.read_excel(file_path)

    errors = []
    duplicates = []
    duplicate_rows = []
    list_objects = []

    successful_imports = 0
    duplicate_imports = 0
    duplicate_file_path = None

    # MAPPING Activity Categories
    category_dict = dict(UnitStatus.objects.annotate(trimmed=Trim('name') ).values_list('trimmed', 'id'))

    # AMBIL EXISTING KEYS (master data → aman)
    existing_keys = set(UnitActivity.objects.values_list('code', flat=True))
    seen_keys = set()

    try:
        with transaction.atomic():
            # 1️ VALIDASI KATEGORI (FAIL FAST)
            missing_categories = set()

            for index, row in df.iterrows():
                category = row.get('activity_category')

                if pd.isna(category):
                    missing_categories.add(f"Empty category at row {index}")
                    continue

                category_key = str(category).strip()
                if category_key not in category_dict:
                    missing_categories.add(f"{category_key} (row {index})")

            if missing_categories:
                raise ValueError(
                    "Import dibatalkan. Category tidak valid:\n" +
                    "\n".join(sorted(missing_categories))
                )

            # ============================
            # 2️ PROSES INSERT
            # ============================
            for index, row in df.iterrows():
                #  perbaiki typo kolom
                code_raw = row.get('activity_code')
                name_raw = row.get('activity_name')
                category_raw = row.get('activity_category')

                # validasi code
                if pd.isna(code_raw) or str(code_raw).strip() == '':
                    errors.append(f"Empty code at row {index}")
                    continue

                # trim & format
                code = str(code_raw).strip().upper()
                name = str(name_raw).strip() if not pd.isna(name_raw) else ''
                category_str = str(category_raw).strip()

                # ambil id_category
                id_category = category_dict.get(category_str)
                if id_category is None:
                    errors.append(f"Category not found at row {index}")
                    continue

                # cek duplikat dalam file
                if code in seen_keys:
                    duplicates.append(f"Duplicate in file at row {index}: {code}")
                    duplicate_rows.append(row.to_dict())
                    duplicate_imports += 1
                    continue

                # cek duplikat di DB
                if code in existing_keys:
                    duplicates.append(f"Duplicate in DB at row {index}: {code}")
                    duplicate_rows.append(row.to_dict())
                    duplicate_imports += 1
                    continue

                # tambahkan ke set
                seen_keys.add(code)

                # buat object
                obj = UnitActivity(
                    code=code,
                    name=name,
                    status_id=id_category,
                )
                list_objects.append(obj)
            # BULK INSERT
            if list_objects:
                UnitActivity.objects.bulk_create(list_objects, batch_size=200)
                successful_imports = len(list_objects)

            # SIMPAN FILE DUPLIKAT
            if duplicate_rows:
                dup_df = pd.DataFrame(duplicate_rows)
                filename = f"duplicates_{uuid.uuid4().hex}.xlsx"
                duplicate_dir = os.path.join(settings.MEDIA_ROOT, 'tmp_duplicates')
                os.makedirs(duplicate_dir, exist_ok=True)
                duplicate_file_path = os.path.join(duplicate_dir, filename)
                dup_df.to_excel(duplicate_file_path, index=False)

    except Exception as e:
        errors.append(str(e))

    # 3️ LOGGING TASK
    try:
        taskImports.objects.create(
            task_id=import_mines_equipments_activity.request.id,
            successful_imports=successful_imports,
            failed_imports=len(errors),
            duplicate_imports=duplicate_imports,
            errors="\n".join(errors) if errors else None,
            duplicates="\n".join(duplicates) if duplicates else None,
            file_name=original_file_name,
            destination='Mine Equipments Activity',
            duplicate_file_path=os.path.relpath(
                duplicate_file_path, settings.MEDIA_ROOT
            ) if duplicate_file_path else None
        )
    except Exception:
        pass

    return {
        'message': (
            'Import failed due to invalid category'
            if errors and not successful_imports
            else 'Import completed with duplicates'
            if duplicates
            else 'Import successful'
        ),
        'successful_imports': successful_imports,
        'failed_imports': len(errors),
        'duplicate_imports': duplicate_imports,
        'errors': errors,
        'duplicates': duplicates,
        'duplicate_file': (
            os.path.relpath(duplicate_file_path, settings.MEDIA_ROOT)
            if duplicate_file_path else None
        )
    }
