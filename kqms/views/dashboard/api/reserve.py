# views.py
import logging
from django.http import JsonResponse
from django.db import connections, DatabaseError
from prophet import Prophet
import pandas as pd

import itertools
from django.db.models import Sum
from django.utils.timezone import now
from django.db.models.functions import TruncWeek
logger = logging.getLogger(__name__) #tambahkan ini untuk multi database.
import json
from ....utils.db_utils import get_db_vendor
logger = logging.getLogger(__name__)
# Memanggil fungsi utility
db_vendor = get_db_vendor('kqms_db')

class NaNEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, float) and (obj != obj):  # Memeriksa NaN
            return None
        return super().default(obj)



def to_float1(value):
    try:
        return round(float(value or 0), 1)
    except Exception:
        return 0.0


# ======================================
# Query Builder
# ======================================
def build_summary_query(db_vendor: str, where_clause: str, where_barge: str) -> str:
    if db_vendor == 'postgresql':
        return f"""
            SELECT 
                -- Total Reserve (dari mine_reserve)
                COALESCE(SUM(r.tonnage), 0) AS reserve_ton,

                -- Total Production (pakai filter dinamis)
                COALESCE((
                    SELECT ROUND(SUM(CASE WHEN nama_material IN ('LIM', 'SAP') THEN tonnage ELSE 0 END)::numeric, 2)
                    FROM ore_production {where_clause}
                ), 0) AS prod_ton,

                -- Total Sales (pakai filter date_barge_out dan status_barging)
                COALESCE((
                    SELECT ROUND(SUM(s.tonnage)::numeric, 2)
                    FROM ore_sellings_barging s
                    {where_barge}
                ), 0) AS sales_ton,

                -- Persentase produksi vs reserve
                COALESCE((
                    (SELECT SUM(CASE WHEN nama_material IN ('LIM', 'SAP') THEN tonnage ELSE 0 END)
                     FROM ore_production {where_clause}) /
                    NULLIF(SUM(r.tonnage), 0) * 100
                ), 0) AS percent_mined,

                -- Persentase penjualan vs reserve
                COALESCE((
                    (SELECT SUM(s.tonnage)
                     FROM ore_sellings_barging s {where_barge}) /
                    NULLIF(SUM(r.tonnage), 0) * 100
                ), 0) AS percent_sold

            FROM mine_reserve r
        """
    else:
        raise ValueError("Unsupported vendor")


# ======================================
# Main Function
# ======================================
def get_reserve_summary(request):
    try:
        db_vendor = connections['kqms_db'].vendor
        filter_type = request.GET.get('filter_type')
        year        = request.GET.get('year')
        month       = request.GET.get('month')
        week        = request.GET.get('week')
        date_start  = request.GET.get('date_start')
        date_end    = request.GET.get('date_end')
        filter_date = request.GET.get('filter_date')

        where_clause = "WHERE 1=1"
        where_barge  = "WHERE status_barging = 'Complete'"
        params = []

        # === FILTER LOGIC ===
        if filter_type == 'daily' and filter_date:
            where_clause += " AND tgl_production <= %s"
            where_barge  += " AND date_barge_out <= %s"
            params = [filter_date, filter_date]

        elif filter_type == 'range' and date_end:
            where_clause += " AND tgl_production <= %s"
            where_barge  += " AND date_barge_out <= %s"
            params = [date_end, date_end]

        elif filter_type == 'weekly' and week:
            if db_vendor == 'postgresql':
                where_clause += """
                    AND (
                        (EXTRACT(YEAR FROM tgl_production)::int < SPLIT_PART(%s, '-', 1)::int)
                        OR
                        (EXTRACT(YEAR FROM tgl_production)::int = SPLIT_PART(%s, '-', 1)::int
                        AND EXTRACT(WEEK FROM tgl_production)::int <= SPLIT_PART(%s, '-', 2)::int)
                    )
                """
                where_barge += """
                    AND (
                        (EXTRACT(YEAR FROM date_barge_out)::int < SPLIT_PART(%s, '-', 1)::int)
                        OR
                        (EXTRACT(YEAR FROM date_barge_out)::int = SPLIT_PART(%s, '-', 1)::int
                        AND EXTRACT(WEEK FROM date_barge_out)::int <= SPLIT_PART(%s, '-', 2)::int)
                    )
                """
                params = [week, week, week, week, week, week]

        elif filter_type == 'monthly' and year and month:
            if db_vendor == 'postgresql':
                where_clause += " AND EXTRACT(YEAR FROM tgl_production) = %s AND EXTRACT(MONTH FROM tgl_production) <= %s"
                where_barge  += " AND EXTRACT(YEAR FROM date_barge_out) = %s AND EXTRACT(MONTH FROM date_barge_out) <= %s"
            else:
                where_clause += " AND YEAR(tgl_production) = %s AND MONTH(tgl_production) <= %s"
                where_barge  += " AND YEAR(date_barge_out) = %s AND MONTH(date_barge_out) <= %s"
            params = [year, month, year, month]

        elif filter_type == 'yearly' and year:
            if db_vendor == 'postgresql':
                where_clause += " AND EXTRACT(YEAR FROM tgl_production) <= %s"
                where_barge  += " AND EXTRACT(YEAR FROM date_barge_out) <= %s"
            else:
                where_clause += " AND YEAR(tgl_production) <= %s"
                where_barge  += " AND YEAR(date_barge_out) <= %s"
            params = [year, year]

        elif filter_type == 'all':
            params = []

        else:
            return JsonResponse({'error': 'Invalid or missing filter type'}, status=400)

        # === BUILD QUERY ===
        query = build_summary_query(db_vendor, where_clause, where_barge)

        # === DUPLICATE PARAMS (karena subquery dipakai dua kali) ===
        params = params * 2

        # === PARAM CHECK ===
        expected = query.count("%s")
        if expected != len(params):
            logger.warning(f"⚠️ Param mismatch: query expects {expected}, got {len(params)}")
            logger.warning(f"Params: {params}")

        # === EXECUTE QUERY ===
        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()

        # === RESPONSE ===
        return JsonResponse({
            "reserve_ton"   : to_float1(row[0]),
            "prod_ton"      : to_float1(row[1]),
            "sales_ton"     : to_float1(row[2]),
            "percent_mined" : to_float1(row[3]),
            "percent_sold"  : to_float1(row[4]),
        })

    except DatabaseError:
        logger.exception("Database query failed.")
        return JsonResponse({'error': 'Database error'}, status=500)
    except Exception as e:
        logger.exception("Unexpected error in get_reserve_summary")
        return JsonResponse({'error': str(e)}, status=500)
