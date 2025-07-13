import os
import uuid
import pandas as pd
from datetime import datetime
from celery import shared_task
from django.db import transaction
from django.conf import settings
from datetime import datetime, timedelta,time
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

    # Konversi kolom ke datetime dengan format yang sesuai
    df['Date Production'] = pd.to_datetime(df['Date Production'], format='%Y-%m-%d', errors='coerce')

    # Buat dictionary dari Tabel untuk pencarian ID berdasarkan nama
    source_dict   = dict(SourceMines.objects.annotate(trimmed_sources=Trim('sources_area')).values_list('trimmed_sources', 'id'))
    loading_dict  = dict(SourceMinesLoading.objects.annotate(trimmed_loading=Trim('loading_point')).values_list('trimmed_loading', 'id'))
    dumping_dict  = dict(SourceMinesDumping.objects.annotate(trimmed_dumping=Trim('dumping_point')).values_list('trimmed_dumping', 'id'))
    dome_dict     = dict(SourceMinesDome.objects.annotate(trimmed_dome=Trim('pile_id')).values_list('trimmed_dome', 'id'))
    material_dict = dict(Material.objects.annotate(trimmed_material=Trim('nama_material')).values_list('trimmed_material', 'id'))
    addition_bcm  = dict(mineAdditionFactor.objects.values_list('validation', 'tf_bcm'))
    addition_ton  = dict(mineAdditionFactor.objects.values_list('validation', 'tf_ton'))


    # Kolom non-waktu (kolom tetap yang tidak perlu ditranspose)
    non_time_columns = ['Date Production', 'Vendors', 'Shift', 'Loader', 'Hauler', 'Hauler Class', 
                        'Sources', 'Loading Point', 'Dumping Point', 'Pile Id', 'Material', 
                        'Category', 'Distance', 'Block Id', 'From Rl', 'To Rl', 'Remarks']

    # Kolom waktu dimulai dari kolom yang mengandung jam (contoh: 07:00, 08:00, dst.)
    time_columns = df.columns[len(non_time_columns):]  # Mulai dari kolom waktu
    
    # Mulai transaksi untuk memastikan rollback jika terjadi error
    try:
        with transaction.atomic():
            # Loop untuk setiap baris di DataFrame
            for index, row in df.iterrows():
                # Transpose setiap kolom waktu dan masukkan ke dalam database
                for i, time_col in enumerate(time_columns):
                    time_value = row[time_col]
                    if pd.notna(time_value):  # Jika ada data ritase
                        date_pds        = row['Date Production']
                        vendors         = row['Vendors']
                        shift           = row['Shift']
                        loader          = row['Loader']
                        hauler          = row['Hauler']
                        hauler_class    = row['Hauler Class']
                        # source          = str(row['Sources']).strip()  # Hapus spasi di awal/akh
                        source          = row['Sources']
                        loading_point   = row['Loading Point']
                        dumping_point   = row['Dumping Point']
                        dome_id         = row['Pile Id']
                        nama_material   = row['Material']
                        category_mine   = row['Category']
                        distance        = row['Distance']
                        block           = row['Block Id']
                        rl_from         = row['From Rl']
                        rl_to           = row['To Rl']
                        # bcm           = row['Bcm']
                        # tonnage       = row['Tonnage']
                        remarks       = row['Remarks']
                        rl_from       = None if pd.isna(rl_from) else rl_from
                        rl_to         = None if pd.isna(rl_to) else rl_to
                        remarks       = None if pd.isna(remarks) else remarks

                        # Cari ID dari Model berdasarkan nama
                        id_source     = source_dict.get(source, None)  
                        id_loading    = loading_dict.get(loading_point, 1)  
                        id_dumping    = dumping_dict.get(dumping_point, 1)  
                        id_dome       = dome_dict.get(dome_id, 1)  
                        id_material   = material_dict.get(nama_material, None)
                        
                        hauler_class  = str(hauler_class) if hauler_class is not None else ""
                        nama_material = str(nama_material) if nama_material is not None else ""

                        # Buat key untuk mencari addition factor
                        addition_key =  f"{hauler_class.strip()}{nama_material.strip()}"  
                        # Ambil tf_bcm dan tf_ton dari dictionary
                        if not addition_key:
                            logger.warning(f"Invalid addition_key generated: {addition_key}")
                            continue  # atau penanganan error yang sesuai

                        bcm_factor = addition_bcm.get(addition_key, None)
                        ton_factor = addition_ton.get(addition_key, None)

                        logger.debug(f"Generated addition_key: {addition_key}")
                        logger.debug(f"BCM Factor: {bcm_factor}, Ton Factor: {ton_factor}")

                        if bcm_factor is None:
                            bcm_factor = 0  # atau nilai default lainnya
                        if ton_factor is None:
                            ton_factor = 0  # atau nilai default lainnya

                        # Modifikasi hauler
                        if isinstance(hauler_class, str):
                            if 'ADT' in hauler_class:
                                type_hauler = 'ADT'
                            elif 'Dump Truck' in hauler_class:  
                                type_hauler = 'DT'
                            else:
                                type_hauler = None
                        else:
                            type_hauler = None  # Jika hauler_class bukan 

                        # Gabungkan Refrensi Plan
                        ref_plan = f"{date_pds}{category_mine}{source}{vendors}".replace(" ", "")  

                        try:
                           # Hapus desimal jika ada (contoh: '07:00:00.1' menjadi '07:00:00')
                            clean_time_str = str(time_columns[i]).strip().split('.')[0]  # Hapus spasi di awal/akhir dan desimal


                            # Parsing waktu dengan format 24 jam (H:M:S)
                            parsed_time = pd.to_datetime(clean_time_str, format='%H:%M:%S')

                            if pd.isna(parsed_time):  # Validasi parsing waktu
                                raise ValueError(f"Invalid time format: {clean_time_str}")

                            hour_value = parsed_time.hour  # Ambil jam

                            if pd.notna(time_value) and str(time_value).strip():  # Validasi nilai menit
                                # minute_value = int(time_value)  # Ambil menit dari kolom data
                                minute_value = int(float(time_value))  # Konversi dari float ke int secara eksplisit
                                
                            else:
                                raise ValueError(f"Invalid minute value for time column: {time_value}")


                            # Menyesuaikan jam berdasarkan shift
                            if shift == 'N' and 7 <= hour_value <= 18:  # Jika shift malam dan jam antara 7-18
                                hour_value = (hour_value + 12) % 24  # Tambahkan 12 dan pastikan tetap dalam rentang 0-23

                            # Gabungkan jam dan menit menjadi format waktu
                            time_loading = f"{hour_value}:{minute_value:02d}"  # Format sebagai HH:MM

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
                                left_loading    = hour_value, 
                                # block_id        = id_block,
                                from_rl         = rl_from,
                                to_rl           = rl_to,
                                id_material     = id_material,
                                ritase          = 1,  # Tetap 1 untuk setiap baris
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
                        except Exception as e:
                            errors.append(f"Error parsing time column: {clean_time_str} -> {str(e)}")
                            continue
            
            # Menggunakan bulk_create untuk menyimpan objek dalam batch
            mineProductions.objects.bulk_create(list_objects, batch_size=200)
    
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
            task_id=import_mine_productions.request.id,
            successful_imports=successful_imports,
            failed_imports=len(errors),
            duplicate_imports=duplicate_imports,
            errors="\n".join(errors) if errors else None,
            duplicates="\n".join(duplicates) if duplicates else None,
            file_name=original_file_name,
            destination ='Mine Productions',
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
