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

@login_required
def splitOfficialPage(request):
    return render(request, 'admin-selling/official/list-coa.html')

def splitSamplePage(request):
    return render(request, 'admin-selling/split/list-samples.html')

@login_required
def rangeSplitHpal(request):
    code_lot       = request.GET.get('code_lot')
    startDate      = request.GET.get('startDate')
    endDate        = request.GET.get('endDate')
    bulanFilter    = request.GET.get('bulanFilter')
    tahunFilter    = request.GET.get('tahunFilter')
    materialFilter = request.GET.get('materialFilter')

    sql_query = """
                SELECT 
                    code_lot,
                    sum(tonnage) AS tonnage,
                    COALESCE(sum(tonnage * ni) / NULLIF(sum(
                        CASE
                            WHEN sample_number IS NOT NULL AND ni IS NOT NULL THEN tonnage
                            ELSE 0::double precision
                        END), 0::double precision), 0::double precision) AS ni,
                    COALESCE(sum(tonnage * fe) / NULLIF(sum(
                        CASE
                            WHEN sample_number IS NOT NULL AND fe IS NOT NULL THEN tonnage
                            ELSE 0::double precision
                        END), 0::double precision), 0::double precision) AS fe,
                    COALESCE(sum(tonnage * co) / NULLIF(sum(
                        CASE
                            WHEN sample_number IS NOT NULL AND co IS NOT NULL THEN tonnage
                            ELSE 0::double precision
                        END), 0::double precision), 0::double precision) AS co,
                    COALESCE(sum(tonnage * mgo) / NULLIF(sum(
                        CASE
                            WHEN sample_number IS NOT NULL AND mgo IS NOT NULL THEN tonnage
                            ELSE 0::double precision
                        END), 0::double precision), 0::double precision) AS mgo,
                    COALESCE(sum(tonnage * sio2) / NULLIF(sum(
                        CASE
                            WHEN sample_number IS NOT NULL AND sio2 IS NOT NULL THEN tonnage
                            ELSE 0::double precision
                        END), 0::double precision), 0::double precision) AS sio2,
                    COALESCE(sum(tonnage * mc) / NULLIF(sum(
                        CASE
                            WHEN sample_number IS NOT NULL AND mc IS NOT NULL THEN tonnage
                            ELSE 0::double precision
                        END), 0::double precision), 0::double precision) AS mc
                FROM details_selling_barge_split
                WHERE sale_adjust = 'HPAL'::text
        """

    if code_lot:
        sql_query += f" AND code_lot = '{code_lot}'"

    if materialFilter:
        sql_query += f" AND sale_adjust = '{materialFilter}'"    

    if startDate and endDate:
        sql_query += f" AND date_hauling BETWEEN '{startDate}' AND '{endDate}'"

    if bulanFilter and tahunFilter:
        sql_query += f" AND MONTH(date_hauling) = {bulanFilter} AND YEAR(date_hauling) = {tahunFilter}"

    if tahunFilter:
        sql_query += f" AND YEAR(date_hauling) = {tahunFilter}"
    
    sql_query += """
            GROUP BY code_lot,sale_adjust
            ORDER BY code_lot ASC
        """

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(sql_query)
        columns = [col[0] for col in cursor.description]
        sql_data = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
    # print(data)  # Cetak hasil query
    return JsonResponse({'data': sql_data})

