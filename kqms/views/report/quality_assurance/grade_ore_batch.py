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

# Fungsi untuk sanitasi input
def sanitize_input(value):
    if value is None:
        return None
    return escape(re.sub(r"[;'\"]", "", str(value)))
@login_required
def grade_ore_page(request):
    return render(request, 'admin-mgoqa/report-qa/list-grade-ore.html')

def mralgradeBatch(request):
    domeFilter   = json.loads(request.GET.get('domeFilter', '[]'))

    # Filter list domeFilter
    domeFilter = [sanitize_input(dome) for dome in domeFilter if dome]

    # Query berdasarkan database
    if db_vendor == 'mysql':
        # Query untuk MySQL
        sql_query = f"""
                SELECT 
                    TRIM(pile_id) pile_id,
                    TRIM(nama_material) nama_material,
                    TRIM(batch_code) AS batch_code,
                    SUM(tonnage) AS total_ore,
                    SUM(CASE WHEN batch_status = 'Incomplete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS incomplete,
                    SUM(CASE WHEN batch_status = 'Complete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS unprepared,
                    SUM(CASE WHEN MRAL_Ni IS NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS unreleased,
                    SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS released,
                    COALESCE(FORMAT(SUM(tonnage * MRAL_Ni) / SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Ni,
                    COALESCE(FORMAT(SUM(tonnage * MRAL_Co) / SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Co,
                    COALESCE(FORMAT(SUM(tonnage * MRAL_Fe2O3) / SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Fe2O3,
                    COALESCE(FORMAT(SUM(tonnage * MRAL_Fe) / SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Fe,
                    COALESCE(FORMAT(SUM(tonnage * MRAL_MgO) / SUM(CASE WHEN sample_number  IS NOT NULL AND MRAL_Ni  IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS Mgo,
                    COALESCE(FORMAT(SUM(tonnage * MRAL_SiO2) / SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 2), 0) AS SiO2,
                    ROUND((COALESCE(SUM(tonnage * MRAL_SiO2) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL AND MRAL_MgO != 0 THEN tonnage ELSE 0 END), 0), 0)) / 
                    (COALESCE(SUM(tonnage * MRAL_MgO) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0), 0) + 0.000001), 2) AS SM
                FROM details_mral
                WHERE stockpile <> 'Temp-Rompile_KM09'
        """
   
    elif db_vendor in ['mssql', 'microsoft']:
            # Query untuk SQL Server
        sql_query = f"""
                SELECT 
                    TRIM(pile_id) AS pile_id,
                    TRIM(nama_material) nama_material,
                    TRIM(batch_code) AS batch_code,
                    SUM(tonnage) AS total_ore,
                    SUM(CASE WHEN batch_status = 'Incomplete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS incomplete,
                    SUM(CASE WHEN batch_status = 'Complete' AND sample_number = 'Unprepared' THEN tonnage ELSE 0 END) AS unprepared,
                    SUM(CASE WHEN MRAL_Ni IS NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS unreleased,
                    SUM(CASE WHEN MRAL_Ni IS NOT NULL AND sample_number <> 'Unprepared' THEN tonnage ELSE 0 END) AS released,
                    COALESCE(CAST(SUM(tonnage * MRAL_Ni) / SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END) AS NUMERIC(10,2)), 0) AS Ni,
                    COALESCE(CAST(SUM(tonnage * MRAL_Co) / SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END) AS NUMERIC(10,2)), 0) AS Co,
                    COALESCE(CAST(SUM(tonnage * MRAL_Fe2O3) / SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END) AS NUMERIC(10,2)), 0) AS Fe2O3,
                    COALESCE(CAST(SUM(tonnage * MRAL_Fe) / SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END) AS NUMERIC(10,2)), 0) AS Fe,
                    COALESCE(CAST(SUM(tonnage * MRAL_MgO) / SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END) AS NUMERIC(10,2)), 0) AS Mgo,
                    COALESCE(CAST(SUM(tonnage * MRAL_SiO2) / SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END) AS NUMERIC(10,2)), 0) AS SiO2,
                    ROUND((COALESCE(SUM(tonnage * MRAL_SiO2) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL AND MRAL_MgO != 0 THEN tonnage ELSE 0 END), 0), 0)) / 
                    (COALESCE(SUM(tonnage * MRAL_MgO) / NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND MRAL_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0), 0) + 0.000001), 2) AS SM
                FROM details_mral
                WHERE stockpile <> 'Temp-Rompile_KM09'
            """
   
    else:
        raise ValueError("Unsupported database vendor.")

     # **Filter pada query utama t1**
    params = []
    
    if domeFilter:
        placeholders = ', '.join(['%s'] * len(domeFilter))
        sql_query += f" AND pile_id IN ({placeholders})"
        params.extend(domeFilter)

    sql_query += """
        GROUP BY pile_id, nama_material,batch_code
        ORDER BY batch_code asc
    """

    # **Eksekusi Query**
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(sql_query, params)
        columns = [col[0] for col in cursor.description]
        sql_data = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    return JsonResponse({'data': sql_data})

