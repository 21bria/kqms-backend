import os
import uuid
import pandas as pd
from celery import shared_task
from django.db import transaction
from django.conf import settings
from ..models.waybill_model import Waybills
from ..models.task_model import taskImports
from datetime import datetime,timezone
from django.db import transaction


@shared_task(name='kqms.task.import_waybills.import_waybills')
def import_waybills(file_path, original_file_name):
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

        df['tgl_deliver'] = pd.to_datetime(df['tgl_deliver']).dt.date

        # Konversi durasi waktu (misalnya 13.5 jam → timedelta)
        df['delivery_time'] = pd.to_datetime(df['delivery_time'], format='%H:%M:%S').dt.time

        # Gabungkan kolom  menjadi datetime tanpa timezone
        # df['delivery'] = df.apply(lambda row: datetime.combine(row['tgl_deliver'], row['delivery_time']), axis=1)
        df['delivery'] = df.apply(lambda row: timezone.make_aware(datetime.combine(row['tgl_deliver'], row['delivery_time'])), axis=1)
        # df['delivery'] = df['delivery'].apply(lambda x: x.replace(tzinfo=None))
        

        df['numb_sample'] = df['numb_sample'].fillna(0).astype(int)


        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    tgl_deliver = row.get('tgl_deliver')
                    delivery_time = row.get('delivery_time')
                    waybill_number = row.get('waybill_number')
                    sample_id = row.get('sample_id')
                    numb_sample = row.get('numb_sample')
                    mral_order = row.get('mral_order')
                    roa_order = row.get('roa_order')
                    remarks = row.get('remarks')
                    delivery = row.get('delivery')

                    if Waybills.objects.filter(waybill_number=waybill_number).exists():
                        duplicates.append(f"Duplicate at row {index}: {waybill_number}")
                        duplicate_rows.append(row.to_dict())
                        duplicate_imports += 1
                        continue

                    obj = Waybills(
                        tgl_deliver=tgl_deliver,
                        delivery_time=delivery_time,
                        delivery=delivery,
                        waybill_number=waybill_number,
                        sample_id=sample_id,
                        numb_sample=numb_sample,
                        mral_order=(str(mral_order).strip().lower() == 'yes'),
                        roa_order=(str(roa_order).strip().lower() == 'yes'),
                        remarks=remarks
                    )
                    list_objects.append(obj)
                    successful_imports += 1
                except Exception as e:
                    errors.append(f"Error at row {index}: {str(e)}")

            if list_objects:
                Waybills.objects.bulk_create(list_objects, batch_size=200)

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
            task_id=import_waybills.request.id,
            successful_imports=successful_imports,
            failed_imports=len(errors),
            duplicate_imports=duplicate_imports,
            errors="\n".join(errors) if errors else None,
            duplicates="\n".join(duplicates) if duplicates else None,
            file_name=original_file_name,
            destination='Waybills',
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