@login_required
def rangeSplitPulpHpal(request):
    code_lot = request.GET.get('code_lot')
    startDate      = request.GET.get('startDate')
    endDate        = request.GET.get('endDate')
    bulanFilter    = request.GET.get('bulanFilter')
    tahunFilter    = request.GET.get('tahunFilter')
    materialFilter = request.GET.get('materialFilter')

    sql_query = """
            SELECT 
                code_lot,
                sum(tonnage) AS tonnage,
                COALESCE(sum(tonnage * ni) / NULLIF(sum(
                    CASE
                        WHEN sample_number IS NOT NULL AND ni IS NOT NULL THEN tonnage
                        ELSE 0::double precision
                    END), 0::double precision), 0::double precision) AS ni,
                COALESCE(sum(tonnage * fe) / NULLIF(sum(
                    CASE
                        WHEN sample_number IS NOT NULL AND fe IS NOT NULL THEN tonnage
                        ELSE 0::double precision
                    END), 0::double precision), 0::double precision) AS fe,
                COALESCE(sum(tonnage * co) / NULLIF(sum(
                    CASE
                        WHEN sample_number IS NOT NULL AND co IS NOT NULL THEN tonnage
                        ELSE 0::double precision
                    END), 0::double precision), 0::double precision) AS co,
                COALESCE(sum(tonnage * mgo) / NULLIF(sum(
                    CASE
                        WHEN sample_number IS NOT NULL AND mgo IS NOT NULL THEN tonnage
                        ELSE 0::double precision
                    END), 0::double precision), 0::double precision) AS mgo,
                COALESCE(sum(tonnage * sio2) / NULLIF(sum(
                    CASE
                        WHEN sample_number IS NOT NULL AND sio2 IS NOT NULL THEN tonnage
                        ELSE 0::double precision
                    END), 0::double precision), 0::double precision) AS sio2,
                COALESCE(sum(tonnage * mc) / NULLIF(sum(
                    CASE
                        WHEN sample_number IS NOT NULL AND mc IS NOT NULL THEN tonnage
                        ELSE 0::double precision
                    END), 0::double precision), 0::double precision) AS mc
            FROM
            details_selling_barge_split_pulp
            WHERE sale_adjust = 'HPAL'::text
        """
    
    if code_lot:
        sql_query += f" AND code_lot = '{code_lot}'"

    if materialFilter:
        sql_query += f" AND sale_adjust = '{materialFilter}'"    

    if startDate and endDate:
        sql_query += f" AND date_hauling BETWEEN '{startDate}' AND '{endDate}'"

    if bulanFilter and tahunFilter:
        sql_query += f" AND MONTH(date_hauling) = {bulanFilter} AND YEAR(date_hauling) = {tahunFilter}"

    if tahunFilter:
        sql_query += f" AND YEAR(date_hauling) = {tahunFilter}"

    sql_query += """
            GROUP BY code_lot,sale_adjust
            ORDER BY code_lot ASC
        """

    # with connection.cursor() as cursor:
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(sql_query)
        columns = [col[0] for col in cursor.description]
        sql_data = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
    # print(data)  # Cetak hasil query
    
    return JsonResponse({'data': sql_data})

@login_required
def rangeOfficial(request):
    materialFilter = request.GET.get('materialFilter')
    startDate      = request.GET.get('startDate')
    endDate        = request.GET.get('endDate')
    bulanFilter    = request.GET.get('bulanFilter')
    tahunFilter    = request.GET.get('tahunFilter')

    sql_query = """
            SELECT 
                DISTINCT details_selling_barge_split.code_lot,
                sellings_official_view.product_code,
                sellings_official_view.so_number,
                COALESCE(sellings_official_view.tonnage,'0') as tonnage,
                COALESCE(sellings_official_view.ni,'0') as ni,
                COALESCE(sellings_official_view.co,'0') as co,
                COALESCE(sellings_official_view.al2o3,'0')as al2o3,
                COALESCE(sellings_official_view.fe,'0') as fe,
                COALESCE(sellings_official_view.mgo,'0') as mgo,
                COALESCE(sellings_official_view.sio2,'0') as sio2,
                COALESCE(sellings_official_view.mc,'0') as mc
            FROM 
                sellings_official_view          
            LEFT JOIN  
                details_selling_barge_split ON details_selling_barge_split.code_lot = sellings_official_view.product_code
        """

    if materialFilter:
        sql_query += f" WHERE sale_adjust = '{materialFilter}'"
  
    if startDate and endDate:
        sql_query += f" AND date_hauling BETWEEN '{startDate}' AND '{endDate}'"

    if bulanFilter and tahunFilter:
        sql_query += f" AND MONTH(date_hauling) = {bulanFilter} AND YEAR(date_hauling) = {tahunFilter}"

    if tahunFilter:
        sql_query += f" AND YEAR(date_hauling) = {tahunFilter}"

    sql_query += """
            ORDER BY code_lot ASC
        """

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(sql_query)
        columns = [col[0] for col in cursor.description]
        sql_data = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
    # print(data)  # Cetak hasil query
    
    return JsonResponse({'data': sql_data})

