# from celery import shared_task
# import pandas as pd
# import re
# from django.db.models import F, Func
# from datetime import datetime
# from django.db import transaction
# from ..models.task_model import taskImports
# from ..models.task_model import UploadLog
# from ..models.selling_data import SellingProductions
# from ..models.materials import Material
# from ..models.stock_factories import StockFactories
# from ..models.selling_dome import SellingDomeTemp
# from ..models.selling_stock import SellingStockTemp
# from ..models.mine_units import MineUnits
# from ..models.source_model import SourceMinesDumping,SourceMinesDome
# from django.db.models.functions import Trim

# # Fungsi untuk membersihkan data numerik
# def clean_numeric(value):
#     try:
#         if pd.isna(value):  # Cek jika NaN atau None
#             return 0
#         if isinstance(value, str):
#             value = value.strip()  # Menghapus spasi di awal dan akhir
#             if value == '':  # Jika string kosong
#                 return None
#             # Menghapus karakter selain angka dan titik desimal
#             value = re.sub(r"[^0-9.<>]", "", value)
#             if value.startswith('<') or value.startswith('>'):
#                 value = value[1:]  # Menghapus tanda '<' atau '>'
#             if re.match(r"^\d+(\.\d+)?$", value):  # Cek jika angka valid
#                 return float(value)
#             return 0  # Jika tidak valid, kembalikan 0
#         return value if isinstance(value, (int, float)) else 0
#     except Exception as e:
#         print(f"Error processing value: {value}, Error: {e}")
#         return 0  # Kembalikan 0 jika terjadi error

# @shared_task
# def import_selling_rkef(file_path, original_file_name):
#     df = pd.read_excel(file_path)
#     errors = []
#     duplicates = []
#     list_objects = []
#     successful_imports = 0
#     duplicate_imports = 0
#     list_new = []
#     list_update = []

#     df['date_gwt']      = df['date_gwt'].fillna(pd.Timestamp('1900-01-01')).dt.strftime('%Y-%m-%d %H:%M:%S')
#     df['date_ewt']      = df['date_ewt'].fillna(pd.Timestamp('1900-01-01')).dt.strftime('%Y-%m-%d %H:%M:%S')
#     df['load_date']     = pd.to_datetime(df['load_date']).dt.date
#     df['weighing_date'] = pd.to_datetime(df['weighing_date']).dt.date


#     # Buat dictionary dari Tabel untuk pencarian ID berdasarkan nama
#     material_dict   = dict(Material.objects.annotate(trimmed_material=Trim('nama_material')).values_list('trimmed_material', 'id'))
#     dome_dict       = dict(SourceMinesDome.objects.annotate(trimmed_dome=Trim('pile_id')).values_list('trimmed_dome', 'id'))
#     factory_dict    = dict(StockFactories.objects.annotate(trimmed_fact=Trim('factory_stock')).values_list('trimmed_fact', 'id'))
#     dome_temp_dict  = dict(SellingDomeTemp.objects.annotate(trim_dome=Trim('temp_dome')).values_list('trim_dome', 'id'))
#     stock_temp_dict = dict(SellingStockTemp.objects.annotate(trim_stock=Trim('temp_stock')).values_list('trim_stock', 'id'))

#     # Menentukan kolom yang perlu dibersihkan
#     numeric_columns = [
#         'netto', 'gross', 'empty'
#         ]
        
#     # Kolom yang diinginkan tetap kosong jika kosong
#     empty_columns = [
#             'stockpile_temp','dome_temp','buyer','product_code','scci_gps', 'scci_sl','awk_inc','awk_sl','nota'
#         ]

#     for col in numeric_columns:
#             if col in df.columns:
#                 df[col] = df[col].apply(clean_numeric)

#     # Untuk kolom yang perlu tetap kosong jika kosong
#     for col in empty_columns:
#             if col in df.columns:
#                 df[col] = df[col].apply(lambda x: None if pd.isna(x) or x == '' else x)

