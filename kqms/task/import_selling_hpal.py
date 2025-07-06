from celery import shared_task
import pandas as pd
import re
from django.db.models.functions import Trim
from datetime import datetime
from django.db import transaction
from ..models.task_model import taskImports
from ..models.selling_data import SellingProductions
from ..models.materials import Material
from ..models.stock_factories import StockFactories
from ..models.source_model import SourceMinesDumping,SourceMinesDome

# Fungsi untuk membersihkan data numerik
def clean_numeric(value):
    try:
        if pd.isna(value):  # Cek jika NaN atau None
            return 0
        if isinstance(value, str):
            value = value.strip()  # Menghapus spasi di awal dan akhir
            if value == '':  # Jika string kosong
                return None
            # Menghapus karakter selain angka dan titik desimal
            value = re.sub(r"[^0-9.<>]", "", value)
            if value.startswith('<') or value.startswith('>'):
                value = value[1:]  # Menghapus tanda '<' atau '>'
            if re.match(r"^\d+(\.\d+)?$", value):  # Cek jika angka valid
                return float(value)
            return 0  # Jika tidak valid, kembalikan 0
        return value if isinstance(value, (int, float)) else 0
    except Exception as e:
        print(f"Error processing value: {value}, Error: {e}")
        return 0  # Kembalikan 0 jika terjadi error


