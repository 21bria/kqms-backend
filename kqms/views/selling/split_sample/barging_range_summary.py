from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import datetime
from django.db import connections, DatabaseError
from django.utils.html import escape
import json,re

# Fungsi untuk sanitasi input
def sanitize_input(value):
    if value is None:
        return None
    return escape(re.sub(r"[;'\"]", "", str(value)))

def samplesMonitoringSummary(request):
    data = get_samples_monitoring(
        typeFilter=request.GET.get("typeFilter"),
        startDate=request.GET.get("startDate"),
        endDate=request.GET.get("endDate"),
        bulanFilter=request.GET.get("bulanFilter"),
        tahunFilter=request.GET.get("tahunFilter")
    )
    return JsonResponse({"data": data}, safe=False)

def samplesReAssaySummary(request):
    data = get_samples_re_assay_summary(
        typeFilter=request.GET.get("typeFilter"),
        startDate=request.GET.get("startDate"),
        endDate=request.GET.get("endDate"),
        bulanFilter=request.GET.get("bulanFilter"),
        tahunFilter=request.GET.get("tahunFilter")
    )
    return JsonResponse({"data": data}, safe=False)

def shipmentSummaryBuyer(request):
    data = get_shipment_summary_buyer(
        typeFilter=request.GET.get("typeFilter"),
        startDate=request.GET.get("startDate"),
        endDate=request.GET.get("endDate"),
        bulanFilter=request.GET.get("bulanFilter"),
        tahunFilter=request.GET.get("tahunFilter")
    )
    return JsonResponse({"data": data}, safe=False)

def shipmentSummaryByMonth(request):
    data = get_shipment_summary_month(
        startDate=request.GET.get("startDate"),
        endDate=request.GET.get("endDate"),
    )
    return JsonResponse({"data": data}, safe=False)

def get_samples_monitoring(typeFilter=None, startDate=None, endDate=None, bulanFilter=None, tahunFilter=None):
    sql_query = """
       SELECT 
            t1.date_barge_out,
            TRIM(t1.barge_name) AS barge_name,
            COALESCE(SUM(t1.tonnage), 0) AS tonnage_split,
            COALESCE(
                    SUM(t1.tonnage * t1.ni) / 
                    NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.ni IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),
                    0
                ) AS ni_split,
            COALESCE(
                    SUM(t1.tonnage * t1.fe) / 
                    NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.fe IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),
                    0
                ) AS fe_split,
            COALESCE(
                    SUM(t1.tonnage * t1.sm) / 
                    NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.sm IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),
                    0
                ) AS sm_split,
            COALESCE(t2.tonnage_official, 0) AS tonnage_official,
            COALESCE(t2.ni, 0) AS ni_official,
            COALESCE(t2.fe, 0) AS fe_official,
            COALESCE(t2.sm, 0) AS sm_official,
            COALESCE((SUM(t1.tonnage * t1.ni) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.ni IS NOT NULL THEN t1.tonnage  ELSE 0 END), 0) )- t2.ni,0) AS ni_diff,
            COALESCE(((SUM(t1.tonnage * t1.ni) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.ni IS NOT NULL THEN t1.tonnage ELSE 0 END), 0)) - t2.ni) / NULLIF(t2.ni, 0) * 100, 0) AS ni_diff_perc,
            COALESCE((SUM(t1.tonnage * t1.fe) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.fe IS NOT NULL THEN t1.tonnage  ELSE 0 END), 0) )- t2.fe,0) AS fe_diff,
            COALESCE(((SUM(t1.tonnage * t1.fe) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.fe IS NOT NULL THEN t1.tonnage ELSE 0 END), 0)) - t2.fe) / NULLIF(t2.fe, 0) * 100, 0) AS fe_diff_perc,
            COALESCE((SUM(t1.tonnage * t1.sm) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.sm IS NOT NULL THEN t1.tonnage  ELSE 0 END), 0) )- t2.sm,0) AS sm_diff,
            COALESCE(((SUM(t1.tonnage * t1.sm) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.sm IS NOT NULL THEN t1.tonnage ELSE 0 END), 0)) - t2.sm) / NULLIF(t2.sm, 0) * 100, 0) AS sm_diff_perc
        FROM details_selling_barge_split t1
        LEFT JOIN (
            SELECT 
                product_code,
                COALESCE(SUM(tonnage), 0) AS tonnage_official,
                COALESCE(SUM(ni), 0) AS ni,
                COALESCE(SUM(fe), 0) AS fe,
                COALESCE(SUM(sm), 0) AS sm,
                type_selling
            FROM sellings_official_view
            WHERE re_assay = 1
            GROUP BY product_code, type_selling
        ) AS t2 ON t1.code_lot = t2.product_code
        WHERE 1=1
    """

    params = []
    if typeFilter:
        sql_query += " AND t1.sale_adjust = %s"
        params.append(typeFilter)
    if startDate and endDate:
        sql_query += " AND t1.date_hauling BETWEEN %s AND %s"
        params.extend([startDate, endDate])
    if bulanFilter and tahunFilter:
        sql_query += " AND EXTRACT(MONTH FROM t1.date_barge_out) = %s AND EXTRACT(YEAR FROM t1.date_barge_out) = %s"
        params.extend([bulanFilter, tahunFilter])
    elif tahunFilter:
        sql_query += " AND EXTRACT(YEAR FROM t1.date_barge_out) = %s"
        params.append(tahunFilter)

    sql_query += """
        GROUP BY 
            t1.date_barge_out,t1.code_lot,t1.barge_code,t1.barge_name,
            t2.tonnage_official,t2.ni,t2.fe,t2.sm
        ORDER BY t1.code_lot ASC
    """

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(sql_query, params)
        columns = [col[0] for col in cursor.description]
        sql_data = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    # **Kembalikan data Python murni, bukan JsonResponse**
    return sql_data

