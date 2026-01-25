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
from kqms.utils.db_utils import get_db_vendor
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

def dictfetchone(cursor):
    desc = [col[0] for col in cursor.description]
    row = cursor.fetchone()
    return dict(zip(desc, row)) if row else {}

# ======================================
# Query Builder
# ======================================
def build_summary_query(db_vendor: str, where_clause: str, where_barge: str) -> str:
    if db_vendor == 'postgresql':
        return f"""
            WITH base AS (
            SELECT
                -- Reserve awal
                COALESCE(SUM(r.tonnage), 0) AS reserve_awal
            FROM mine_reserve r
        ),
        prod AS (
            SELECT
                COALESCE(SUM(
                    CASE WHEN nama_material IN ('LIM', 'SAP') THEN tonnage ELSE 0 END
                ), 0) AS prod_ton
            FROM ore_production
            {where_clause}
        ),
        sales AS (
            SELECT
                COALESCE(SUM(s.tonnage), 0) AS sales_ton
            FROM ore_sellings_barging s
            {where_barge}
        )
        SELECT
            base.reserve_awal,
            prod.prod_ton,
            sales.sales_ton,
            -- remaining reserve
            (base.reserve_awal - prod.prod_ton - sales.sales_ton) AS remaining_reserve,
            -- percent mined
            CASE
                WHEN base.reserve_awal = 0 THEN 0
                ELSE (prod.prod_ton / base.reserve_awal) * 100
            END AS percent_mined,
            -- percent sold
            CASE
                WHEN base.reserve_awal = 0 THEN 0
                ELSE (sales.sales_ton / base.reserve_awal) * 100
            END AS percent_sold
        FROM base, prod, sales;
        """
    else:
        raise ValueError("Unsupported vendor")

# ======================================
# Main Function
# ======================================
def get_reserve_summary_daily(request):
    try:
        db_vendor = connections['kqms_db'].vendor
        filter_date = request.GET.get('filter_date')

        where_clause = "WHERE 1=1"
        where_barge  = "WHERE status_barging = 'Complete'"
        params = []

        # === FILTER LOGIC ===
        where_clause += " AND tgl_production <= %s"
        where_barge  += " AND date_barge_out <= %s"
        params = [filter_date, filter_date]


        # === BUILD QUERY ===
        query = build_summary_query(db_vendor, where_clause, where_barge)

        # === DUPLICATE PARAMS (karena subquery dipakai dua kali) ===
        # params = params * 2

        # === PARAM CHECK ===
        expected = query.count("%s")
        if expected != len(params):
            logger.warning(f"Param mismatch: query expects {expected}, got {len(params)}")
            logger.warning(f"Params: {params}")

        # === EXECUTE QUERY ===
        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            row = dictfetchone(cursor)

        return JsonResponse({
            "reserve_ton"       : to_float1(row["reserve_awal"]),
            "prod_ton"          : to_float1(row["prod_ton"]),
            "sales_ton"         : to_float1(row["sales_ton"]),
            "remaining_reserve" : to_float1(row["remaining_reserve"]),
            "percent_mined"     : round(to_float1(row["percent_mined"]), 2),
            "percent_sold"      : round(to_float1(row["percent_sold"]), 2),
        })


    except DatabaseError:
        logger.exception("Database query failed.")
        return JsonResponse({'error': 'Database error'}, status=500)
    except Exception as e:
        logger.exception("Unexpected error in get_reserve_summary")
        return JsonResponse({'error': str(e)}, status=500)