def samplesSplit(request):
    typeFilter   = request.GET.get('typeFilter')
    startDate    = request.GET.get('startDate')
    endDate      = request.GET.get('endDate')
    codeFilter   = json.loads(request.GET.get('codeFilter', '[]'))

    # Filter list codeFilter
    codeFilter = [sanitize_input(code) for code in codeFilter if code]

    sql_query = """
       SELECT 
            TRIM(t1.code_lot)code_lot,
            TRIM(t1.code_sub) code_sub,
            TRIM(t1.sample_number) sample_number,
            COALESCE(SUM(t1.tonnage), 0) AS tonnage_split,              
            COALESCE(SUM(t1.tonnage * t1.ni) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.ni IS NOT NULL THEN t1.tonnage ELSE 0 END), 0) AS ni_split,
            COALESCE(SUM(t1.tonnage * t1.co) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.co IS NOT NULL THEN t1.tonnage ELSE 0 END), 0) AS co_split,
            COALESCE(SUM(t1.tonnage * t1.fe) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.fe IS NOT NULL THEN t1.tonnage ELSE 0 END), 0) AS fe_split,
            COALESCE(SUM(t1.tonnage * t1.mgo) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.mgo IS NOT NULL THEN t1.tonnage ELSE 0 END), 0) AS mgo_split,
            COALESCE(SUM(t1.tonnage * t1.sio2) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.sio2 IS NOT NULL THEN t1.tonnage ELSE 0 END), 0) AS sio2_split,
            COALESCE(t2.tonnage_pulp, 0) AS tonnage_pulp,
            COALESCE(t2.ni, 0) AS ni_pulp,
            COALESCE(t2.co, 0) AS co_pulp,
            COALESCE(t2.fe, 0) AS fe_pulp,
            COALESCE(t2.mgo, 0) AS mgo_pulp,
            COALESCE(t2.sio2, 0) AS sio2_pulp
        FROM details_selling_barge_split AS t1
        LEFT JOIN (
            SELECT 
                code_lot,
                code_sub,
                sample_number,
                COALESCE(SUM(tonnage), 0) AS tonnage_pulp,
                COALESCE(SUM(tonnage * ni) / SUM(CASE WHEN sample_number IS NOT NULL AND ni IS NOT NULL THEN tonnage ELSE 0 END), 0) AS ni,
                COALESCE(SUM(tonnage * co) / SUM(CASE WHEN sample_number IS NOT NULL AND co IS NOT NULL THEN tonnage ELSE 0 END), 0) AS co,
                COALESCE(SUM(tonnage * fe) / SUM(CASE WHEN sample_number IS NOT NULL AND fe IS NOT NULL THEN tonnage ELSE 0 END), 0) AS fe,
                COALESCE(SUM(tonnage * mgo) / SUM(CASE WHEN sample_number IS NOT NULL AND mgo IS NOT NULL THEN tonnage ELSE 0 END), 0) AS mgo,
                COALESCE(SUM(tonnage * sio2) / SUM(CASE WHEN sample_number IS NOT NULL AND sio2 IS NOT NULL THEN tonnage ELSE 0 END), 0) AS sio2
            FROM details_selling_barge_split_pulp
            GROUP BY code_lot,code_sub,sample_number) AS t2 ON t1.code_lot = t2.code_lot AND t1.code_sub=t2.code_sub
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

    if codeFilter:
        placeholders = ', '.join(['%s'] * len(codeFilter))
        sql_query += f" AND t1.code_lot IN ({placeholders})"
        params.extend(codeFilter)

    sql_query += """
        GROUP BY t1.code_lot, t1.code_sub, t1.sample_number, 
                 t2.tonnage_pulp, t2.ni, t2.co, t2.fe, t2.mgo, t2.sio2
        ORDER BY t1.code_lot, t1.code_lot ASC
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

