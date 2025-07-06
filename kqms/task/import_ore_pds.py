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
from ..models.ore_productions import OreProductions
from ..models.materials import Material
from ..models.block_model import Block
from ..models.source_model import SourceMinesLoading,SourceMinesDumping,SourceMinesDome

@shared_task(name='kqms.task.import_ore_pds.import_ore_productions')
def import_ore_productions(file_path, original_file_name):
    df = pd.read_excel(file_path)
    errors = []
    duplicates = []
    duplicate_rows = []
    list_objects = []
    successful_imports = 0
    duplicate_imports = 0
    duplicate_file_path = None

    #Konversi kolom ke datetime dengan format yang sesuai
    df['Date_Production'] = pd.to_datetime(df['Date_Production'], format='%Y-%m-%d', errors='coerce')

    # Buat dictionary dari Tabel untuk pencarian ID berdasarkan nama
    source_dict     = dict(SourceMinesLoading.objects.values_list('loading_point', 'id'))
    block_dict      = dict(Block.objects.values_list('mine_block', 'id'))
    material_dict   = dict(Material.objects.values_list('nama_material', 'id'))
    stockpile_dict  = dict(SourceMinesDumping.objects.values_list('dumping_point', 'id'))
    dome_dict       = dict(SourceMinesDome.objects.values_list('pile_id', 'id'))
      

    # Mulai transaksi untuk memastikan rollback jika terjadi error
    try:
        with transaction.atomic():
            for index, row in df.iterrows():
                date_pds        = row['Date_Production']
                shift           = row['Shift']
                source          = row['Prospect_Area']
                block           = row['Mine_Block']
                rl_from         = row['From']
                rl_to           = row['To']
                nama_material   = row['Layer']
                grade           = row['Ni_GradeEx']
                grade_control   = row['Grade_Control']
                truck           = row['Unit_Truck']
                stockpile       = row['Stockpile']
                dome            = row['Pile_ID']
                batch           = row['Batch_Code']
                increment       = row['Incerment']
                status_batch    = row['Batch_Status']
                ritase          = row['Ritase']
                tonnage         = row['Tonnage']
                status_pile     = row['Pile_Status']
                remarks         = row['Remarks']
                class_ore       = row['Ore_Class']

                remarks = None if pd.isna(remarks) else remarks
                
                # Cari ID dari Model berdasarkan nama
                id_source         = source_dict.get(source, None)  
                id_block          = block_dict.get(block, None)  
                id_material       = material_dict.get(nama_material, None) 
                id_pile           = dome_dict.get(dome, None) 
                id_stockpile      = stockpile_dict.get(stockpile, None)  
               
                # Gabungkan Kode
                kode_batch   = 'PDS' + str(id_material) + truck + str(id_stockpile) + str(id_pile) + batch
                status_dome  = 'Continue'

                if date_pds:  # Pastikan tanggal bukan None
                    date_str  = date_pds.strftime('%Y-%m-%d')
                    date_obj  = datetime.strptime(date_str, '%Y-%m-%d')
                    left_date = date_obj.day
                else:
                    left_date = None

                # Menentukan nilai sale_adjust berdasarkan nilai Layer
                if nama_material == 'LIM':
                    sale_adjust = 'HPAL'
                elif nama_material == 'SAP':
                    sale_adjust = 'RKEF'
                else:
                    sale_adjust = None  # Atau bisa set default value lainnya    

                try:
                    data = OreProductions(
                        tgl_production=date_pds,
                        shift=shift,
                        id_prospect_area=id_source,
                        id_block=id_block,
                        from_rl =rl_from,
                        to_rl=rl_to,
                        id_material=id_material,
                        grade_expect=grade,
                        grade_control=grade_control,
                        unit_truck=truck,
                        id_stockpile=id_stockpile,
                        id_pile=id_pile,
                        batch_code=batch,
                        increment=increment,
                        batch_status=status_batch,
                        ritase=ritase,
                        tonnage=tonnage,
                        pile_status=status_pile,
                        remarks=remarks,
                        kode_batch=kode_batch,
                        pile_original=id_pile,
                        stockpile_ori=id_stockpile,
                        left_date=left_date,
                        truck_factor=truck,
                        ore_class=class_ore,
                        status_dome=status_dome,
                        sale_adjust=sale_adjust,
                    )
                    list_objects.append(data)
                    successful_imports += 1
                except Exception as e:
                    errors.append(f"Error at row {index}: {str(e)}")
                    continue
            
            # Menggunakan bulk_create untuk menyimpan objek dalam batch
            OreProductions.objects.bulk_create(list_objects, batch_size=1000)
        
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
            task_id=import_ore_productions.request.id,
            successful_imports=successful_imports,
            failed_imports=len(errors),
            duplicate_imports=duplicate_imports,
            errors="\n".join(errors) if errors else None,
            duplicates="\n".join(duplicates) if duplicates else None,
            file_name=original_file_name,
            destination ='Ore Productions',
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