def roagradeBatch(request):
    domeFilter   = json.loads(request.GET.get('domeFilter', '[]'))

    # Filter list domeFilter
    domeFilter = [sanitize_input(dome) for dome in domeFilter if dome]

    # Query berdasarkan database
     # Query berdasarkan database
    if db_vendor == 'mysql':
    # Query untuk MySQL
        sql_query = """
            SELECT
                pile_id,
                nama_material,
                TRIM(batch_code) AS batch_code,
                SUM(tonnage) AS total_ore,
                SUM(CASE WHEN batch_status = 'Incomplete' AND sample_number ='Unprepared' THEN tonnage ELSE 0 END) AS incomplete,
                SUM(CASE WHEN batch_status = 'Complete' AND sample_number ='Unprepared' THEN tonnage ELSE 0 END) AS unprepared,
                SUM(CASE WHEN ROA_Ni IS NULL AND sample_number  <> 'Unprepared' THEN tonnage ELSE 0 END) AS unreleased,
                SUM(CASE WHEN ROA_Ni  IS NOT NULL AND sample_number  <> 'Unprepared' THEN tonnage ELSE 0 END) AS released,
                COALESCE (FORMAT(SUM(tonnage * ROA_Ni) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Ni,
                COALESCE (FORMAT(SUM(tonnage * ROA_Co) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Co,
                COALESCE (FORMAT(SUM(tonnage * ROA_Al2O3) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Al2O3,
                COALESCE (FORMAT(SUM(tonnage * ROA_CaO) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS CaO,
                COALESCE (FORMAT(SUM(tonnage * ROA_Cr2O3) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Cr2O3,
                COALESCE (FORMAT(SUM(tonnage * ROA_Fe2O3) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Fe2O3,
                COALESCE (FORMAT(SUM(tonnage * ROA_Fe) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Fe,
                COALESCE (FORMAT(SUM(tonnage * ROA_MgO) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS Mgo,
                COALESCE (FORMAT(SUM(tonnage * ROA_SiO2) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS SiO2,
                COALESCE (FORMAT(SUM(tonnage * ROA_MC) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),2), 0) AS MC,
                ROUND((COALESCE(SUM(tonnage * ROA_SiO2) / NULLIF(SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL AND ROA_MgO != 0 THEN tonnage ELSE 0 END), 0), 0)) /
                (COALESCE(SUM(tonnage * ROA_MgO) / NULLIF(SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0), 0) + 0.000001), 2) AS SM
            FROM details_roa
            WHERE stockpile <> 'Temp-Rompile_KM09'
    """
    elif db_vendor in ['mssql', 'microsoft']:
    # Query untuk SQL Server
        sql_query = """
            SELECT
                pile_id,
                nama_material,
                TRIM(batch_code) AS batch_code,
                SUM(tonnage) AS total_ore,
                SUM(CASE WHEN batch_status = 'Incomplete' AND sample_number ='Unprepared' THEN tonnage ELSE 0 END) AS incomplete,
                SUM(CASE WHEN batch_status = 'Complete' AND sample_number ='Unprepared' THEN tonnage ELSE 0 END) AS unprepared,
                SUM(CASE WHEN ROA_Ni IS NULL AND sample_number  <> 'Unprepared' THEN tonnage ELSE 0 END) AS unreleased,
                SUM(CASE WHEN ROA_Ni  IS NOT NULL AND sample_number  <> 'Unprepared' THEN tonnage ELSE 0 END) AS released,
                COALESCE (FORMAT(SUM(tonnage * ROA_Ni) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Ni,
                COALESCE (FORMAT(SUM(tonnage * ROA_Co) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Co,
                COALESCE (FORMAT(SUM(tonnage * ROA_Al2O3) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Al2O3,
                COALESCE (FORMAT(SUM(tonnage * ROA_CaO) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS CaO,
                COALESCE (FORMAT(SUM(tonnage * ROA_Cr2O3) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Cr2O3,
                COALESCE (FORMAT(SUM(tonnage * ROA_Fe2O3) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Fe2O3,
                COALESCE (FORMAT(SUM(tonnage * ROA_Fe) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Fe,
                COALESCE (FORMAT(SUM(tonnage * ROA_MgO) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS Mgo,
                COALESCE (FORMAT(SUM(tonnage * ROA_SiO2) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS SiO2,
                COALESCE (FORMAT(SUM(tonnage * ROA_MC) / SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END),'N2'), '0') AS MC,
                ROUND((COALESCE(SUM(tonnage * ROA_SiO2) / NULLIF(SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL AND ROA_MgO != 0 THEN tonnage ELSE 0 END), 0), 0)) /
                (COALESCE(SUM(tonnage * ROA_MgO) / NULLIF(SUM(CASE WHEN sample_number  <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0), 0) + 0.000001), 2) AS SM
            FROM details_roa
            WHERE stockpile <> 'Temp-Rompile_KM09'
    """
    else:
        raise ValueError("Unsupported database vendor.")
     # **Filter pada query utama t1**
    params = []
    
    if domeFilter:
        placeholders = ', '.join(['%s'] * len(domeFilter))
        sql_query += f" AND pile_id IN ({placeholders})"
        params.extend(domeFilter)

    sql_query += """
        GROUP BY pile_id, nama_material,batch_code
        ORDER BY batch_code asc
    """

    # **Eksekusi Query**
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(sql_query, params)
        columns = [col[0] for col in cursor.description]
        sql_data = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    return JsonResponse({'data': sql_data})