def splitOfficial(request):
    typeFilter   = request.GET.get('materialFilter')
    startDate    = request.GET.get('startDate')
    endDate      = request.GET.get('endDate')
    bulanFilter  = request.GET.get('bulanFilter')
    tahunFilter  = request.GET.get('tahunFilter')

    sql_query = """
        SELECT 
                TRIM(t1.code_lot)code_lot,
                COALESCE(SUM(t1.tonnage), 0) AS tonnage_split,              
                COALESCE(SUM(t1.tonnage * t1.ni) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.ni IS NOT NULL THEN t1.tonnage ELSE 0 END), 0) AS ni_split,
                COALESCE(SUM(t1.tonnage * t1.co) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.co IS NOT NULL THEN t1.tonnage ELSE 0 END), 0) AS co_split,
                COALESCE(SUM(t1.tonnage * t1.fe) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.fe IS NOT NULL THEN t1.tonnage ELSE 0 END), 0) AS fe_split,
                COALESCE(SUM(t1.tonnage * t1.al2o3) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.al2o3 IS NOT NULL THEN t1.tonnage ELSE 0 END), 0) AS al2o3_split,
                COALESCE(SUM(t1.tonnage * t1.mgo) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.mgo IS NOT NULL THEN t1.tonnage ELSE 0 END), 0) AS mgo_split,
                COALESCE(SUM(t1.tonnage * t1.sio2) / SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.sio2 IS NOT NULL THEN t1.tonnage ELSE 0 END), 0) AS sio2_split,
                COALESCE(t3.tonnage_pulp, 0) AS tonnage_pulp,
                COALESCE(t3.ni, 0) AS ni_pulp,
                COALESCE(t3.co, 0) AS co_pulp,
                COALESCE(t3.fe, 0) AS fe_pulp,
                COALESCE(t3.al2o3, 0) AS al2o3_pulp,
                COALESCE(t3.mgo, 0) AS mgo_pulp,
                COALESCE(t3.sio2, 0) AS sio2_pulp,
                COALESCE(t2.tonnage_official, 0) AS tonnage_official,
                COALESCE(t2.ni, 0) AS ni_official,
                COALESCE(t2.co, 0) AS co_official, 
                COALESCE(t2.fe, 0) AS fe_official, 
                COALESCE(t2.al2o3, 0) AS al2o3_official,
                COALESCE(t2.mgo, 0) AS mgo_official,
                COALESCE(t2.sio2, 0) AS sio2_official
            FROM details_selling_barge_split AS t1
            LEFT JOIN (
                SELECT 
                    product_code,
                    COALESCE(SUM(tonnage), 0) AS tonnage_official,
                    COALESCE(SUM(ni), 0) AS ni,
                    COALESCE(SUM(co), 0) AS co,
                    COALESCE(SUM(fe), 0) AS fe,
                    COALESCE(SUM(al2o3), 0) AS al2o3,
                    COALESCE(SUM(mgo), 0) AS mgo,
                    COALESCE(SUM(sio2), 0) AS sio2,
                    type_selling
                FROM sellings_official_view
                GROUP BY product_code, type_selling
            ) AS t2 ON t1.code_lot = t2.product_code
            LEFT JOIN (
                SELECT 
                    code_lot,
                    COALESCE(SUM(tonnage), 0) AS tonnage_pulp,
                    COALESCE(SUM(tonnage * ni) / SUM(CASE WHEN sample_number IS NOT NULL AND ni IS NOT NULL THEN tonnage ELSE 0 END), 0) AS ni,
                    COALESCE(SUM(tonnage * co) / SUM(CASE WHEN sample_number IS NOT NULL AND co IS NOT NULL THEN tonnage ELSE 0 END), 0) AS co,
                    COALESCE(SUM(tonnage * fe) / SUM(CASE WHEN sample_number IS NOT NULL AND fe IS NOT NULL THEN tonnage ELSE 0 END), 0) AS fe,
                    COALESCE(SUM(tonnage * al2o3) / SUM(CASE WHEN sample_number IS NOT NULL AND al2o3 IS NOT NULL THEN tonnage ELSE 0 END), 0) AS al2o3,
                    COALESCE(SUM(tonnage * mgo) / SUM(CASE WHEN sample_number IS NOT NULL AND mgo IS NOT NULL THEN tonnage ELSE 0 END), 0) AS mgo,
                    COALESCE(SUM(tonnage * sio2) / SUM(CASE WHEN sample_number IS NOT NULL AND sio2 IS NOT NULL THEN tonnage ELSE 0 END), 0) AS sio2
                FROM details_selling_barge_split_pulp
                WHERE 1=1
    """

    # **Filter pada subquery t3**
    filters = []
    if startDate and endDate:
        filters.append(f"date_hauling BETWEEN '{startDate}' AND '{endDate}'")
    if bulanFilter and tahunFilter:
        filters.append(f"EXTRACT(MONTH FROM date_hauling) = {bulanFilter} AND EXTRACT(YEAR FROM date_hauling) = {tahunFilter}")
    elif tahunFilter:
        filters.append(f"EXTRACT(YEAR FROM date_hauling) = {tahunFilter}")

    if filters:
        sql_query += " AND " + " AND ".join(filters)

    sql_query += " GROUP BY code_lot ) AS t3 ON t1.code_lot = t3.code_lot WHERE 1=1"

    # **Filter pada query utama t1**
    filters = []
    if startDate and endDate:
        filters.append(f"t1.date_hauling BETWEEN '{startDate}' AND '{endDate}'")
    if typeFilter:
        filters.append(f"t2.type_selling = '{typeFilter}'")
    if bulanFilter and tahunFilter:
        filters.append(f"EXTRACT(MONTH FROM t1.date_hauling) = {bulanFilter} AND EXTRACT(YEAR FROM t1.date_hauling) = {tahunFilter}")
    elif tahunFilter:
        filters.append(f"EXTRACT(YEAR FROM t1.date_hauling) = {tahunFilter}")

    if filters:
        sql_query += " AND " + " AND ".join(filters)


    sql_query += """
        GROUP BY t1.code_lot, t3.tonnage_pulp, t2.tonnage_official,
         t3.ni, t2.ni,t3.co, t2.co,t3.fe, t2.fe,t3.al2o3, t2.al2o3,t3.mgo, t2.mgo,t3.sio2, t2.sio2
        ORDER BY t1.code_lot ASC
    """

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(sql_query)
        columns = [col[0] for col in cursor.description]
        sql_data = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        
    # print(sql_data)  # Cetak hasil query
    
    return JsonResponse({'data': sql_data})