def get_samples_re_assay_summary(typeFilter=None, startDate=None, endDate=None, bulanFilter=None, tahunFilter=None):

    sql_query = """
       SELECT 
            t1.date_barge_out,
            TRIM(t1.barge_name) AS barge_name,
            COALESCE(SUM(t1.tonnage), 0) AS tonnage_split,
            COALESCE(
                    SUM(t1.tonnage * t1.ni) / 
                    NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.ni IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),
                    0
                ) AS ni_split,
            COALESCE(
                    SUM(t1.tonnage * t1.fe) / 
                    NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.fe IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),
                    0
                ) AS fe_split,
            COALESCE(
                    SUM(t1.tonnage * t1.sm) / 
                    NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.sm IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),
                    0
                ) AS sm_split,
            COALESCE(t2.tonnage_official, 0) AS tonnage_official,
            COALESCE(t2.ni, 0) AS ni_official,
            COALESCE(t2.fe, 0) AS fe_official,
            COALESCE(t2.sm, 0) AS sm_official,
            COALESCE((SUM(t1.tonnage * t1.ni) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.ni IS NOT NULL THEN t1.tonnage  ELSE 0 END), 0) )- t2.ni,0) AS ni_diff,
            COALESCE(((SUM(t1.tonnage * t1.ni) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.ni IS NOT NULL THEN t1.tonnage ELSE 0 END), 0)) - t2.ni) / NULLIF(t2.ni, 0) * 100, 0) AS ni_diff_perc,
            COALESCE((SUM(t1.tonnage * t1.fe) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.fe IS NOT NULL THEN t1.tonnage  ELSE 0 END), 0) )- t2.fe,0) AS fe_diff,
			COALESCE(((SUM(t1.tonnage * t1.fe) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.fe IS NOT NULL THEN t1.tonnage ELSE 0 END), 0)) - t2.fe) / NULLIF(t2.fe, 0) * 100, 0) AS fe_diff_perc,
			COALESCE((SUM(t1.tonnage * t1.sm) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.sm IS NOT NULL THEN t1.tonnage  ELSE 0 END), 0) )- t2.sm,0) AS sm_diff,
			COALESCE(((SUM(t1.tonnage * t1.sm) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.sm IS NOT NULL THEN t1.tonnage ELSE 0 END), 0)) - t2.sm) / NULLIF(t2.sm, 0) * 100, 0) AS sm_diff_perc,
            COALESCE(t2.re_assay,0) AS re_assay
        FROM details_selling_barge_split t1
        LEFT JOIN (
            SELECT 
                product_code,
                type_selling,
                tonnage_official,
                ni,
                fe,
                sm,
                re_assay
            FROM (
                SELECT 
                    product_code,
                    type_selling,
                    COALESCE(SUM(tonnage), 0) AS tonnage_official,
                    COALESCE(SUM(ni), 0) AS ni,
                    COALESCE(SUM(fe), 0) AS fe,
                    COALESCE(SUM(sm), 0) AS sm,
                    re_assay,
                    ROW_NUMBER() OVER(
                        PARTITION BY product_code
                        ORDER BY re_assay DESC
                    ) AS rn
                FROM sellings_official_view
                GROUP BY product_code, type_selling, re_assay
            ) x
            WHERE rn = 1
        ) AS t2 ON t1.code_lot = t2.product_code
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

    sql_query += """
        GROUP BY 
            t1.date_barge_out,t1.code_lot,t1.barge_code,t1.barge_name,
            t2.tonnage_official,t2.ni,t2.fe,t2.sm,t2.re_assay
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

     # **Kembalikan data Python murni, bukan JsonResponse**
    return sql_data

