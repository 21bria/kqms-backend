import os
import uuid
import pandas as pd
from datetime import datetime, timedelta,time
from celery import shared_task
from django.db import transaction
from django.conf import settings
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

def parse_time_hauling(raw_value):
    if pd.isna(raw_value):
        return None

    # Jika sudah datetime.time
    if isinstance(raw_value, time):
        return raw_value

    # Jika sudah datetime
    if isinstance(raw_value, datetime):
        return raw_value.time()

    # Jika format Excel waktu (float)
    if isinstance(raw_value, float) and 0 <= raw_value < 1:
        try:
            excel_base = datetime(1899, 12, 30)  # Excel zero date
            time_value = (excel_base + pd.to_timedelta(raw_value, unit="D")).time()
            return time_value
        except:
            pass

    # Jika integer (seperti 805 → 08:05)
    if isinstance(raw_value, int) or (isinstance(raw_value, str) and raw_value.isdigit()):
        try:
            val = str(int(raw_value)).zfill(4)  # Pastikan panjang 4 digit
            return time(hour=int(val[:2]), minute=int(val[2:]))
        except:
            pass

    # Coba parsing dari string format umum
    if isinstance(raw_value, str):
        for fmt in ("%H:%M", "%I:%M %p", "%H%M", "%H:%M:%S"):
            try:
                return datetime.strptime(raw_value.strip(), fmt).time()
            except:
                continue

    # Gagal parsing
    return None

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

    #Konversi kolom ke datetime dengan format yang sesuai
    df['Date Production'] = pd.to_datetime(df['Date Production'], format='%Y-%m-%d', errors='coerce')
    # Ambil hanya tanggal (tanpa waktu)
    df['Date Production'] = df['Date Production'].dt.date

    # Buat dictionary dari Tabel untuk pencarian ID berdasarkan nama
    # source_dict      = dict(SourceMines.objects.values_list('sources_area', 'id'))
    loading_dict     = dict(SourceMinesLoading.objects.values_list('loading_point', 'id'))
    dumping_dict     = dict(SourceMinesDumping.objects.values_list('dumping_point', 'id'))
    dome_dict        = dict(SourceMinesDome.objects.values_list('pile_id', 'id'))
    material_dict    = dict(Material.objects.values_list('nama_material', 'id'))
    addition_bucket  = dict(mineAdditionFactor.objects.values_list('validation', 'bucket_capacity'))
    addition_density = dict(mineAdditionFactor.objects.values_list('validation', 'density_lcm'))


    # Mulai transaksi untuk memastikan rollback jika terjadi error
    try:
        with transaction.atomic():
            for index, row in df.iterrows():
                date_pds        = row['Date Production']
                time            = row['Time Hauling']
                jam_ritase      = parse_time_hauling(time)
                vendors         = row['Vendors']
                shift           = row['Shift']
                loader          = row['Loader']
                parsing         = row['Parsing']
                hauler_class    = row['Loader Class']
                hauler          = row['Hauler']
                # source          = row['Sources']
                loading_point   = row['Loading Point']
                dumping_point   = row['Dumping Point']
                dome_id         = row['Pile Id']
                nama_material   = row['Material']
                category_mine   = row['Category']
                distance        = row['Distance']
                block           = row['Block Id']
                rl_from         = row['From Rl']
                rl_to           = row['To Rl']
                ritase          = row['Ritase']
                direct          = row['Direct']
                remarks         = row['Remarks']

                # Tambahkan leading zero untuk time jika nilainya antara 0-9
                if isinstance(time, int) and 0 <= time <= 9:
                    time = f"0{time}"

                vendors       = None if pd.isna(vendors) else vendors
                category_mine = None if pd.isna(category_mine) else category_mine
                block         = None if pd.isna(block) else block
                rl_from       = None if pd.isna(rl_from) else rl_from
                rl_to         = None if pd.isna(rl_to) else rl_to
                distance      = None if pd.isna(distance) else distance
                remarks       = None if pd.isna(remarks) else remarks

                # Cari ID dari Model berdasarkan nama
                # id_source   = source_dict.get(source, 1)  
                id_source   = None  
                id_loading  = loading_dict.get(loading_point, 1)  
                id_dumping  = dumping_dict.get(dumping_point, 1)  
                id_dome     = dome_dict.get(dome_id, None)  
                # id_block    = block_dict.get(block, None)  
                id_material = material_dict.get(nama_material, None) 

                hauler_class_str  = str(hauler_class or "")
                nama_material_str = str(nama_material or "")

                # addition_key = f"{hauler_class_str.strip()}{vendors.strip()}{nama_material_str.strip()}"
                
                addition_key = f"{hauler_class_str.strip()}{nama_material_str.strip()}"

                bucket_capacity = addition_bucket.get(addition_key, 0)
                density_lcm     = addition_density.get(addition_key, 0)

                # hitung tonnage sesuai formula
                tonnage = (float(parsing or 0) * float(ritase or 0) * float(bucket_capacity or 0) * float(density_lcm or 0))

                # hitung tonnage sesuai material
                # if nama_material_str.upper() == "LIM":
                #     tonnage = 19.5 * float(ritase or 0)
                # elif nama_material_str.upper() == "SAP":
                #     tonnage = 19 * float(ritase or 0)
                # else:
                #     tonnage = (
                #         float(parsing or 0) *
                #         float(ritase or 0) *
                #         float(bucket_capacity or 0) *
                #         float(density_lcm or 0)
                #     )


                # Modifikasi hauler
                type_hauler = None


                # ref_plan = f"{date_pds}{category_mine}{source}{vendors}".replace(" ", "")
                ref_plan = f"{date_pds}{category_mine}{vendors}".replace(" ", "")

                if date_pds:  # Pastikan tanggal bukan None
                    date_str  = date_pds.strftime('%Y-%m-%d')
                    date_obj  = datetime.strptime(date_str, '%Y-%m-%d')
                    left_date = date_obj.day
                else:
                    left_date = None

               # Ambil jam dari kolom "Time Hauling" sebagai left_loading
                jam_ritase = None
                if pd.notna(time):
                    if isinstance(time, datetime):
                        jam_ritase = time.time()
                    else:
                        try:
                            jam_ritase = pd.to_datetime(str(time)).time()
                        except:
                            jam_ritase = None

                # Ambil hanya jam (2 digit) sebagai string
                left_loading = str(jam_ritase.hour).zfill(2) if jam_ritase else None

                try:
                    data = mineProductions(
                           date_production = date_pds,
                                vendors         = vendors,
                                shift           = shift,
                                loader          = loader,
                                bucket          = parsing,
                                hauler_class    = hauler_class,
                                hauler          = hauler,
                                sources_area    = id_source,
                                loading_point   = id_loading,
                                dumping_point   = id_dumping,
                                dome_id         = id_dome,
                                category_mine   = category_mine,
                                time_loading    = time,
                                left_loading    = left_loading, 
                                from_rl         = rl_from,
                                to_rl           = rl_to,
                                id_material     = id_material,
                                ritase          = ritase,
                                bcm             = 0,
                                tonnage         = tonnage,
                                direct          = direct,
                                remarks         = remarks,
                                hauler_type     = type_hauler,
                                ref_materials   = ref_plan,
                                left_date       = left_date,
                                task_id         = import_mine_productions.request.id,
                    )
                    list_objects.append(data)
                    successful_imports += 1
                except Exception as e:
                    errors.append(f"Error at row {index}: {str(e)}")
                    continue
            
            # Menggunakan bulk_create untuk menyimpan objek dalam batch
            mineProductions.objects.bulk_create(list_objects, batch_size=1000)
    
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
