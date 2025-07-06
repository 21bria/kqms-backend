# utils.py

from datetime import date,datetime
from django.db.models import Max
from ..models.sample_production import SampleProductions
from ..models.ore_productions import OreProductions
from ..models.merge_stock import domeMerge,stockpileMerge
from ..models.mine_productions import mineProductions,mineQuickProductions
import json
from ..models.waybill_model import Waybills
from datetime import datetime, date
from django.db.models import Max
from datetime import datetime

def clean_string(value):
    """Menghapus spasi berlebih dari string, jika bukan string, biarkan apa adanya."""
    return value.strip() if isinstance(value, str) else value

def safe_float(value):
    try:
        return float(value) if value and str(value).replace('.', '', 1).isdigit() else 0.0
    except:
        return 0.0
    
def validate_year(value):
    if value is None:  # Jika None, kembalikan None
        return None
    try:
        year = int(value)
        if 1900 <= year <= datetime.now().year:  # Pastikan dalam rentang wajar
            return year
    except ValueError:
        pass
    return None

def validate_month(value):
    if value is None:  # Jika None, kembalikan None
        return None
    try:
        month = int(value)
        if 1 <= month <= 12:  # Pastikan bulan antara 1 dan 12
            return month
    except ValueError:
        pass
    return None

class NaNEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, float) and (obj != obj):  # Memeriksa NaN
            return None
        return super().default(obj)

def get_month_label(month_number):
    month_labels = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr',
        5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug',
        9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }
    return month_labels.get(month_number, '')


def generate_sample_number():
    today = date.today()
    formatted_date = today.strftime('%y%m%d')

    # Ambil nomor sampel terakhir untuk hari ini
    max_kd = SampleProductions.objects.filter(created_at__date=today).aggregate(Max('no_sample'))
    last_sample_number = max_kd['no_sample__max']

    if last_sample_number:
        kd = int(last_sample_number[6:]) + 1
    else:
        kd = 1

    formatted_kd = '{:04}'.format(kd)

    return f'{formatted_date}{formatted_kd}'

def generate_ore_number():
    today = date.today()
    formatted_date = today.strftime('%y%m%d')

    # Ambil nomor pds terakhir untuk hari ini
    max_kd = OreProductions.objects.filter(created_at__date=today).aggregate(Max('no_production'))
    last_pds_number = max_kd['no_production__max']

    if last_pds_number:
        kd = int(last_pds_number[6:]) + 1
    else:
        kd = 1

    formatted_kd = '{:04}'.format(kd)

    return f'{formatted_date}{formatted_kd}'

def generate_production_number():
    today = date.today()
    formatted_date = today.strftime('%y%m%d')

    # Ambil nomor pds terakhir untuk hari ini
    max_kd = mineProductions.objects.filter(created_at__date=today).aggregate(Max('no_production'))
    last_pds_number = max_kd['no_production__max']

    if last_pds_number:
        kd = int(last_pds_number[6:]) + 1
    else:
        kd = 1

    formatted_kd = '{:04}'.format(kd)

    return f'{formatted_date}{formatted_kd}'

def generate_quick_production():
    today = date.today()
    formatted_date = today.strftime('%y%m%d')

    # Ambil nomor pds terakhir untuk hari ini
    max_kd = mineQuickProductions.objects.filter(created_at__date=today).aggregate(Max('no_production'))
    last_pds_number = max_kd['no_production__max']

    if last_pds_number:
        kd = int(last_pds_number[6:]) + 1
    else:
        kd = 1

    formatted_kd = '{:04}'.format(kd)

    return f'{formatted_date}{formatted_kd}'