def get_shipment_summary_buyer(typeFilter=None, startDate=None, endDate=None, bulanFilter=None, tahunFilter=None):

    sql_query = """
       SELECT 
            TRIM(t1.factory_stock) AS buyer,
            t1.date_barge_out,
            TRIM(t1.barge_name) AS barge_name,
            COALESCE(SUM(t1.tonnage), 0) AS tonnage_split,
            COALESCE(
                    SUM(t1.tonnage * t1.ni) / 
                    NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.ni IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),
                    0
                ) AS ni_split,
            COALESCE(
                    SUM(t1.tonnage * t1.fe) / 
                    NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.fe IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),
                    0
                ) AS fe_split,
            COALESCE(
                    SUM(t1.tonnage * t1.sm) / 
                    NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.sm IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),
                    0
                ) AS sm_split,
            COALESCE(t2.tonnage_official, 0) AS tonnage_official,
            COALESCE(t2.ni, 0) AS ni_official,
            COALESCE(t2.fe, 0) AS fe_official,
            COALESCE(t2.sm, 0) AS sm_official,
            COALESCE((SUM(t1.tonnage * t1.ni) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.ni IS NOT NULL THEN t1.tonnage  ELSE 0 END), 0) )- t2.ni,0) AS ni_diff,
            COALESCE(((SUM(t1.tonnage * t1.ni) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.ni IS NOT NULL THEN t1.tonnage ELSE 0 END), 0)) - t2.ni) / NULLIF(t2.ni, 0) * 100, 0) AS ni_diff_perc,
            COALESCE((SUM(t1.tonnage * t1.fe) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.fe IS NOT NULL THEN t1.tonnage  ELSE 0 END), 0) )- t2.fe,0) AS fe_diff,
			COALESCE(((SUM(t1.tonnage * t1.fe) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.fe IS NOT NULL THEN t1.tonnage ELSE 0 END), 0)) - t2.fe) / NULLIF(t2.fe, 0) * 100, 0) AS fe_diff_perc,
			COALESCE((SUM(t1.tonnage * t1.sm) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.sm IS NOT NULL THEN t1.tonnage  ELSE 0 END), 0) )- t2.sm,0) AS sm_diff,
			COALESCE(((SUM(t1.tonnage * t1.sm) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.sm IS NOT NULL THEN t1.tonnage ELSE 0 END), 0)) - t2.sm) / NULLIF(t2.sm, 0) * 100, 0) AS sm_diff_perc
        FROM details_selling_barge_split t1
        LEFT JOIN (
            SELECT 
                product_code,
                tonnage_official,
                ni,
                fe,
                sm,
                type_selling
            FROM (
                SELECT 
                    product_code,
                    type_selling,
                    COALESCE(SUM(tonnage), 0) AS tonnage_official,
                    COALESCE(SUM(ni), 0) AS ni,
                    COALESCE(SUM(fe), 0) AS fe,
                    COALESCE(SUM(sm), 0) AS sm,
                    ROW_NUMBER() OVER(
                        PARTITION BY product_code 
                        ORDER BY re_assay DESC
                    ) AS rn
                FROM sellings_official_view
                GROUP BY product_code, type_selling, re_assay
            ) x
            WHERE rn = 1
        ) AS t2 
            ON t1.code_lot = t2.product_code
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

    sql_query += """
        GROUP BY 
            t1.factory_stock,t1.date_barge_out,t1.code_lot,t1.barge_code,t1.barge_name,
            t2.tonnage_official,t2.ni,t2.fe,t2.sm
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

    # **Kembalikan data Python murni, bukan JsonResponse**
    return sql_data

