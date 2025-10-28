from celery import shared_task
import pandas as pd
import re
from django.db.models.functions import Trim
from datetime import datetime
from django.db import transaction
from ..models.task_model import taskImports
from ..models.selling_barging import SellingBarging
from ..models.materials import Material
from ..models.stock_factories import StockFactories
from ..models.source_model import SourceMinesDumping,SourceMinesDome
from ..models.master_barge import BargeUnits,BargePort

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
    
def safe_parse_time(val):
    if pd.isna(val):
        return None
    val = str(val).strip()
    for fmt in ("%H:%M", "%H:%M:%S", "%H:%M:%S.%f"):
        try:
            parsed = datetime.strptime(val, fmt).time()
            # buang detik & microseconds
            return parsed.replace(second=0, microsecond=0)
        except ValueError:
            continue
    return None

@shared_task(name='kqms.task.import_selling_barge.import_selling')
def import_selling(file_path, original_file_name):
    df = pd.read_excel(file_path)
    errors = []
    list_new = []
    successful_imports = 0

    # Konversi datetime dan waktu
    df['date_barging_in']  = pd.to_datetime(df['date_barging_in'], errors='coerce').dt.date
    df['date_hauling']     = pd.to_datetime(df['date_hauling'], errors='coerce').dt.date
    df['date_barging_out'] = pd.to_datetime(df['date_barging_out'], errors='coerce').dt.date
    df['date_barging_load']= pd.to_datetime(df['date_barging_load'], errors='coerce').dt.date
    # df['time']              = pd.to_datetime(df['time'], errors='coerce')
    # df['time']              = df['time'].apply(lambda x: x.time() if pd.notna(x) else None)
    
    df['time'] = df['time'].apply(safe_parse_time)  # type: ignore

    # Lookup dictionaries
    material_dict   = dict(Material.objects.annotate(trimmed=Trim('nama_material')).values_list('trimmed', 'id'))
    pile_dict       = dict(SourceMinesDome.objects.annotate(trimmed=Trim('pile_id')).values_list('trimmed', 'id'))
    stockpile_dict  = dict(SourceMinesDome.objects.annotate(trimmed=Trim('pile_id')).values_list('trimmed', 'id'))
    factory_dict    = dict(StockFactories.objects.annotate(trimmed=Trim('factory_stock')).values_list('trimmed', 'id'))
    barge_dict      = dict(BargeUnits.objects.annotate(trimmed=Trim('barge_code')).values_list('trimmed', 'id'))
    port_dict       = dict(BargePort.objects.annotate(trimmed=Trim('port_name')).values_list('trimmed', 'port_name'))


    try:
       with transaction.atomic():
        for _, row in df.iterrows():
            # Lookup nama → ID
            nama_material   = str(row.get('material', '')).strip()
            pile_name       = str(row.get('dome_ori', '')).strip()
            stockpile_name  = str(row.get('stockpile', '')).strip()
            factory_name    = str(row.get('buyer', '')).strip()
            barge_code_str  = str(row.get('barge_code', '')).strip()
            load_loc_name   = str(row.get('barge_load_loc', '')).strip()
            unload_loc_name = str(row.get('barge_unload_loc', '')).strip()

            validated_load_loc   = port_dict.get(load_loc_name, load_loc_name)
            validated_unload_loc = port_dict.get(unload_loc_name, unload_loc_name)


            id_material     = material_dict.get(nama_material)
            material_ori    = material_dict.get(nama_material)
            id_pile         = pile_dict.get(pile_name)
            id_stockpile    = stockpile_dict.get(stockpile_name)
            id_factory      = factory_dict.get(factory_name)
            id_barge        = barge_dict.get(barge_code_str)

            # Ambil nilai yang dibutuhkan dari row
            type_selling    = str(row.get('sale_code', '')).strip()
            code_lot        = str(row.get('code_lot', '')).strip()
            batch           = str(row.get('sub_lot', '')).strip()
            truck           = str(row.get('no_truck', '')).strip()
            group           = str(row.get('group', '')).strip()
            # Buat kode batch
            # code_batch_in     = f"{type_selling}{id_material}{code_lot}{batch}"
            # code_batch_ex     = f"{type_selling}{id_material}Split_CAR{code_lot}{batch}"
            # code_batch_pulp   = f"{type_selling}{code_lot}Split_CAR{batch}"

            # Mapping adjust_sale ke material & type_selling
            if row['adjust_sale'] == 'RKEF':
                material_name = 'SAP'
                type_selling  = 'SAS'
                type_monitoring  = 'SAS_CKS'
            elif row['adjust_sale'] == 'HPAL':
                material_name = 'LIM'
                type_selling  = 'LIS'
                type_monitoring  = 'LIS_CKS'
            else:
                material_name = row['material']   # default material asli
                # type_selling tetap pakai dari row['sale_code']
                type_selling = row['sale_code']

            # Ambil id_material dari tabel Materials (aman tanpa error)
            id_material = (
                Material.objects.filter(nama_material=material_name)
                .values_list('id', flat=True)
                .first()
            )

            # Kalau tidak ada di tabel, kasih default 0 (atau None sesuai kebutuhan)
            if not id_material:
                id_material = 0   # <- default supaya tidak error

            # Buat kode batch
            code_batch_in   = f"{type_selling}{id_material}{code_lot}{batch}"
            code_monitoring = f"{type_monitoring}{id_material}{code_lot}{batch}{group}"
            code_batch_ex   = f"{type_selling}{id_material}Split_CAR{code_lot}{batch}"
            code_batch_pulp = f"{type_selling}{code_lot}Split_CAR{batch}"
          

            list_new.append(SellingBarging(
                date_barge_in       = row['date_barging_in'],
                date_hauling        = row['date_hauling'],
                time_hauling        = row['time'],
                shift               = row['shift'],
                date_barging        = row['date_barging_load'],
                barge_code          = id_barge,
                barging_load_loc    = validated_load_loc,
                barging_unload_loc  = validated_unload_loc,
                unit_code           = truck,
                type_selling        = type_selling,
                id_material         = material_ori,
                id_pile             = id_pile,
                id_stockpile        = id_stockpile,
                id_factory          = id_factory,
                tonnage             = row.get('tonnage'),
                batch               = batch,
                # nota                = None,
                code_inc            = row.get('group'),
                code_sub            = batch,
                code_batch_in       = code_batch_in,
                code_batch_ex       = code_batch_ex,
                code_batch_pulp     = code_batch_pulp,
                surv_order          = row.get('surv_order'),
                code_monitoring     = code_monitoring,
                code_lot            = code_lot,
                date_barge_out      = row['date_barging_out'],
                sale_adjust         = row['adjust_sale'],
                direct              = row['direct'],
                sale_dome           = 'Continue',
            ))
            successful_imports += 1

        if list_new:
            SellingBarging.objects.bulk_create(list_new, batch_size=300)


    except Exception as e:
        errors.append(f"Transaction failed: {str(e)}")

    # Simpan laporan task
    taskImports.objects.create(
        task_id=import_selling.request.id,
        successful_imports=successful_imports,
        failed_imports=len(errors),
        duplicate_imports=0,
        errors="\n".join(errors) if errors else None,
        duplicates=None,
        file_name=original_file_name,
        destination='Selling Barge'
    )

    if errors:
        return {'message': 'Import completed with some errors', 'errors': errors}
    return {'message': 'Import completed successfully'}
