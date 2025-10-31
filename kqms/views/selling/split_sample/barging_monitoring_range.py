from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.db import connections, DatabaseError
from django.utils.html import escape
import json,re

# Fungsi untuk sanitasi input
def sanitize_input(value):
    if value is None:
        return None
    return escape(re.sub(r"[;'\"]", "", str(value)))

def samplesMonitoring(request):
    typeFilter   = request.GET.get('typeFilter')
    startDate    = request.GET.get('startDate')
    endDate      = request.GET.get('endDate')
    codeFilter   = json.loads(request.GET.get('codeFilter', '[]'))
    bulanFilter  = request.GET.get('bulanFilter')
    tahunFilter  = request.GET.get('tahunFilter')
    # Filter list codeFilter
    codeFilter = [sanitize_input(code) for code in codeFilter if code]

    sql_query = """
       SELECT 
            TRIM(t1.code_lot) AS code_lot,
            TRIM(t1.barge_code) AS barge_code,
            CONCAT(TRIM(t1.barge_code), '/', RIGHT(TRIM(t1.code_lot), 3)) AS lot_barge,
            -- Tonnage dan Ni dari monitoring
            COALESCE(SUM(t1.tonnage), 0) AS tonnage_monitoring,
            COALESCE(
                SUM(t1.tonnage * t1.ni) / 
                NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.ni IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),
                0
                ) AS ni_monitoring,
            COALESCE(
                SUM(t1.tonnage * t1.co) / 
                NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.co IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),
                0
                ) AS co_monitoring,
            COALESCE(
                SUM(t1.tonnage * t1.fe) / 
                NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.fe IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),
                0
                ) AS fe_monitoring,
            COALESCE(
                SUM(t1.tonnage * t1.mgo) / 
                NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.mgo IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),
                0
                ) AS mgo_monitoring,
            COALESCE(
                SUM(t1.tonnage * t1.sio2) / 
                NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.sio2 IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),
                0
                ) AS sio2_monitoring,
            -- Tonnage dan Ni dari split (gabungan dari tabel barge_split)
            COALESCE(t4.tonnage_split, 0) AS tonnage_split,
            COALESCE(t4.ni_split, 0) AS ni_split,
            COALESCE(t4.co_split, 0) AS co_split,
            COALESCE(t4.fe_split, 0) AS fe_split,
            COALESCE(t4.mgo_split, 0) AS mgo_split,
            COALESCE(t4.sio2_split, 0) AS sio2_split,
            -- Tonnage dan Ni official
            COALESCE(t2.tonnage_official, 0) AS tonnage_official,
            COALESCE(t2.ni, 0) AS ni_official,
            COALESCE(t2.co, 0) AS co_official,
            COALESCE(t2.fe, 0) AS fe_official,
            COALESCE(t2.mgo, 0) AS mgo_official,
            COALESCE(t2.sio2, 0) AS sio2_official,
            -- Ni plan
            COALESCE(t3.ni_plan, 0) AS ni_plan,
            COALESCE(t3.co_plan, 0) AS co_plan,
            COALESCE(t3.fe_plan, 0) AS fe_plan,
            COALESCE(t3.mgo_plan, 0) AS mgo_plan,
            COALESCE(t3.sio2_plan, 0) AS sio2_plan
        FROM details_selling_monitoring t1
        LEFT JOIN (
            SELECT 
                product_code,
                COALESCE(SUM(tonnage), 0) AS tonnage_official,
                COALESCE(SUM(ni), 0) AS ni,
                COALESCE(SUM(co), 0) AS co,
                COALESCE(SUM(fe), 0) AS fe,
                COALESCE(SUM(mgo), 0) AS mgo,
                COALESCE(SUM(sio2), 0) AS sio2,
                type_selling
            FROM sellings_official_view
            GROUP BY product_code, type_selling
        ) AS t2 ON t1.code_lot = t2.product_code
        LEFT JOIN (
            SELECT 
                product_code,
                COALESCE(SUM(tonnage), 0) AS tonnage_plan,
                COALESCE(SUM(ni), 0) AS ni_plan,
                COALESCE(SUM(co), 0) AS co_plan,
                COALESCE(SUM(fe), 0) AS fe_plan,
                COALESCE(SUM(mgo), 0) AS mgo_plan,
                COALESCE(SUM(sio2), 0) AS sio2_plan
            FROM ore_selling_code_product
            GROUP BY product_code
        ) AS t3 ON t1.code_lot = t3.product_code
        LEFT JOIN (
            -- Subquery untuk ambil data dari details_selling_barge_split (sumber ni_split)
            SELECT 
                code_lot,
                barge_code,
                COALESCE(SUM(tonnage), 0) AS tonnage_split,
                COALESCE(
                    SUM(tonnage * ni) / 
                    NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND ni IS NOT NULL THEN tonnage ELSE 0 END), 0),
                    0
                ) AS ni_split,
                COALESCE(
                    SUM(tonnage * co) / 
                    NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND co IS NOT NULL THEN tonnage ELSE 0 END), 0),
                    0
                ) AS co_split,
                COALESCE(
                    SUM(tonnage * fe) / 
                    NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND fe IS NOT NULL THEN tonnage ELSE 0 END), 0),
                    0
                ) AS fe_split,
                COALESCE(
                    SUM(tonnage * mgo) / 
                    NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND mgo IS NOT NULL THEN tonnage ELSE 0 END), 0),
                    0
                ) AS mgo_split,
                COALESCE(
                    SUM(tonnage * sio2) / 
                    NULLIF(SUM(CASE WHEN sample_number IS NOT NULL AND sio2 IS NOT NULL THEN tonnage ELSE 0 END), 0),
                    0
                ) AS sio2_split
            FROM details_selling_barge_split
            GROUP BY code_lot, barge_code
        ) AS t4 ON t1.code_lot = t4.code_lot AND t1.barge_code = t4.barge_code
        WHERE 1=1
    """

     # **Filter pada query utama t1**
    params = []
    
    if typeFilter:
        sql_query += " AND t1.sale_adjust = %s"
        params.append(typeFilter)

    if startDate and endDate:
        sql_query += " AND t1.date_hauling BETWEEN %s AND %s"
        params.extend([startDate, endDate])

    #  Filter berdasarkan bulan & tahun
    if bulanFilter and tahunFilter:
        sql_query += " AND EXTRACT(MONTH FROM t1.date_barge_out) = %s AND EXTRACT(YEAR FROM t1.date_barge_out) = %s"
        params.extend([bulanFilter, tahunFilter])
    elif tahunFilter:
        sql_query += " AND EXTRACT(YEAR FROM t1.date_barge_out) = %s"
        params.append(tahunFilter)

    if codeFilter:
        placeholders = ', '.join(['%s'] * len(codeFilter))
        sql_query += f" AND t1.code_lot IN ({placeholders})"
        params.extend(codeFilter)

    sql_query += """
        GROUP BY 
            t1.date_barge_in,t1.code_lot,t1.barge_code,
            t2.tonnage_official,t2.ni,t2.co,t2.fe,t2.mgo,t2.sio2,
            t3.ni_plan,t3.co_plan,t3.fe_plan,t3.mgo_plan,t3.sio2_plan,   
            t4.tonnage_split,t4.ni_split,t4.co_split,t4.fe_split,t4.mgo_split,t4.sio2_split
        ORDER BY t1.code_lot ASC
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