#     # Ambil semua nota yang sudah ada di database dalam dictionary untuk pencarian cepat
#     existing_data = {obj.haulage_code: obj for obj in SellingProductions.objects.all()}

#     try:
#         # Mulai transaksi untuk memastikan rollback jika terjadi error
#         with transaction.atomic():
#             for index, row in df.iterrows():
#                 haulage_code    = row['haulage_code']  
#                 existing_entry  = existing_data.get(haulage_code)
#                 load_date       = row['load_date']
#                 shift           = row['shift']
#                 load_code       = row['load_code']
#                 truck           = row['no_truck']
#                 sale_code       = row['sale_code']
#                 sale_type       = row['type_sale']
#                 nama_material   = row['material']
#                 dome            = row['dome_ori']
#                 stockpile_temp  = row['stockpile_temp']
#                 dome_temp       = row['dome_temp']
#                 buyer           = row['buyer']
#                 delivery_order  = row['product_code']
#                 new_scci        = row['scci_gps']
#                 scci_sl         = row['scci_sl']
#                 new_awk         = row['awk_inc']
#                 awk_sl          = row['awk_sl']
#                 weighing_date   = row['weighing_date']
#                 empety_weigth_f = row['empty']      
#                 fill_weigth_f   = row['gross']   
#                 netto_weigth_f  = row['netto']   
#                 nota            = row['nota']
#                 date_gwt        = row['date_gwt']
#                 date_ewt        = row['date_ewt']

#                 # Cari ID dari Model berdasarkan nama
#                 id_material       = material_dict.get(nama_material, None) 
#                 id_pile           = dome_dict.get(dome, None) 
#                 id_stock_temp     = stock_temp_dict.get(stockpile_temp, None)  
#                 id_dome_temp      = dome_temp_dict.get(dome_temp, None)  
#                 id_factory        = factory_dict.get(buyer, None)  

#                 # Gabungkan Kode
#                 new_kode_batch_scci = f"{sale_code}Split_SCCI{str(id_material) if id_material else ''}{delivery_order}{scci_sl if scci_sl else ''}"
#                 new_kode_batch_awk  = f"{sale_code}Split_AWK{str(id_material) if id_material else ''}{delivery_order}{awk_sl if awk_sl else ''}"
#                 new_batch_awk_pulp  = f"{sale_code}Split_AWK{delivery_order}{awk_sl if awk_sl else ''}"
#                 scci_order   = 'Yes'
#                 awk_order    = 'Yes'
#                 sale_dome    = 'Continue'
#                 time_hauling = '00:00:00'

#                 if weighing_date:  # Pastikan tanggal bukan None
#                     date_str  = weighing_date.strftime('%Y-%m-%d')
#                     date_obj  = datetime.strptime(date_str, '%Y-%m-%d')
#                     left_date = date_obj.day
#                 else:
#                     left_date = None

#                 # Cek duplikat berdasarkan kriteria
#                 if existing_entry:
#                     existing_entry.nota=nota
#                     existing_entry.timbang_isi=date_gwt
#                     existing_entry.timbang_kosong=date_ewt
#                     existing_entry.id_material=id_material
#                     existing_entry.unit_code=truck
#                     existing_entry.delivery_order =delivery_order
#                     existing_entry.empety_weigth_f=empety_weigth_f
#                     existing_entry.fill_weigth_f=fill_weigth_f
#                     existing_entry.netto_weigth_f=netto_weigth_f
#                     existing_entry.id_factory=id_factory
#                     existing_entry.id_pile=id_pile
#                     existing_entry.id_stock_temp=id_stock_temp
#                     existing_entry.id_dome_temp=id_dome_temp
#                     existing_entry.tgl_hauling=load_date
#                     existing_entry.time_hauling=time_hauling
#                     existing_entry.shift=shift
#                     existing_entry.left_date=left_date
#                     existing_entry.new_scci=new_scci
#                     existing_entry.new_scci_sub=scci_sl
#                     existing_entry.new_kode_batch_scci=new_kode_batch_scci
#                     existing_entry.scci_order=scci_order
#                     existing_entry.new_awk=new_awk
#                     existing_entry.new_awk_sub=awk_sl
#                     existing_entry.new_kode_batch_awk=new_kode_batch_awk
#                     existing_entry.new_batch_awk_pulp=new_batch_awk_pulp
#                     existing_entry.awk_order=awk_order
#                     existing_entry.type_selling=sale_type
#                     existing_entry.load_code=load_code
#                     existing_entry.haulage_code=haulage_code
#                     existing_entry.date_wb=weighing_date
#                     existing_entry.sale_adjust='RKEF'
#                     existing_entry.sale_dome=sale_dome