def generate_dome_merger():
    today = date.today()
    formatted_date = today.strftime('%y%m%d')

    # Ambil nomor dome terakhir untuk hari ini
    max_kd = domeMerge.objects.filter(created_at__date=today).aggregate(Max('ref_id'))
    last_number = max_kd['ref_id__max']

    print(f"Last number: {last_number}")  # Debugging

    if last_number and last_number.startswith(formatted_date):
        try:
            kd = int(last_number[6:]) + 1  # Increment nomor terakhir
        except (ValueError, IndexError):
            kd = 1  # Kembali ke 1 jika ada kesalahan
    else:
        kd = 1  # Reset ke 1 jika tidak ada entri untuk hari ini

    formatted_kd = '{:04}'.format(kd)  # Format menjadi 4 digit
    new_number = f'{formatted_date}{formatted_kd}'

    print(f"Generated new number: {new_number}")  # Debugging

    return new_number

def generate_stockpile_merger():
    today = date.today()
    formatted_date = today.strftime('%y%m%d')

    # Ambil nomor dome terakhir untuk hari ini
    max_kd = stockpileMerge.objects.filter(created_at__date=today).aggregate(Max('ref_id'))
    last_number = max_kd['ref_id__max']

    print(f"Last number: {last_number}")  # Debugging

    if last_number and last_number.startswith(formatted_date):
        try:
            kd = int(last_number[6:]) + 1  # Increment nomor terakhir
        except (ValueError, IndexError):
            kd = 1  # Kembali ke 1 jika ada kesalahan
    else:
        kd = 1  # Reset ke 1 jika tidak ada entri untuk hari ini

    formatted_kd = '{:04}'.format(kd)  # Format menjadi 4 digit
    new_number = f'{formatted_date}{formatted_kd}'

    print(f"Generated new number: {new_number}")  # Debugging

    return new_number

# def generate_unique_approval(team, date_production=None):
#     # Menggunakan tanggal hari ini jika date_production tidak diberikan
#     if date_production is None:
#         today = date.today()
#         date_production = today.strftime('%Y-%m-%d')  # Mengambil tanggal hari ini

#     # Mengonversi string date_production ke objek date
#     date_obj = datetime.strptime(date_production, '%Y-%m-%d').date()  # Hanya ambil tanggal
#     formatted_date = date_obj.strftime('%y%m%d')

#     # Ambil nomor terakhir berdasarkan updated_at untuk hari ini
#     max_kd = Workflow.objects.filter(updated_at__date=date_obj, team=team).aggregate(Max('register'))
#     last_number = max_kd['register__max']

#     print(f"Last number: {last_number}")  # Debugging

#     # Menghitung nomor urut
#     # if last_number and last_number.startswith(f"MDK/{formatted_date}/"):
#     if last_number and len(last_number.split('/')) >= 3:
#         try:
#             # Mengambil angka urut dari nomor terakhir
#             kd = int(last_number.split('/')[2]) + 1  # Ambil substring angka urut di tengah
#         except (ValueError, IndexError):
#             kd = 1  # Kembali ke 1 jika ada kesalahan
#     else:
#         kd = 1  # Reset ke 1 jika tidak ada entri untuk hari ini

#     # Format nomor urut menjadi 4 digit
#     formatted_kd = f"{kd:04d}"  
#     new_number = f"MDK/{formatted_date}/{formatted_kd}/{team}"  # Format sesuai kebutuhan
#     print(f"Generated new number: {new_number}")  # Debugging
#     return new_number

def generate_waybill_number(team, date_delivery=None):
    if date_delivery is None:
        today = date.today()
        date_delivery = today.strftime('%Y-%m-%d')

    date_obj = datetime.strptime(date_delivery, '%Y-%m-%d').date()
    formatted_date = date_obj.strftime('%y%m%d')

    max_kd = Waybills.objects.filter(
        created_at__date=date_obj).aggregate(Max('waybill_number'))

    last_number = max_kd['waybill_number__max']

    if last_number and len(last_number.split('/')) >= 3:
        try:
            kd = int(last_number.split('/')[1]) + 1
        except (ValueError, IndexError):
            kd = 1
    else:
        kd = 1

    formatted_kd = f"{kd:04d}"
    new_number = f"{formatted_date}/{formatted_kd}/{team.upper()}"
    return new_number

