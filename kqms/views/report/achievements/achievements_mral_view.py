from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render
from django.db import connections
import re,json
from django.utils.html import escape
from ....utils.db_utils import get_db_vendor
 # Memanggil fungsi utility
db_vendor = get_db_vendor('kqms_db')

@login_required
def achievement_mral_page(request):

    return render(request, 'admin-mgoqa/achievement/achievement_mral.html')

@login_required
def stockpile_mral_page(request):
    return render(request, 'admin-mgoqa/achievement/stockpile_mral.html')

@login_required
def source_mral_page(request):
    return render(request, 'admin-mgoqa/achievement/source_mral.html')

@login_required
def to_stockpile_mral_page(request):
    return render(request, 'admin-mgoqa/achievement/source_stockpile_mral.html')

@login_required
def to_dome_mral_page(request):
    return render(request, 'admin-mgoqa/achievement/source_dome_mral.html')


# Fungsi untuk sanitasi input
def sanitize_input(value):
    if value is None:
        return None
    return escape(re.sub(r"[;'\"]", "", str(value)))


@login_required
def achievement_mral(request):
    start_date     = sanitize_input(request.GET.get('startDate'))
    end_date       = sanitize_input(request.GET.get('endDate'))
    materialFilter = sanitize_input(request.GET.get('materialFilter'))
    cutDate        = sanitize_input(request.GET.get('cutDate'))
    bulanFilter    = sanitize_input(request.GET.get('bulanFilter'))
    tahunFilter    = sanitize_input(request.GET.get('tahunFilter'))
    sourceFilter   = json.loads(request.GET.get('sourceFilter', '[]'))
    areaFilter     = sanitize_input(request.GET.get('areaFilter'))
    pointFilter    = sanitize_input(request.GET.get('pointFilter'))

    sourceFilter = [sanitize_input(source) for source in sourceFilter if source]

    page = int(request.GET.get('page', 1))
    per_page = 1000
    offset = (page - 1) * per_page

    count_query = """
        SELECT COUNT(*) FROM details_mral
        WHERE stockpile <> 'Temp-Rompile_KM09'
    """

    if materialFilter:
        count_query += f" AND nama_material = '{materialFilter}'"
    if cutDate:
        count_query += f" AND tgl_production <= '{cutDate}'"
    if start_date and end_date:
        count_query += f" AND tgl_production BETWEEN '{start_date}' AND '{end_date}'"
    if bulanFilter and tahunFilter:
        if db_vendor == 'postgresql':
            count_query += f" AND EXTRACT(MONTH FROM tgl_production) = {bulanFilter} AND EXTRACT(YEAR FROM tgl_production) = {tahunFilter}"
        else:  # SQL Server
            count_query += f" AND MONTH(tgl_production) = {bulanFilter} AND YEAR(tgl_production) = {tahunFilter}"
    if tahunFilter:
        if db_vendor == 'postgresql':
            count_query += f" AND EXTRACT(YEAR FROM tgl_production) = {tahunFilter}"
        else:
            count_query += f" AND YEAR(tgl_production) = {tahunFilter}"
    if sourceFilter:
        count_query += f" AND prospect_area IN ({', '.join(f'\'{source}\'' for source in sourceFilter)})"
    if areaFilter:
        count_query += f" AND stockpile = '{areaFilter}'"
    if pointFilter:
        count_query += f" AND pile_id = '{pointFilter}'"

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(count_query)
        result = cursor.fetchone()
        total_data = result[0] if result else 0

    if db_vendor == 'postgresql':
        sql_query = """
            SELECT 
                TRIM(stockpile) AS stockpile,
                TRIM(pile_id) AS pile_id,
                TRIM(nama_material) AS nama_material,
                SUM(tonnage) AS total_ore,
                SUM(CASE WHEN batch_status = 'Incomplete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS incomplete,
                SUM(CASE WHEN batch_status = 'Complete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS unprepared,
                SUM(CASE WHEN MRAL_Ni IS NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS unreleased,
                SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS released,
                CONCAT(
                    ROUND(( COALESCE(SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) * 100.0 / NULLIF(SUM(tonnage), 0), 0) )::numeric, 0),'%') AS recovery,
                COALESCE(ROUND((SUM(tonnage * MRAL_Ni) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0))::numeric, 2), 0) as ni,
                COALESCE(ROUND((SUM(tonnage * MRAL_Co) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0))::numeric, 2), 0) as co,
                COALESCE(ROUND((SUM(tonnage * MRAL_Fe2O3) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0))::numeric, 2), 0) as fe2o3,
                COALESCE(ROUND((SUM(tonnage * MRAL_Fe) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0))::numeric, 2), 0) as fe,
                COALESCE(ROUND((SUM(tonnage * MRAL_MgO) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0))::numeric, 2), 0) as mgo,
                COALESCE(ROUND((SUM(tonnage * MRAL_SiO2) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0))::numeric, 2), 0) as sio2,
                ROUND(COALESCE((SUM(tonnage * MRAL_SiO2) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)) /
                (NULLIF(SUM(tonnage * MRAL_MgO) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0), 0) + 0.000001), 0)::numeric, 2) as sm
            FROM details_mral
            WHERE stockpile <> 'Temp-Rompile_KM09'
        """
    else:
        raise ValueError("Unsupported database vendor.")

    if materialFilter:
        sql_query += f" AND nama_material = '{materialFilter}'"
    if cutDate:
        sql_query += f" AND tgl_production <= '{cutDate}'"
    if start_date and end_date:
        sql_query += f" AND tgl_production BETWEEN '{start_date}' AND '{end_date}'"
    if bulanFilter and tahunFilter:
        if db_vendor == 'postgresql':
            sql_query += f" AND EXTRACT(MONTH FROM tgl_production) = {bulanFilter} AND EXTRACT(YEAR FROM tgl_production) = {tahunFilter}"
        else:
            sql_query += f" AND MONTH(tgl_production) = {bulanFilter} AND YEAR(tgl_production) = {tahunFilter}"
    if tahunFilter:
        if db_vendor == 'postgresql':
            sql_query += f" AND EXTRACT(YEAR FROM tgl_production) = {tahunFilter}"
        else:
            sql_query += f" AND YEAR(tgl_production) = {tahunFilter}"
    if sourceFilter:
        sql_query += f" AND prospect_area IN ({', '.join(f'\'{source}\'' for source in sourceFilter)})"
    if areaFilter:
        sql_query += f" AND stockpile = '{areaFilter}'"
    if pointFilter:
        sql_query += f" AND pile_id = '{pointFilter}'"

    sql_query += " GROUP BY stockpile, pile_id, nama_material"
    sql_query += f" LIMIT {per_page} OFFSET {offset};"

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(sql_query)
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            sql_data = []


    more_data = len(sql_data) == per_page
    total_pages = (total_data // per_page) + (1 if total_data % per_page > 0 else 0)

    grandTotalOre = grandTotalIncomplete = grandTotalUnprepared = grandTotalUnRelease = grandTotalRelease = 0
    data_Ni = data_Co = data_Fe2O3 = data_Fe = data_Mgo = data_SiO2 = []

    for row in sql_data:
        grandTotalOre += float(row['total_ore'])
        grandTotalIncomplete += float(row['incomplete'])
        grandTotalUnprepared += float(row['unprepared'])
        grandTotalUnRelease += float(row['unreleased'])
        grandTotalRelease += float(row['released'])

        data_Ni.append(row['released'] * float(row['ni']))
        data_Co.append(row['released'] * float(row['co']))
        data_Fe2O3.append(row['released'] * float(row['fe2o3']))
        data_Fe.append(row['released'] * float(row['fe']))
        data_Mgo.append(row['released'] * float(row['mgo']))
        data_SiO2.append(row['released'] * float(row['sio2']))

    def sum_product(data_array):
        return sum(data_array)

    sumResults = {
        'Ni': sum_product(data_Ni) / grandTotalRelease if grandTotalRelease else 0,
        'Co': sum_product(data_Co) / grandTotalRelease if grandTotalRelease else 0,
        'Fe2O3': sum_product(data_Fe2O3) / grandTotalRelease if grandTotalRelease else 0,
        'Fe': sum_product(data_Fe) / grandTotalRelease if grandTotalRelease else 0,
        'Mgo': sum_product(data_Mgo) / grandTotalRelease if grandTotalRelease else 0,
        'SiO2': sum_product(data_SiO2) / grandTotalRelease if grandTotalRelease else 0,
    }

    return JsonResponse({
        'data': sql_data,
        'grand_totals': {
            'total_ore': grandTotalOre,
            'incomplete': grandTotalIncomplete,
            'unprepared': grandTotalUnprepared,
            'unreleased': grandTotalUnRelease,
            'released': grandTotalRelease
        },
        'sum_results': sumResults,
        'pagination': {
            'more': more_data,
            'total_pages': total_pages,
            'current_page': page,
            'total_data': total_data
        }
    })

@login_required
def stockpile_mral(request):
    # Ambil dan sanitasi input dari request
    start_date     = sanitize_input(request.GET.get('startDate'))
    end_date       = sanitize_input(request.GET.get('endDate'))
    materialFilter = sanitize_input(request.GET.get('materialFilter'))
    cutDate        = sanitize_input(request.GET.get('cutDate'))
    bulanFilter    = sanitize_input(request.GET.get('bulanFilter'))
    tahunFilter    = sanitize_input(request.GET.get('tahunFilter'))
    sourceFilter   = json.loads(request.GET.get('sourceFilter', '[]'))
    areaFilter     = sanitize_input(request.GET.get('areaFilter'))
    pointFilter    = sanitize_input(request.GET.get('pointFilter'))

    # sanitize_input: Fungsi ini membersihkan karakter yang berpotensi menyebabkan SQL injection.
    # Filter list sourceFilter
    sourceFilter = [sanitize_input(source) for source in sourceFilter if source]
   # Pagination setup
    page = int(request.GET.get('page', 1))
    per_page = 1000
    offset = (page - 1) * per_page

    # Query untuk menghitung total data
    count_query = """
        SELECT COUNT(*) FROM details_mral
        WHERE stockpile <> 'Temp-Rompile_KM09'
    """
    
    # Menambahkan kondisi ke count_query berdasarkan input
    if materialFilter:
        count_query += f" AND nama_material = '{materialFilter}'"
    if cutDate:
        count_query += f" AND tgl_production <= '{cutDate}'"
    if start_date and end_date:
        count_query += f" AND tgl_production BETWEEN '{start_date}' AND '{end_date}'"
    if bulanFilter and tahunFilter:
        if db_vendor == 'postgresql':
            count_query += f" AND EXTRACT(MONTH FROM tgl_production) = {bulanFilter} AND EXTRACT(YEAR FROM tgl_production) = {tahunFilter}"
        else:  # SQL Server
            count_query += f" AND MONTH(tgl_production) = {bulanFilter} AND YEAR(tgl_production) = {tahunFilter}"
    if tahunFilter:
        if db_vendor == 'postgresql':
            count_query += f" AND EXTRACT(YEAR FROM tgl_production) = {tahunFilter}"
        else:
            count_query += f" AND YEAR(tgl_production) = {tahunFilter}"
    if sourceFilter:
        count_query += f" AND prospect_area IN ({', '.join(f'\'{source}\'' for source in sourceFilter)})"
    if areaFilter:
        count_query += f" AND stockpile = '{areaFilter}'"
    if pointFilter:
        count_query += f" AND pile_id = '{pointFilter}'"

    # Hitung total data
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(count_query)
        result = cursor.fetchone()
        total_data = result[0] if result else 0

    # Query berdasarkan database
    if db_vendor == 'postgresql':
        sql_query = f"""
                SELECT 
                    TRIM(stockpile) AS stockpile,
                    TRIM(nama_material) AS nama_material,
                    SUM(tonnage) AS total_ore,
                    SUM(CASE WHEN batch_status = 'Incomplete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS incomplete,
                    SUM(CASE WHEN batch_status = 'Complete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS unprepared,
                    SUM(CASE WHEN MRAL_Ni IS NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS unreleased,
                    SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS released,
                    CONCAT(
                        ROUND(( COALESCE(SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) * 100.0 / NULLIF(SUM(tonnage), 0), 0) )::numeric, 0),'%') AS recovery,
                    COALESCE(ROUND((
                        SUM(tonnage * MRAL_Ni) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                    )::numeric, 2), 0) as ni,
                    COALESCE(ROUND((
                        SUM(tonnage * MRAL_Co) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                    )::numeric, 2), 0) as co,
                    COALESCE(ROUND((
                        SUM(tonnage * MRAL_Fe2O3) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                    )::numeric, 2), 0) as fe2o3,
                    COALESCE(ROUND((
                        SUM(tonnage * MRAL_Fe) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                    )::numeric, 2), 0) as fe,
                    COALESCE(ROUND((
                        SUM(tonnage * MRAL_MgO) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                    )::numeric, 2), 0) as mgo,
                    COALESCE(ROUND((
                        SUM(tonnage * MRAL_SiO2) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                    )::numeric, 2), 0) as sio2,
                    ROUND(COALESCE(
                        (
                            SUM(tonnage * MRAL_SiO2) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                        ) /
                        (
                            NULLIF(
                                SUM(tonnage * MRAL_MgO) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0),
                                0) + 0.000001), 0
                    )::numeric, 2) as sm
                FROM details_mral
                WHERE stockpile <> 'Temp-Rompile_KM09'
                """
    else:
        raise ValueError("Unsupported database vendor.")

    # Menambahkan kondisi ke query berdasarkan input
    if materialFilter:
        sql_query += f" AND nama_material = '{materialFilter}'"
    if cutDate:
        sql_query += f" AND tgl_production <= '{cutDate}'"
    if start_date and end_date:
        sql_query += f" AND tgl_production BETWEEN '{start_date}' AND '{end_date}'"
    if bulanFilter and tahunFilter:
        if db_vendor == 'postgresql':
            sql_query += f" AND EXTRACT(MONTH FROM tgl_production) = {bulanFilter} AND EXTRACT(YEAR FROM tgl_production) = {tahunFilter}"
        else:
            sql_query += f" AND MONTH(tgl_production) = {bulanFilter} AND YEAR(tgl_production) = {tahunFilter}"
    if tahunFilter:
        if db_vendor == 'postgresql':
            sql_query += f" AND EXTRACT(YEAR FROM tgl_production) = {tahunFilter}"
        else:
            sql_query += f" AND YEAR(tgl_production) = {tahunFilter}"
    if sourceFilter:
        sql_query += f" AND prospect_area IN ({', '.join(f'\'{source}\'' for source in sourceFilter)})"
    if areaFilter:
        sql_query += f" AND stockpile = '{areaFilter}'"
    if pointFilter:
        sql_query += f" AND pile_id = '{pointFilter}'"

    sql_query += " GROUP BY stockpile, nama_material"

    # Query untuk mengambil data dengan pagination
    if db_vendor == 'postgresql':
        # Query untuk postgresql
        sql_query += f" LIMIT {per_page} OFFSET {offset};"
    else:
        raise ValueError("Unsupported database vendor.")

    # Eksekusi query untuk mengambil data
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(sql_query)
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            sql_data = []


    # Hitung jika masih ada data untuk halaman berikutnya
    more_data = len(sql_data) == per_page

    # Hitung total halaman
    total_pages = (total_data // per_page) + (1 if total_data % per_page > 0 else 0)
    grandTotalOre = 0
    grandTotalIncomplete = 0
    grandTotalUnprepared = 0
    grandTotalUnRelease  = 0
    grandTotalRelease    = 0

    # Data untuk product grade
    data_Ni    = []
    data_Co    = []
    data_Fe2O3 = []
    data_Fe    = []
    data_Mgo   = []
    data_SiO2  = []

    # Menghitung grand total dan product grade
    for row in sql_data:
            grandTotalOre += float(row['total_ore'])
            grandTotalIncomplete += float(row['incomplete'])
            grandTotalUnprepared += float(row['unprepared'])
            grandTotalUnRelease  += float(row['unreleased'])
            grandTotalRelease    += float(row['released'])

            # Hitung Product Grade
            data_Ni.append(row['released'] * float(row['ni']))
            data_Co.append(row['released'] * float(row['co']))
            data_Fe2O3.append(row['released'] * float(row['fe2o3']))
            data_Fe.append(row['released'] * float(row['fe']))
            data_Mgo.append(row['released'] * float(row['mgo']))
            data_SiO2.append(row['released'] * float(row['sio2']))

    # Fungsi untuk menghitung SUM Product
    def sum_product(data_array):
        return sum(data_array)

 # Menghitung SUM Product Grade
    sumResults = {
        'ni': round(sum_product(data_Ni) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'co': round(sum_product(data_Co) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'fe2o3': round(sum_product(data_Fe2O3) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'fe': round(sum_product(data_Fe) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'mgo': round(sum_product(data_Mgo) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'sio2': round(sum_product(data_SiO2) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0
    }

    return JsonResponse({
        'data': sql_data,
        'grand_totals': {
            'total_ore'  : grandTotalOre,
            'incomplete' : grandTotalIncomplete,
            'unprepared' : grandTotalUnprepared,
            'unreleased' : grandTotalUnRelease,
            'released'   : grandTotalRelease
        },
        'sum_results': sumResults,
        'pagination': {
            'more': more_data,
            'total_pages': total_pages,
            'current_page': page,
            'total_data': total_data
        }
    })

@login_required
def source_mral(request):
    # Ambil dan sanitasi input dari request
    start_date     = sanitize_input(request.GET.get('startDate'))
    end_date       = sanitize_input(request.GET.get('endDate'))
    materialFilter = sanitize_input(request.GET.get('materialFilter'))
    cutDate        = sanitize_input(request.GET.get('cutDate'))
    bulanFilter    = sanitize_input(request.GET.get('bulanFilter'))
    tahunFilter    = sanitize_input(request.GET.get('tahunFilter'))
    sourceFilter   = json.loads(request.GET.get('sourceFilter', '[]'))

    # sanitize_input: Fungsi ini membersihkan karakter yang berpotensi menyebabkan SQL injection.

    # Filter list sourceFilter
    sourceFilter = [sanitize_input(source) for source in sourceFilter if source]

   # Pagination setup
    page = int(request.GET.get('page', 1))
    per_page = 1000
    offset = (page - 1) * per_page

    # Query untuk menghitung total data
    count_query = """
        SELECT COUNT(*) FROM details_mral
        WHERE stockpile <> 'Temp-Rompile_KM09'
    """
    
    # Menambahkan kondisi ke count_query berdasarkan input
    if materialFilter:
        count_query += f" AND nama_material = '{materialFilter}'"
    if cutDate:
        count_query += f" AND tgl_production <= '{cutDate}'"
    if start_date and end_date:
        count_query += f" AND tgl_production BETWEEN '{start_date}' AND '{end_date}'"
    if bulanFilter and tahunFilter:
        if db_vendor == 'postgresql':
            count_query += f" AND EXTRACT(MONTH FROM tgl_production) = {bulanFilter} AND EXTRACT(YEAR FROM tgl_production) = {tahunFilter}"
        else:  # SQL Server
            count_query += f" AND MONTH(tgl_production) = {bulanFilter} AND YEAR(tgl_production) = {tahunFilter}"
    if tahunFilter:
        if db_vendor == 'postgresql':
            count_query += f" AND EXTRACT(YEAR FROM tgl_production) = {tahunFilter}"
        else:
            count_query += f" AND YEAR(tgl_production) = {tahunFilter}"

    if sourceFilter:
        count_query += f" AND prospect_area IN ({', '.join(f'\'{source}\'' for source in sourceFilter)})"

    # eksekusi query
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(count_query)
        result = cursor.fetchone()
        total_data = result[0] if result else 0

    # Query berdasarkan database
    if db_vendor == 'postgresql':
    # Query untuk postgresql
        sql_query = f"""
             SELECT 
                    TRIM(prospect_area) AS prospect_area,
                    TRIM(nama_material) AS nama_material,
                    SUM(tonnage) AS total_ore,
                    SUM(CASE WHEN batch_status = 'Incomplete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS incomplete,
                    SUM(CASE WHEN batch_status = 'Complete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS unprepared,
                    SUM(CASE WHEN MRAL_Ni IS NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS unreleased,
                    SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS released,
                    CONCAT(
                        ROUND(( COALESCE(SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) * 100.0 / NULLIF(SUM(tonnage), 0), 0) )::numeric, 0),'%') AS recovery,
                    COALESCE(ROUND((
                        SUM(tonnage * MRAL_Ni) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                    )::numeric, 2), 0) as ni,
                    COALESCE(ROUND((
                        SUM(tonnage * MRAL_Co) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                    )::numeric, 2), 0) as co,
                    COALESCE(ROUND((
                        SUM(tonnage * MRAL_Fe2O3) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                    )::numeric, 2), 0) as fe2o3,
                    COALESCE(ROUND((
                        SUM(tonnage * MRAL_Fe) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                    )::numeric, 2), 0) as fe,
                    COALESCE(ROUND((
                        SUM(tonnage * MRAL_MgO) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                    )::numeric, 2), 0) as mgo,
                    COALESCE(ROUND((
                        SUM(tonnage * MRAL_SiO2) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                    )::numeric, 2), 0) as sio2,
                    ROUND(COALESCE(
                        (
                            SUM(tonnage * MRAL_SiO2) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                        ) /
                        (
                            NULLIF(
                                SUM(tonnage * MRAL_MgO) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0),
                                0) + 0.000001), 0
                    )::numeric, 2) as sm
                FROM details_mral
                WHERE stockpile <> 'Temp-Rompile_KM09'
    """
    else:
        raise ValueError("Unsupported database vendor.")

    # Menambahkan kondisi ke query berdasarkan input
    if materialFilter:
        sql_query += f" AND nama_material = '{materialFilter}'"
    if cutDate:
        sql_query += f" AND tgl_production <= '{cutDate}'"
    if start_date and end_date:
        sql_query += f" AND tgl_production BETWEEN '{start_date}' AND '{end_date}'"
    if bulanFilter and tahunFilter:
        if db_vendor == 'postgresql':
            sql_query += f" AND EXTRACT(MONTH FROM tgl_production) = {bulanFilter} AND EXTRACT(YEAR FROM tgl_production) = {tahunFilter}"
        else:
            sql_query += f" AND MONTH(tgl_production) = {bulanFilter} AND YEAR(tgl_production) = {tahunFilter}"
    if tahunFilter:
        if db_vendor == 'postgresql':
            sql_query += f" AND EXTRACT(YEAR FROM tgl_production) = {tahunFilter}"
        else:
            sql_query += f" AND YEAR(tgl_production) = {tahunFilter}"

    if sourceFilter:
        sql_query += f" AND prospect_area IN ({', '.join(f'\'{source}\'' for source in sourceFilter)})"

    sql_query += " GROUP BY prospect_area, nama_material"
    # Query untuk mengambil data dengan pagination
    if db_vendor == 'postgresql':
        # Query untuk postgresql
        sql_query += f" LIMIT {per_page} OFFSET {offset};"
    else:
        raise ValueError("Unsupported database vendor.")

    # Eksekusi query untuk mengambil data
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(sql_query)
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            sql_data = []

    # Hitung jika masih ada data untuk halaman berikutnya
    more_data = len(sql_data) == per_page

    # Hitung total halaman
    total_pages = (total_data // per_page) + (1 if total_data % per_page > 0 else 0)

    grandTotalOre = 0
    grandTotalIncomplete = 0
    grandTotalUnprepared = 0
    grandTotalUnRelease  = 0
    grandTotalRelease    = 0


    # Data untuk product grade
    data_Ni    = []
    data_Co    = []
    data_Fe2O3 = []
    data_Fe    = []
    data_Mgo   = []
    data_SiO2  = []

    # Menghitung grand total dan product grade
    for row in sql_data:
            grandTotalOre += float(row['total_ore'])
            grandTotalIncomplete += float(row['incomplete'])
            grandTotalUnprepared += float(row['unprepared'])
            grandTotalUnRelease  += float(row['unreleased'])
            grandTotalRelease    += float(row['released'])

            # Hitung Product Grade
            data_Ni.append(row['released'] * float(row['ni']))
            data_Co.append(row['released'] * float(row['co']))
            data_Fe2O3.append(row['released'] * float(row['fe2o3']))
            data_Fe.append(row['released'] * float(row['fe']))
            data_Mgo.append(row['released'] * float(row['mgo']))
            data_SiO2.append(row['released'] * float(row['sio2']))

    # Fungsi untuk menghitung SUM Product
    def sum_product(data_array):
        return sum(data_array)

 # Menghitung SUM Product Grade
    sumResults = {
        'ni': round(sum_product(data_Ni) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'co': round(sum_product(data_Co) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'fe2o3': round(sum_product(data_Fe2O3) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Fe': round(sum_product(data_Fe) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'mgo': round(sum_product(data_Mgo) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'sio2': round(sum_product(data_SiO2) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0
    }

    return JsonResponse({
        'data': sql_data,
        'grand_totals': {
            'total_ore'  : grandTotalOre,
            'incomplete' : grandTotalIncomplete,
            'unprepared' : grandTotalUnprepared,
            'unreleased' : grandTotalUnRelease,
            'released'   : grandTotalRelease
        },
        'sum_results': sumResults,
        'pagination': {
            'more': more_data,
            'total_pages': total_pages,
            'current_page': page,
            'total_data': total_data
        }
    })

@login_required
def to_stockpile_mral(request):
    # Ambil dan sanitasi input dari request
    start_date     = sanitize_input(request.GET.get('startDate'))
    end_date       = sanitize_input(request.GET.get('endDate'))
    materialFilter = sanitize_input(request.GET.get('materialFilter'))
    cutDate        = sanitize_input(request.GET.get('cutDate'))
    bulanFilter    = sanitize_input(request.GET.get('bulanFilter'))
    tahunFilter    = sanitize_input(request.GET.get('tahunFilter'))
    sourceFilter   = json.loads(request.GET.get('sourceFilter', '[]'))
    areaFilter     = sanitize_input(request.GET.get('areaFilter'))
    pointFilter    = sanitize_input(request.GET.get('pointFilter'))

    # sanitize_input: Fungsi ini membersihkan karakter yang berpotensi menyebabkan SQL injection.

    # Filter list sourceFilter
    sourceFilter = [sanitize_input(source) for source in sourceFilter if source]

   # Pagination setup
    page = int(request.GET.get('page', 1))
    per_page = 1000
    offset = (page - 1) * per_page

    # Query untuk menghitung total data
    count_query = """
        SELECT COUNT(*) FROM details_mral
        WHERE stockpile <> 'Temp-Rompile_KM09'
    """
    
    # Menambahkan kondisi ke count_query berdasarkan input
    if materialFilter:
        count_query += f" AND nama_material = '{materialFilter}'"
    if cutDate:
        count_query += f" AND tgl_production <= '{cutDate}'"
    if start_date and end_date:
        count_query += f" AND tgl_production BETWEEN '{start_date}' AND '{end_date}'"
    if bulanFilter and tahunFilter:
        if db_vendor == 'postgresql':
            count_query += f" AND EXTRACT(MONTH FROM tgl_production) = {bulanFilter} AND EXTRACT(YEAR FROM tgl_production) = {tahunFilter}"
        else:  # SQL Server
            count_query += f" AND MONTH(tgl_production) = {bulanFilter} AND YEAR(tgl_production) = {tahunFilter}"
    if tahunFilter:
        if db_vendor == 'postgresql':
            count_query += f" AND EXTRACT(YEAR FROM tgl_production) = {tahunFilter}"
        else:
            count_query += f" AND YEAR(tgl_production) = {tahunFilter}"

    if sourceFilter:
        count_query += f" AND prospect_area IN ({', '.join(f'\'{source}\'' for source in sourceFilter)})"
    if areaFilter:
        count_query += f" AND stockpile = '{areaFilter}'"
    if pointFilter:
        count_query += f" AND pile_id = '{pointFilter}'"

    # Hitung total data
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(count_query)
        result = cursor.fetchone()
        total_data = result[0] if result else 0
    # Query berdasarkan database
    if db_vendor == 'postgresql':
        sql_query = f"""
             SELECT 
                    TRIM(prospect_area) AS prospect_area,
                    TRIM(stockpile) AS stockpile,
                    TRIM(nama_material) AS nama_material,
                    SUM(tonnage) AS total_ore,
                    SUM(CASE WHEN batch_status = 'Incomplete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS incomplete,
                    SUM(CASE WHEN batch_status = 'Complete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS unprepared,
                    SUM(CASE WHEN MRAL_Ni IS NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS unreleased,
                    SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS released,
                    CONCAT(
                        ROUND(( COALESCE(SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) * 100.0 / NULLIF(SUM(tonnage), 0), 0) )::numeric, 0),'%') AS recovery,
                    COALESCE(ROUND((
                        SUM(tonnage * MRAL_Ni) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                    )::numeric, 2), 0) as ni,
                    COALESCE(ROUND((
                        SUM(tonnage * MRAL_Co) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                    )::numeric, 2), 0) as co,
                    COALESCE(ROUND((
                        SUM(tonnage * MRAL_Fe2O3) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                    )::numeric, 2), 0) as fe2o3,
                    COALESCE(ROUND((
                        SUM(tonnage * MRAL_Fe) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                    )::numeric, 2), 0) as fe,
                    COALESCE(ROUND((
                        SUM(tonnage * MRAL_MgO) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                    )::numeric, 2), 0) as mgo,
                    COALESCE(ROUND((
                        SUM(tonnage * MRAL_SiO2) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                    )::numeric, 2), 0) as sio2,
                    ROUND(COALESCE(
                        (
                            SUM(tonnage * MRAL_SiO2) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                        ) /
                        (
                            NULLIF(
                                SUM(tonnage * MRAL_MgO) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0),
                                0) + 0.000001), 0
                    )::numeric, 2) as sm
                FROM details_mral
                WHERE stockpile <> 'Temp-Rompile_KM09'
    """
    else:
        raise ValueError("Unsupported database vendor.")

    # Menambahkan kondisi ke query berdasarkan input
    if materialFilter:
        sql_query += f" AND nama_material = '{materialFilter}'"
    if cutDate:
        sql_query += f" AND tgl_production <= '{cutDate}'"
    if start_date and end_date:
        sql_query += f" AND tgl_production BETWEEN '{start_date}' AND '{end_date}'"
    if bulanFilter and tahunFilter:
        if db_vendor == 'postgresql':
            sql_query += f" AND EXTRACT(MONTH FROM tgl_production) = {bulanFilter} AND EXTRACT(YEAR FROM tgl_production) = {tahunFilter}"
        else:
            sql_query += f" AND MONTH(tgl_production) = {bulanFilter} AND YEAR(tgl_production) = {tahunFilter}"
    if tahunFilter:
        if db_vendor == 'postgresql':
            sql_query += f" AND EXTRACT(YEAR FROM tgl_production) = {tahunFilter}"
        else:
            sql_query += f" AND YEAR(tgl_production) = {tahunFilter}"
    if sourceFilter:
        sql_query += f" AND prospect_area IN ({', '.join(f'\'{source}\'' for source in sourceFilter)})"
    if areaFilter:
        sql_query += f" AND stockpile = '{areaFilter}'"
    if pointFilter:
        sql_query += f" AND pile_id = '{pointFilter}'"

    sql_query += " GROUP BY prospect_area, stockpile, nama_material"

    # Query untuk mengambil data dengan pagination
    if db_vendor == 'postgresql':
        # Query untuk postgresql
        sql_query += f" LIMIT {per_page} OFFSET {offset};"
       
    else:
        raise ValueError("Unsupported database vendor.")
    
    # Eksekusi query untuk mengambil data
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(sql_query)
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            sql_data = []


    # Hitung jika masih ada data untuk halaman berikutnya
    more_data = len(sql_data) == per_page

    # Hitung total halaman
    total_pages = (total_data // per_page) + (1 if total_data % per_page > 0 else 0)

    grandTotalOre = 0
    grandTotalIncomplete = 0
    grandTotalUnprepared = 0
    grandTotalUnRelease  = 0
    grandTotalRelease    = 0


    # Data untuk product grade
    data_Ni    = []
    data_Co    = []
    data_Fe2O3 = []
    data_Fe    = []
    data_Mgo   = []
    data_SiO2  = []

    # Menghitung grand total dan product grade
    for row in sql_data:
            grandTotalOre += float(row['total_ore'])
            grandTotalIncomplete += float(row['incomplete'])
            grandTotalUnprepared += float(row['unprepared'])
            grandTotalUnRelease  += float(row['unreleased'])
            grandTotalRelease    += float(row['released'])

            # Hitung Product Grade
            data_Ni.append(row['released'] * float(row['ni']))
            data_Co.append(row['released'] * float(row['co']))
            data_Fe2O3.append(row['released'] * float(row['fe2o3']))
            data_Fe.append(row['released'] * float(row['fe']))
            data_Mgo.append(row['released'] * float(row['mgo']))
            data_SiO2.append(row['released'] * float(row['sio2']))

    # Fungsi untuk menghitung SUM Product
    def sum_product(data_array):
        return sum(data_array)

 # Menghitung SUM Product Grade
    sumResults = {
        'ni': round(sum_product(data_Ni) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'co': round(sum_product(data_Co) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'fe2o3': round(sum_product(data_Fe2O3) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'Fe': round(sum_product(data_Fe) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'mgo': round(sum_product(data_Mgo) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0,
        'sio2': round(sum_product(data_SiO2) / grandTotalRelease, 2) if grandTotalRelease != 0 else 0
    }

    return JsonResponse({
        'data': sql_data,
        'grand_totals': {
            'total_ore'  : grandTotalOre,
            'incomplete' : grandTotalIncomplete,
            'unprepared' : grandTotalUnprepared,
            'unreleased' : grandTotalUnRelease,
            'released'   : grandTotalRelease
        },
        'sum_results': sumResults,
        'pagination': {
            'more': more_data,
            'total_pages': total_pages,
            'current_page': page,
            'total_data': total_data
        }
    })

# @login_required
def to_dome_mral(request):
    # Ambil dan sanitasi input dari request
    start_date     = sanitize_input(request.GET.get('startDate'))
    end_date       = sanitize_input(request.GET.get('endDate'))
    materialFilter = sanitize_input(request.GET.get('materialFilter'))
    cutDate        = sanitize_input(request.GET.get('cutDate'))
    bulanFilter    = sanitize_input(request.GET.get('bulanFilter'))
    tahunFilter    = sanitize_input(request.GET.get('tahunFilter'))
    sourceFilter   = json.loads(request.GET.get('sourceFilter', '[]'))
    areaFilter     = sanitize_input(request.GET.get('areaFilter'))
    pointFilter    = sanitize_input(request.GET.get('pointFilter'))

    # Filter list sourceFilter
    sourceFilter = [sanitize_input(source) for source in sourceFilter if source]
   # Pagination setup
    page = int(request.GET.get('page', 1))
    per_page = 50
    offset = (page - 1) * per_page

    # Query untuk menghitung total data
    count_query = """
        SELECT COUNT(*) FROM details_mral
        WHERE stockpile <> 'Temp-Rompile_KM09'
    """
    
    # Menambahkan kondisi ke count_query berdasarkan input
    if materialFilter:
        count_query += f" AND nama_material = '{materialFilter}'"
    if cutDate:
        count_query += f" AND tgl_production <= '{cutDate}'"
    if start_date and end_date:
        count_query += f" AND tgl_production BETWEEN '{start_date}' AND '{end_date}'"
    if bulanFilter and tahunFilter:
        if db_vendor == 'postgresql':
            count_query += f" AND EXTRACT(MONTH FROM tgl_production) = {bulanFilter} AND EXTRACT(YEAR FROM tgl_production) = {tahunFilter}"
        else:  # SQL Server
            count_query += f" AND MONTH(tgl_production) = {bulanFilter} AND YEAR(tgl_production) = {tahunFilter}"

    if tahunFilter:
        if db_vendor == 'postgresql':
            count_query += f" AND EXTRACT(YEAR FROM tgl_production) = {tahunFilter}"
        else:
            count_query += f" AND YEAR(tgl_production) = {tahunFilter}"

    if sourceFilter:
        count_query += f" AND prospect_area IN ({', '.join(f'\'{source}\'' for source in sourceFilter)})"
    if areaFilter:
        count_query += f" AND stockpile = '{areaFilter}'"
    if pointFilter:
        count_query += f" AND pile_id = '{pointFilter}'"

    # Hitung total data
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(count_query)
        result = cursor.fetchone()
        total_data = result[0] if result else 0 

    # Query berdasarkan database
    if db_vendor == 'postgresql':
    # Query untuk postgresql
        sql_query = f"""
            SELECT 
                    TRIM(prospect_area) AS prospect_area,
                    TRIM(pile_id) AS pile_id,
                    TRIM(nama_material) AS nama_material,
                    SUM(tonnage) AS total_ore,
                    SUM(CASE WHEN batch_status = 'Incomplete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS incomplete,
                    SUM(CASE WHEN batch_status = 'Complete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS unprepared,
                    SUM(CASE WHEN MRAL_Ni IS NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS unreleased,
                    SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS released,
                    CONCAT(
                        ROUND(( COALESCE(SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) * 100.0 / NULLIF(SUM(tonnage), 0), 0) )::numeric, 0),'%') AS recovery,
                    COALESCE(ROUND((
                        SUM(tonnage * MRAL_Ni) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                    )::numeric, 2), 0) as ni,
                    COALESCE(ROUND((
                        SUM(tonnage * MRAL_Co) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                    )::numeric, 2), 0) as co,
                    COALESCE(ROUND((
                        SUM(tonnage * MRAL_Fe2O3) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                    )::numeric, 2), 0) as fe2o3,
                    COALESCE(ROUND((
                        SUM(tonnage * MRAL_Fe) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                    )::numeric, 2), 0) as fe,
                    COALESCE(ROUND((
                        SUM(tonnage * MRAL_MgO) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                    )::numeric, 2), 0) as mgo,
                    COALESCE(ROUND((
                        SUM(tonnage * MRAL_SiO2) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                    )::numeric, 2), 0) as sio2,
                    ROUND(COALESCE(
                        (
                            SUM(tonnage * MRAL_SiO2) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                        ) /
                        (
                            NULLIF(
                                SUM(tonnage * MRAL_MgO) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0),
                                0) + 0.000001), 0
                    )::numeric, 2) as sm
                FROM details_mral
                WHERE stockpile <> 'Temp-Rompile_KM09'
    """
    else:
        raise ValueError("Unsupported database vendor.")

    # Menambahkan kondisi berdasarkan input
    if materialFilter:
        sql_query += f" AND nama_material = '{materialFilter}'"
    if cutDate:
        sql_query += f" AND tgl_production <= '{cutDate}'"
    if start_date and end_date:
        sql_query += f" AND tgl_production BETWEEN '{start_date}' AND '{end_date}'"
    if bulanFilter and tahunFilter:
        if db_vendor == 'postgresql':
            sql_query += f" AND EXTRACT(MONTH FROM tgl_production) = {bulanFilter} AND EXTRACT(YEAR FROM tgl_production) = {tahunFilter}"
        else:
            sql_query += f" AND MONTH(tgl_production) = {bulanFilter} AND YEAR(tgl_production) = {tahunFilter}"
    if tahunFilter:
        if db_vendor == 'postgresql':
            sql_query += f" AND EXTRACT(YEAR FROM tgl_production) = {tahunFilter}"
        else:
            sql_query += f" AND YEAR(tgl_production) = {tahunFilter}"
    if sourceFilter:
        sql_query += f" AND prospect_area IN ({', '.join(f'\'{source}\'' for source in sourceFilter)})"
    if areaFilter:
        sql_query += f" AND stockpile = '{areaFilter}'"
    if pointFilter:
        sql_query += f" AND pile_id = '{pointFilter}'"

   # Pengelompokan dan pagination
    sql_query += """
        GROUP BY prospect_area, pile_id, nama_material
        ORDER BY prospect_area, pile_id, nama_material ASC
    """

    # Query untuk mengambil data dengan pagination
    if db_vendor == 'postgresql':
        sql_query += f" LIMIT {per_page} OFFSET {offset};"
    else:
        raise ValueError("Unsupported database vendor.")

    # Eksekusi query untuk mengambil data
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(sql_query)
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            sql_data = []


    # Hitung jika masih ada data untuk halaman berikutnya
    more_data = len(sql_data) == per_page
    # Hitung total halaman
    total_pages = (total_data // per_page) + (1 if total_data % per_page > 0 else 0)
    return JsonResponse({
        'data': sql_data,
        'pagination': {
            'more'         : more_data,
            'total_pages'  : total_pages,
            'current_page' : page,
            'total_data'   : total_data
        }
    })