def get_shipment_summary_month(startDate=None,endDate=None):
    tahun = None
    if endDate:
        try:
            tahun = datetime.strptime(endDate, "%Y-%m-%d").year
        except:
            tahun = None

    sql_query = """
      WITH split_data AS (
            SELECT
                TRIM(factory_stock) AS buyer,
                EXTRACT(YEAR FROM date_barge_out)::int AS year,
                EXTRACT(MONTH FROM date_barge_out)::int AS month,
                TO_CHAR(date_barge_out, 'Mon') AS month_name,
                TRIM(type_selling) AS type_selling,
                COUNT(DISTINCT barge_code) AS total_barge,
                SUM(tonnage) AS tonnage_split,
                SUM(tonnage * ni) / NULLIF(SUM(CASE WHEN ni IS NOT NULL THEN tonnage ELSE 0 END),0) AS ni_split,
                SUM(tonnage * fe) / NULLIF(SUM(CASE WHEN fe IS NOT NULL THEN tonnage ELSE 0 END),0) AS fe_split,
                SUM(tonnage * sm) / NULLIF(SUM(CASE WHEN sm IS NOT NULL THEN tonnage ELSE 0 END),0) AS sm_split
            FROM details_selling_barge_split
            GROUP BY 1,2,3,4,5
        ),
        reassy_official AS (
            SELECT
                TRIM(factory_stock) AS buyer,
                EXTRACT(YEAR FROM end_date)::int AS year,
                EXTRACT(MONTH FROM end_date)::int AS month,
                TRIM(type_selling) AS type_selling,
                product_code,
                tonnage,
                ni,
                fe,
                sm,
                ROW_NUMBER() OVER(
                    PARTITION BY TRIM(factory_stock),
                                EXTRACT(YEAR FROM end_date),
                                EXTRACT(MONTH FROM end_date),
                                TRIM(type_selling),
                                product_code
                    ORDER BY re_assay DESC NULLS LAST
                ) AS rn
            FROM sellings_official_view
        ),
        official_data AS (
            SELECT
                buyer,
                year,
                month,
                type_selling,
                SUM(tonnage) AS tonnage_official,
                SUM(tonnage * ni) / NULLIF(SUM(CASE WHEN ni IS NOT NULL THEN tonnage ELSE 0 END),0) AS ni_official,
                SUM(tonnage * fe) / NULLIF(SUM(CASE WHEN fe IS NOT NULL THEN tonnage ELSE 0 END),0) AS fe_official,
                SUM(tonnage * sm) / NULLIF(SUM(CASE WHEN sm IS NOT NULL THEN tonnage ELSE 0 END),0) AS sm_official
            FROM reassy_official
            WHERE rn = 1
            GROUP BY 1,2,3,4
        )
        SELECT
            s.buyer,
            s.year,
            s.month,
            s.month_name,
            s.type_selling,
            s.total_barge,
            s.tonnage_split,
            s.ni_split, s.fe_split, s.sm_split,
            o.tonnage_official,
            o.ni_official, o.fe_official, o.sm_official,
            (s.ni_split - COALESCE(o.ni_official,0)) AS ni_diff,
            (s.ni_split - COALESCE(o.ni_official,0)) / NULLIF(o.ni_official,0) * 100 AS ni_diff_perc,
            (s.fe_split - COALESCE(o.fe_official,0)) AS fe_diff,
            (s.fe_split - COALESCE(o.fe_official,0)) / NULLIF(o.fe_official,0) *100 AS fe_diff_perc,
            (s.sm_split - COALESCE(o.sm_official,0)) AS sm_diff,
            (s.sm_split - COALESCE(o.sm_official,0)) / NULLIF(o.sm_official,0) *100 AS sm_diff_perc
        FROM split_data s
        LEFT JOIN official_data o
            ON s.buyer = o.buyer
            AND s.year = o.year
            AND s.month = o.month
            AND s.type_selling = o.type_selling
        WHERE 1=1
    """

     # **Filter pada query utama t1**
    params = []
    
    if tahun:
        sql_query += " AND s.year = %s"
        params.append(tahun)

    sql_query += """
       ORDER BY s.month, s.buyer, s.type_selling
    """

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(sql_query, params)
        columns = [col[0] for col in cursor.description]
        sql_data = []
        for row in cursor.fetchall():
            clean = {}
            for key, val in zip(columns, row):
                clean[key] = 0 if val is None else val
            sql_data.append(clean)

    # **Kembalikan data Python murni, bukan JsonResponse**
    return sql_data