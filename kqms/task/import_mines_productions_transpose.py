import os
import uuid
import pandas as pd
from datetime import datetime, timedelta,time
from celery import shared_task
from django.db import transaction
from django.conf import settings
import random
from django.db import transaction
from ..models.task_model import taskImports
from ..models.mine_productions import mineProductions
from ..models.materials import Material
from ..models.source_model import SourceMines,SourceMinesLoading,SourceMinesDumping,SourceMinesDome
from ..models.mine_addition_factor import mineAdditionFactor
from django.db.models import Func
from django.db.models.functions import Trim
import logging

# Dapatkan instance logger
logger = logging.getLogger('celery')


@shared_task(name='kqms.task.import_mines_productions.import_mine_productions')
def import_mine_productions(file_path, original_file_name):
    df = pd.read_excel(file_path)
    errors = []
    duplicates = []
    duplicate_rows = []
    list_objects = []
    successful_imports = 0
    duplicate_imports = 0
    duplicate_file_path = None

    df['Date Production'] = pd.to_datetime(df['Date Production'], format='%Y-%m-%d', errors='coerce')

    source_dict   = dict(SourceMines.objects.annotate(trimmed_sources=Trim('sources_area')).values_list('trimmed_sources', 'id'))
    loading_dict  = dict(SourceMinesLoading.objects.annotate(trimmed_loading=Trim('loading_point')).values_list('trimmed_loading', 'id'))
    dumping_dict  = dict(SourceMinesDumping.objects.annotate(trimmed_dumping=Trim('dumping_point')).values_list('trimmed_dumping', 'id'))
    dome_dict     = dict(SourceMinesDome.objects.annotate(trimmed_dome=Trim('pile_id')).values_list('trimmed_dome', 'id'))
    material_dict = dict(Material.objects.annotate(trimmed_material=Trim('nama_material')).values_list('trimmed_material', 'id'))
    addition_bcm  = dict(mineAdditionFactor.objects.values_list('validation', 'tf_bcm'))
    addition_ton  = dict(mineAdditionFactor.objects.values_list('validation', 'tf_ton'))

    non_time_columns = ['Date Production', 'Vendors', 'Shift', 'Loader', 'Hauler', 'Hauler Class', 
                        'Sources', 'Loading Point', 'Dumping Point', 'Pile Id', 'Material', 
                        'Category', 'Distance', 'Block Id', 'From Rl', 'To Rl', 'Remarks']

    time_columns = [col for col in df.columns if isinstance(col, time)]

    try:
        with transaction.atomic():
            for index, row in df.iterrows():
                date_pds        = row['Date Production']
                vendors         = row['Vendors']
                shift           = row['Shift']
                loader          = row['Loader']
                hauler          = row['Hauler']
                hauler_class    = row['Hauler Class']
                source          = row['Sources']
                loading_point   = row['Loading Point']
                dumping_point   = row['Dumping Point']
                dome_id         = row['Pile Id']
                nama_material   = row['Material']
                category_mine   = row['Category']
                distance        = row['Distance']
                block           = row['Block Id']
                rl_from         = None if pd.isna(row['From Rl']) else row['From Rl']
                rl_to           = None if pd.isna(row['To Rl']) else row['To Rl']
                remarks         = None if pd.isna(row['Remarks']) else row['Remarks']

                id_source     = source_dict.get(source, None)  
                id_loading    = loading_dict.get(loading_point, 1)  
                id_dumping    = dumping_dict.get(dumping_point, 1)  
                id_dome       = dome_dict.get(dome_id, 1)  
                id_material   = material_dict.get(nama_material, None)

                hauler_class_str  = str(hauler_class or "")
                nama_material_str = str(nama_material or "")
                # addition_key = f"{hauler_class_str.strip()}{nama_material_str.strip()}"
                addition_key = f"{hauler_class_str.strip()}{vendors.strip()}{nama_material_str.strip()}"
                bcm_factor = addition_bcm.get(addition_key, 0)
                ton_factor = addition_ton.get(addition_key, 0)

                type_hauler = None
                if isinstance(hauler_class, str):
                    if 'ADT' in hauler_class:
                        type_hauler = 'ADT'
                    elif 'Dump Truck' in hauler_class:
                        type_hauler = 'DT'

                ref_plan = f"{date_pds}{category_mine}{source}{vendors}".replace(" ", "")

                for time_col in time_columns:
                    time_value = row.get(time_col, 0)
                    if pd.notna(time_value) and time_value > 0:
                        jam = time_col.hour

                        for _ in range(int(time_value)):
                            menit = random.randint(0, 59)
                            if shift == 'N' and 7 <= jam <= 18:
                                jam_ritase = (jam + 12) % 24
                            else:
                                jam_ritase = jam

                            time_loading = f"{jam_ritase:02d}:{menit:02d}"

                            data = mineProductions(
                                date_production = date_pds,
                                vendors         = vendors,
                                shift           = shift,
                                loader          = loader,
                                hauler          = hauler,
                                hauler_class    = hauler_class,
                                sources_area    = id_source,
                                loading_point   = id_loading,
                                dumping_point   = id_dumping,
                                dome_id         = id_dome,
                                category_mine   = category_mine,
                                time_loading    = time_loading,
                                left_loading    = jam_ritase, 
                                from_rl         = rl_from,
                                to_rl           = rl_to,
                                id_material     = id_material,
                                ritase          = 1,
                                bcm             = bcm_factor,
                                tonnage         = ton_factor,
                                remarks         = remarks,
                                hauler_type     = type_hauler,
                                ref_materials   = ref_plan,
                                left_date       = date_pds.day if date_pds else None,
                                task_id         = import_mine_productions.request.id,
                            )
                            list_objects.append(data)
                            successful_imports += 1

            mineProductions.objects.bulk_create(list_objects, batch_size=200)

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
            task_id=import_mine_productions.request.id,
            successful_imports=successful_imports,
            failed_imports=len(errors),
            duplicate_imports=duplicate_imports,
            errors="\n".join(errors) if errors else None,
            duplicates="\n".join(duplicates) if duplicates else None,
            file_name=original_file_name,
            destination='Mine Productions',
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