#                     list_update.append(existing_entry)
#                     duplicate_imports += 1
#                 else:
#                     list_new.append(SellingProductions(
#                         nota=nota,
#                         timbang_isi=date_gwt,
#                         timbang_kosong=date_ewt,
#                         id_material=id_material,
#                         unit_code=truck,
#                         delivery_order =delivery_order,
#                         empety_weigth_f=empety_weigth_f,
#                         fill_weigth_f=fill_weigth_f,
#                         netto_weigth_f=netto_weigth_f,
#                         id_factory=id_factory,
#                         id_pile=id_pile,
#                         id_stock_temp=id_stock_temp,
#                         id_dome_temp=id_dome_temp,
#                         tgl_hauling=load_date,
#                         time_hauling=time_hauling,
#                         shift=shift,
#                         left_date=left_date,
#                         new_scci=new_scci,
#                         new_scci_sub=scci_sl,
#                         new_kode_batch_scci=new_kode_batch_scci,
#                         scci_order=scci_order,
#                         new_awk=new_awk,
#                         new_awk_sub=awk_sl,
#                         new_kode_batch_awk=new_kode_batch_awk,
#                         new_batch_awk_pulp=new_batch_awk_pulp,
#                         awk_order=awk_order,
#                         type_selling=sale_type,
#                         load_code=load_code,
#                         haulage_code=haulage_code,
#                         date_wb=weighing_date,
#                         sale_adjust='RKEF',
#                         sale_dome=sale_dome,
#                     ))
                       
#                     successful_imports += 1
     
#             # Bulk Insert Semua Data Baru
#             if list_new:
#                 SellingProductions.objects.bulk_create(list_new, batch_size=300)

#             # Bulk Update Data Lama
#             if list_update:
#                 SellingProductions.objects.bulk_update(list_update, [
#                     'timbang_isi', 'timbang_kosong', 'id_material', 'empety_weigth_f',
#                     'fill_weigth_f', 'netto_weigth_f', 'id_factory', 'id_pile','id_stock_temp','id_dome_temp',
#                     'batch', 'delivery_order', 'tgl_hauling', 'time_hauling', 'shift', 'batch_g',
#                     'kode_batch_g', 'left_date', 'new_scci', 'new_scci_sub', 'new_kode_batch_scci',
#                     'scci_order', 'new_awk', 'new_awk_sub', 'new_kode_batch_awk', 'new_batch_awk_pulp',
#                     'awk_order', 'type_selling', 'date_wb', 'sale_adjust', 'sale_dome'
#                 ], batch_size=300)
#     except Exception as e:
#             errors.append(f"Transaction failed: {str(e)}")

#     # Buat laporan import
#     taskImports.objects.create(
#         task_id             =import_selling_rkef.request.id, 
#         successful_imports  =successful_imports,
#         failed_imports      =len(errors),
#         duplicate_imports   =duplicate_imports,
#         errors              ="\n".join(errors) if errors else None,
#         duplicates          ="\n".join(duplicates) if duplicates else None,
#         file_name           =original_file_name,
#         destination         ='Selling RKEF',
#     )

#     if errors or duplicates:
#         return {'message': 'Import completed with some errors or duplicates', 'errors': errors, 'duplicates': duplicates}
#     else:
#         return {'message': 'Import successful'}