@shared_task
def import_selling_hpal(file_path, original_file_name):
    df = pd.read_excel(file_path)
    errors = []
    duplicates = []
    list_new = []
    list_update = []
    
    successful_imports = 0
    duplicate_imports = 0

    df['timbang_isi']    = df['waktu_timbang_kosong'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df['timbang_kosong'] = df['waktu_timbang_isi'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df['tanggal']        = pd.to_datetime(df['tanggal']).dt.date

    # Dictionary untuk pencarian ID berdasarkan nama
    material_dict   = dict(Material.objects.annotate(trimmed_material=Trim('nama_material')).values_list('trimmed_material', 'id'))
    dome_dict       = dict(SourceMinesDome.objects.annotate(trimmed_dome=Trim('pile_id')).values_list('trimmed_dome', 'id'))
    factory_dict    = dict(StockFactories.objects.annotate(trimmed_fact=Trim('factory_stock')).values_list('trimmed_fact', 'id'))

    # Ambil semua nota yang sudah ada di database dalam dictionary untuk pencarian cepat
    existing_notas = {obj.nota: obj for obj in SellingProductions.objects.all()}  

    try:
        with transaction.atomic():
            for index, row in df.iterrows():
                nota = row['no_seri']
                
                # Cek apakah nota sudah ada di database
                existing_entry = existing_notas.get(nota)

                truck           = row['no_unit']
                nama_material   = row['nama_material']
                empety_weigth_f = row['berat_kosong']
                fill_weigth_f   = row['berat_kotor']
                netto_weigth_f  = row['berat_bersih']
                timbang_isi     = row['timbang_isi']
                timbang_kosong  = row['timbang_kosong']
                tujuan          = row['lokasi_pembongkaran']
                tanggal         = row['tanggal']
                dome            = row['dome']
                discharge       = row['discharge']
                shift           = row['shift']
                delivery_order  = row['code_hync']
                type            = row['type']
                sale_type       = row['sale_type']
                batch           = row['batch']

                id_material  = material_dict.get(nama_material, None)
                id_pile      = dome_dict.get(dome, None)
                id_factory   = factory_dict.get(discharge, None)

                kode_batch_g        = type + str(id_material) + delivery_order + batch
                new_kode_batch_scci = type + 'Split_SCCI' + str(id_material) + delivery_order + batch
                new_kode_batch_awk  = type + 'Split_AWK' + str(id_material) + delivery_order + batch
                new_batch_awk_pulp  = type + 'Split_AWK' + delivery_order + batch
                scci_order   = 'No'
                awk_order    = 'Yes'
                sale_dome    = 'Continue'
                time_hauling = '00:00:00'
                batch_g      = ''
                new_scci     = ''
                new_awk      = ''

                if tanggal:
                    date_str  = tanggal.strftime('%Y-%m-%d')
                    date_obj  = datetime.strptime(date_str, '%Y-%m-%d')
                    left_date = date_obj.day
                else:
                    left_date = None

                if existing_entry:
                    # Data sudah ada → Update
                    existing_entry.timbang_isi      = timbang_isi
                    existing_entry.timbang_kosong   = timbang_kosong
                    existing_entry.unit_code        = truck
                    existing_entry.id_material      = id_material
                    existing_entry.remarks          = tujuan
                    existing_entry.empety_weigth_f  = empety_weigth_f
                    existing_entry.fill_weigth_f    = fill_weigth_f
                    existing_entry.netto_weigth_f   = netto_weigth_f
                    existing_entry.id_factory       = id_factory
                    existing_entry.id_pile          = id_pile
                    existing_entry.batch            = batch
                    existing_entry.delivery_order   = delivery_order
                    existing_entry.tgl_hauling      = tanggal
                    existing_entry.time_hauling     = time_hauling
                    existing_entry.shift            = shift
                    existing_entry.batch_g          = batch_g
                    existing_entry.kode_batch_g     = kode_batch_g
                    existing_entry.left_date        = left_date
                    existing_entry.new_scci         = new_scci
                    existing_entry.new_scci_sub     = batch
                    existing_entry.new_kode_batch_scci = new_kode_batch_scci
                    existing_entry.scci_order       = scci_order
                    existing_entry.new_awk          = new_awk
                    existing_entry.new_awk_sub      = batch
                    existing_entry.new_kode_batch_awk = new_kode_batch_awk
                    existing_entry.new_batch_awk_pulp = new_batch_awk_pulp
                    existing_entry.awk_order        = awk_order
                    existing_entry.type_selling     = sale_type
                    existing_entry.date_wb          = tanggal
                    existing_entry.sale_adjust      = 'HPAL'
                    existing_entry.sale_dome        = sale_dome

                    list_update.append(existing_entry)
                    duplicate_imports += 1
                else:
                    # Data baru → Insert
                    list_new.append(SellingProductions(
                        nota=nota,
                        timbang_isi=timbang_isi,
                        timbang_kosong=timbang_kosong,
                        unit_code=truck,
                        id_material=id_material,
                        remarks=tujuan,
                        empety_weigth_f=empety_weigth_f,
                        fill_weigth_f=fill_weigth_f,
                        netto_weigth_f=netto_weigth_f,
                        id_factory=id_factory,
                        id_pile=id_pile,
                        batch=batch,
                        delivery_order=delivery_order,
                        tgl_hauling=tanggal,
                        time_hauling=time_hauling,
                        shift=shift,
                        batch_g=batch_g,
                        kode_batch_g=kode_batch_g,
                        left_date=left_date,
                        new_scci=new_scci,
                        new_scci_sub=batch,
                        new_kode_batch_scci=new_kode_batch_scci,
                        scci_order=scci_order,
                        new_awk=new_awk,
                        new_awk_sub=batch,
                        new_kode_batch_awk=new_kode_batch_awk,
                        new_batch_awk_pulp=new_batch_awk_pulp,
                        awk_order=awk_order,
                        type_selling=sale_type,
                        date_wb=tanggal,
                        sale_adjust='HPAL',
                        sale_dome=sale_dome,
                    ))

                    successful_imports += 1

            # Bulk Insert Semua Data Baru
            if list_new:
                SellingProductions.objects.bulk_create(list_new, batch_size=300)

            # Bulk Update Data Lama
            if list_update:
                SellingProductions.objects.bulk_update(list_update, [
                    'timbang_isi', 'timbang_kosong', 'id_material', 'remarks', 'empety_weigth_f',
                    'fill_weigth_f', 'netto_weigth_f', 'id_factory', 'id_pile', 'batch',
                    'delivery_order', 'tgl_hauling', 'time_hauling', 'shift', 'batch_g',
                    'kode_batch_g', 'left_date', 'new_scci', 'new_scci_sub', 'new_kode_batch_scci',
                    'scci_order', 'new_awk', 'new_awk_sub', 'new_kode_batch_awk', 'new_batch_awk_pulp',
                    'awk_order', 'type_selling', 'date_wb', 'sale_adjust', 'sale_dome'
                ], batch_size=300)

    except Exception as e:
        errors.append(f"Transaction failed: {str(e)}")

    # Buat laporan import
    taskImports.objects.create(
        task_id=import_selling_hpal.request.id, 
        successful_imports=successful_imports,
        failed_imports=len(errors),
        duplicate_imports=duplicate_imports,
        errors="\n".join(errors) if errors else None,
        duplicates="\n".join(duplicates) if duplicates else None,
        file_name=original_file_name,
        destination='Selling HPAL'
    )

    if errors or duplicates:
        return {'message': 'Import completed with some errors or duplicates', 'errors': errors, 'duplicates': duplicates}
    else:
        return {'message': 'Import successful'}

