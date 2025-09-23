# views.py
import logging
from django.http import JsonResponse
from django.db import connections, DatabaseError
from prophet import Prophet
import pandas as pd
import calendar
from datetime import datetime, timedelta
from ....utils.utils import validate_month,validate_year
from ....models.ore_productions import OreProductions
import itertools
from django.db.models import Sum
from django.utils.timezone import now
from django.db.models.functions import TruncWeek
logger = logging.getLogger(__name__) #tambahkan ini untuk multi database.
import json
from decimal import Decimal
from ....utils.db_utils import get_db_vendor

# Memanggil fungsi utility
db_vendor = get_db_vendor('kqms_db')

class NaNEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, float) and (obj != obj):  # Memeriksa NaN
            return None
        return super().default(obj)

def to_float1(v):
    return round(float(v or 0), 1)

def get_inventory_summary(request):
    try:
        db_vendor   = connections['kqms_db'].vendor
        filter_type = request.GET.get('filter_type')
        year        = request.GET.get('year')
        month       = request.GET.get('month')
        week        = request.GET.get('week')
        date_start  = request.GET.get('date_start')
        date_end    = request.GET.get('date_end')

        if filter_type =='range' and date_start and date_end: 
            if db_vendor == 'postgresql':
                query = """
                        WITH saldo_awal AS (
                            SELECT
                                -- Limonite
                                COALESCE((
                                    SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN tonnage ELSE 0 END)
                                    FROM ore_productions op
                                    LEFT JOIN materials m ON m.id = op.id_material
                                    WHERE tgl_production < %s
                                ), 0) -
                                COALESCE((
                                    SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END)
                                    FROM ore_sellings_barging s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_hauling < %s
                                ), 0) AS lim_awal,
                                -- Saprolite
                                COALESCE((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END)
                                    FROM ore_productions op
                                    LEFT JOIN materials m ON m.id = op.id_material
                                    WHERE tgl_production < %s
                                ), 0) -
                                COALESCE((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END)
                                    FROM ore_sellings_barging s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_hauling < %s
                                ), 0) AS sap_awal
                        ),
                        incoming AS (
                            SELECT
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN tonnage ELSE 0 END) AS lim_in,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END) AS sap_in
                            FROM ore_productions op
                            LEFT JOIN materials m ON m.id = op.id_material
                            WHERE tgl_production BETWEEN %s AND %s
                        ),
                        outgoing AS (
                            SELECT
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END) AS lim_out,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END) AS sap_out
                            FROM ore_sellings_barging s
                            LEFT JOIN materials m ON m.id = s.id_material
                            WHERE date_hauling BETWEEN %s AND %s
                        )
                        SELECT
                            -- LIM
                            COALESCE(i.lim_in, 0) AS lim_in,
                            COALESCE(o.lim_out, 0) AS lim_out,
                            sa.lim_awal + (COALESCE(i.lim_in, 0) - COALESCE(o.lim_out, 0)) AS lim_stock,

                            -- SAP
                            COALESCE(i.sap_in, 0) AS sap_in,
                            COALESCE(o.sap_out, 0) AS sap_out,
                            sa.sap_awal + (COALESCE(i.sap_in, 0) - COALESCE(o.sap_out, 0)) AS sap_stock,

                            -- TOTAL
                            COALESCE(i.lim_in, 0) + COALESCE(i.sap_in, 0) AS total_in,
                            COALESCE(o.lim_out, 0) + COALESCE(o.sap_out, 0) AS total_out,
                            (sa.lim_awal + sa.sap_awal) +
                            ((COALESCE(i.lim_in, 0) + COALESCE(i.sap_in, 0)) -
                            (COALESCE(o.lim_out, 0) + COALESCE(o.sap_out, 0))) AS total_stock
                        FROM incoming i, outgoing o, saldo_awal sa
                """
            else:
                query = """
                        WITH saldo_awal AS (
                            SELECT
                                -- Limonite
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN tonnage ELSE 0 END)
                                    FROM ore_productions op
                                    LEFT JOIN materials m ON m.id = op.id_material
                                    WHERE tgl_production < %s
                                ), 0) -
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END)
                                    FROM ore_sellings_barging s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_hauling < %s
                                ), 0) AS lim_awal,

                                -- Saprolite
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END)
                                    FROM ore_productions op
                                    LEFT JOIN materials m ON m.id = op.id_material
                                    WHERE tgl_production < %s
                                ), 0) -
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END)
                                    FROM ore_sellings_barging s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_hauling < %s
                                ), 0) AS sap_awal
                        ),
                        incoming AS (
                            SELECT
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN tonnage ELSE 0 END) AS lim_in,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END) AS sap_in
                            FROM ore_productions op
                            LEFT JOIN materials m ON m.id = op.id_material
                            WHERE tgl_production BETWEEN %s AND %s
                        ),
                        outgoing AS (
                            SELECT
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END) AS lim_out,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END) AS sap_out
                            FROM ore_sellings_barging s
                            LEFT JOIN materials m ON m.id = s.id_material
                            WHERE date_hauling BETWEEN %s AND %s
                        )
                        SELECT
                            ISNULL(i.lim_in, 0) AS lim_in,
                            ISNULL(o.lim_out, 0) AS lim_out,
                            sa.lim_awal + (ISNULL(i.lim_in, 0) - ISNULL(o.lim_out, 0)) AS lim_stock,

                            ISNULL(i.sap_in, 0) AS sap_in,
                            ISNULL(o.sap_out, 0) AS sap_out,
                            sa.sap_awal + (ISNULL(i.sap_in, 0) - ISNULL(o.sap_out, 0)) AS sap_stock,

                            ISNULL(i.lim_in, 0) + ISNULL(i.sap_in, 0) AS total_in,
                            ISNULL(o.lim_out, 0) + ISNULL(o.sap_out, 0) AS total_out,
                            (sa.lim_awal + sa.sap_awal)
                                + ((ISNULL(i.lim_in, 0) + ISNULL(i.sap_in, 0)) - (ISNULL(o.lim_out, 0) + ISNULL(o.sap_out, 0))) AS total_stock
                        FROM incoming i, outgoing o, saldo_awal sa
                """
            params = [date_start] * 4 + [date_start, date_end] * 2

        elif filter_type =='weekly' and year and month and week:
            try:
                print("RECEIVED:", {"year": year, "month": month, "week": week})

                # Deteksi jika 'week' dalam format ISO (contoh: '2025-03')
                if '-' in str(week):
                    year_str, week_str = str(week).split('-')
                    year = int(year_str)
                    week = int(week_str)

                    # Hitung awal minggu (ISO): Senin minggu ke-X
                    start_date = datetime.strptime(f'{year}-W{week:02}-1', "%G-W%V-%u")
                    end_date = start_date + timedelta(days=6)
                else:
                    # Parsing normal year, month, week
                    year = int(year)
                    month = int(month)
                    week = int(week)

                    if not (1 <= month <= 12):
                        return JsonResponse({"error": "Bulan tidak valid (1–12)"}, status=400)
                    if not (1 <= week <= 5):
                        return JsonResponse({"error": "Minggu tidak valid (1–5)"}, status=400)

                    first_day = datetime(year, month, 1)
                    start_date = first_day + timedelta(days=(week - 1) * 7)
                    end_date = start_date + timedelta(days=6)

                    # Koreksi akhir bulan
                    if end_date.month != month:
                        next_month = datetime(year, month, 28) + timedelta(days=4)
                        end_date = datetime(next_month.year, next_month.month, 1) - timedelta(days=1)
            except Exception as e:
                return JsonResponse({"error": f"Format tahun/bulan/minggu tidak valid: {str(e)}"}, status=400)
            
            # SQL Query
            if db_vendor == 'postgresql':
                query = """
                        WITH saldo_awal AS (
                            SELECT
                                -- Limonite
                                COALESCE((
                                    SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN tonnage ELSE 0 END)
                                    FROM ore_productions op
                                    LEFT JOIN materials m ON m.id = op.id_material
                                    WHERE tgl_production < %s
                                ), 0) -
                                COALESCE((
                                    SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END)
                                    FROM ore_sellings_barging s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_hauling < %s
                                ), 0) AS lim_awal,
                                -- Saprolite
                                COALESCE((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END)
                                    FROM ore_productions op
                                    LEFT JOIN materials m ON m.id = op.id_material
                                    WHERE tgl_production < %s
                                ), 0) -
                                COALESCE((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END)
                                    FROM ore_sellings_barging s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_hauling < %s
                                ), 0) AS sap_awal
                        ),
                        incoming AS (
                            SELECT
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN tonnage ELSE 0 END) AS lim_in,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END) AS sap_in
                            FROM ore_productions op
                            LEFT JOIN materials m ON m.id = op.id_material
                            WHERE tgl_production BETWEEN %s AND %s
                        ),
                        outgoing AS (
                            SELECT
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END) AS lim_out,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END) AS sap_out
                            FROM ore_sellings_barging s
                            LEFT JOIN materials m ON m.id = s.id_material
                            WHERE date_hauling BETWEEN %s AND %s
                        )
                        SELECT
                            -- LIM
                            COALESCE(i.lim_in, 0) AS lim_in,
                            COALESCE(o.lim_out, 0) AS lim_out,
                            sa.lim_awal + (COALESCE(i.lim_in, 0) - COALESCE(o.lim_out, 0)) AS lim_stock,

                            -- SAP
                            COALESCE(i.sap_in, 0) AS sap_in,
                            COALESCE(o.sap_out, 0) AS sap_out,
                            sa.sap_awal + (COALESCE(i.sap_in, 0) - COALESCE(o.sap_out, 0)) AS sap_stock,

                            -- TOTAL
                            COALESCE(i.lim_in, 0) + COALESCE(i.sap_in, 0) AS total_in,
                            COALESCE(o.lim_out, 0) + COALESCE(o.sap_out, 0) AS total_out,
                            (sa.lim_awal + sa.sap_awal) +
                            ((COALESCE(i.lim_in, 0) + COALESCE(i.sap_in, 0)) -
                            (COALESCE(o.lim_out, 0) + COALESCE(o.sap_out, 0))) AS total_stock
                        FROM incoming i, outgoing o, saldo_awal sa
                """
            else:
                query = """
                        WITH saldo_awal AS (
                            SELECT
                                -- Limonite
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN tonnage ELSE 0 END)
                                    FROM ore_productions op
                                    LEFT JOIN materials m ON m.id = op.id_material
                                    WHERE tgl_production < %s
                                ), 0) -
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END)
                                    FROM ore_sellings_barging s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_hauling < %s
                                ), 0) AS lim_awal,

                                -- Saprolite
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END)
                                    FROM ore_productions op
                                    LEFT JOIN materials m ON m.id = op.id_material
                                    WHERE tgl_production < %s
                                ), 0) -
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END)
                                    FROM ore_sellings_barging s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_hauling < %s
                                ), 0) AS sap_awal
                        ),
                        incoming AS (
                            SELECT
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN tonnage ELSE 0 END) AS lim_in,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END) AS sap_in
                            FROM ore_productions op
                            LEFT JOIN materials m ON m.id = op.id_material
                            WHERE tgl_production BETWEEN %s AND %s
                        ),
                        outgoing AS (
                            SELECT
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END) AS lim_out,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END) AS sap_out
                            FROM ore_sellings_barging s
                            LEFT JOIN materials m ON m.id = s.id_material
                            WHERE date_hauling BETWEEN %s AND %s
                        )
                        SELECT
                            ISNULL(i.lim_in, 0) AS lim_in,
                            ISNULL(o.lim_out, 0) AS lim_out,
                            sa.lim_awal + (ISNULL(i.lim_in, 0) - ISNULL(o.lim_out, 0)) AS lim_stock,

                            ISNULL(i.sap_in, 0) AS sap_in,
                            ISNULL(o.sap_out, 0) AS sap_out,
                            sa.sap_awal + (ISNULL(i.sap_in, 0) - ISNULL(o.sap_out, 0)) AS sap_stock,

                            ISNULL(i.lim_in, 0) + ISNULL(i.sap_in, 0) AS total_in,
                            ISNULL(o.lim_out, 0) + ISNULL(o.sap_out, 0) AS total_out,
                            (sa.lim_awal + sa.sap_awal)
                                + ((ISNULL(i.lim_in, 0) + ISNULL(i.sap_in, 0)) - (ISNULL(o.lim_out, 0) + ISNULL(o.sap_out, 0))) AS total_stock
                        FROM incoming i, outgoing o, saldo_awal sa
                """
            
            params = [
                start_date.strftime('%Y-%m-%d'),  # 1: tgl_production < %s
                start_date.strftime('%Y-%m-%d'),  # 2: date_hauling < %s
                start_date.strftime('%Y-%m-%d'),  # 3: tgl_production < %s
                start_date.strftime('%Y-%m-%d'),  # 4: date_hauling < %s
                start_date.strftime('%Y-%m-%d'),  # 5: BETWEEN
                end_date.strftime('%Y-%m-%d'),    # 6: BETWEEN
                start_date.strftime('%Y-%m-%d'),  # 7: BETWEEN
                end_date.strftime('%Y-%m-%d')     # 8: BETWEEN
            ]

        elif filter_type =='monthly' and year and month: 
            year  = int(year)
            month = int(month)

            # Ambil jumlah hari terakhir dalam bulan
            last_day = calendar.monthrange(year, month)[1]

            # Bangun tanggal awal dan akhir bulan
            tgl_pertama = datetime(year, month, 1).date()
            tgl_terakhir = datetime(year, month, last_day).date()

            params = [tgl_pertama] * 4 + [tgl_pertama, tgl_terakhir, tgl_pertama, tgl_terakhir]

            # SQL Query
            if db_vendor == 'postgresql':
                query = """
                        WITH saldo_awal AS (
                            SELECT
                                -- Limonite
                                COALESCE((
                                    SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN tonnage ELSE 0 END)
                                    FROM ore_productions op
                                    LEFT JOIN materials m ON m.id = op.id_material
                                    WHERE tgl_production < %s
                                ), 0) -
                                COALESCE((
                                    SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END)
                                    FROM ore_sellings_barging s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_hauling < %s
                                ), 0) AS lim_awal,
                                -- Saprolite
                                COALESCE((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END)
                                    FROM ore_productions op
                                    LEFT JOIN materials m ON m.id = op.id_material
                                    WHERE tgl_production < %s
                                ), 0) -
                                COALESCE((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END)
                                    FROM ore_sellings_barging s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_hauling < %s
                                ), 0) AS sap_awal
                        ),
                        incoming AS (
                            SELECT
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN tonnage ELSE 0 END) AS lim_in,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END) AS sap_in
                            FROM ore_productions op
                            LEFT JOIN materials m ON m.id = op.id_material
                            WHERE tgl_production BETWEEN %s AND %s
                        ),
                        outgoing AS (
                            SELECT
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END) AS lim_out,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END) AS sap_out
                            FROM ore_sellings_barging s
                            LEFT JOIN materials m ON m.id = s.id_material
                            WHERE date_hauling BETWEEN %s AND %s
                        )
                        SELECT
                            -- LIM
                            COALESCE(i.lim_in, 0) AS lim_in,
                            COALESCE(o.lim_out, 0) AS lim_out,
                            sa.lim_awal + (COALESCE(i.lim_in, 0) - COALESCE(o.lim_out, 0)) AS lim_stock,

                            -- SAP
                            COALESCE(i.sap_in, 0) AS sap_in,
                            COALESCE(o.sap_out, 0) AS sap_out,
                            sa.sap_awal + (COALESCE(i.sap_in, 0) - COALESCE(o.sap_out, 0)) AS sap_stock,

                            -- TOTAL
                            COALESCE(i.lim_in, 0) + COALESCE(i.sap_in, 0) AS total_in,
                            COALESCE(o.lim_out, 0) + COALESCE(o.sap_out, 0) AS total_out,
                            (sa.lim_awal + sa.sap_awal) +
                            ((COALESCE(i.lim_in, 0) + COALESCE(i.sap_in, 0)) -
                            (COALESCE(o.lim_out, 0) + COALESCE(o.sap_out, 0))) AS total_stock
                        FROM incoming i, outgoing o, saldo_awal sa
                """
            else:
                query = """
                        WITH saldo_awal AS (
                            SELECT
                                -- Limonite
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN tonnage ELSE 0 END)
                                    FROM ore_productions op
                                    LEFT JOIN materials m ON m.id = op.id_material
                                    WHERE tgl_production < %s
                                ), 0) -
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END)
                                    FROM ore_sellings_barging s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_hauling < %s
                                ), 0) AS lim_awal,

                                -- Saprolite
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END)
                                    FROM ore_productions op
                                    LEFT JOIN materials m ON m.id = op.id_material
                                    WHERE tgl_production < %s
                                ), 0) -
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END)
                                    FROM ore_sellings_barging s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_hauling < %s
                                ), 0) AS sap_awal
                        ),
                        incoming AS (
                            SELECT
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN tonnage ELSE 0 END) AS lim_in,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END) AS sap_in
                            FROM ore_productions op
                            LEFT JOIN materials m ON m.id = op.id_material
                            WHERE tgl_production BETWEEN %s AND %s
                        ),
                        outgoing AS (
                            SELECT
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END) AS lim_out,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END) AS sap_out
                            FROM ore_sellings_barging s
                            LEFT JOIN materials m ON m.id = s.id_material
                            WHERE date_hauling BETWEEN %s AND %s
                        )
                        SELECT
                            ISNULL(i.lim_in, 0) AS lim_in,
                            ISNULL(o.lim_out, 0) AS lim_out,
                            sa.lim_awal + (ISNULL(i.lim_in, 0) - ISNULL(o.lim_out, 0)) AS lim_stock,

                            ISNULL(i.sap_in, 0) AS sap_in,
                            ISNULL(o.sap_out, 0) AS sap_out,
                            sa.sap_awal + (ISNULL(i.sap_in, 0) - ISNULL(o.sap_out, 0)) AS sap_stock,

                            ISNULL(i.lim_in, 0) + ISNULL(i.sap_in, 0) AS total_in,
                            ISNULL(o.lim_out, 0) + ISNULL(o.sap_out, 0) AS total_out,
                            (sa.lim_awal + sa.sap_awal)
                                + ((ISNULL(i.lim_in, 0) + ISNULL(i.sap_in, 0)) - (ISNULL(o.lim_out, 0) + ISNULL(o.sap_out, 0))) AS total_stock
                        FROM incoming i, outgoing o, saldo_awal sa
                """
       
        elif filter_type =='yearly' and year: 
            year = int(year)
             # SQL Query
            if db_vendor == 'postgresql':
                query = """
                        WITH saldo_awal AS (
                            SELECT
                                -- Limonite
                                COALESCE((
                                    SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN tonnage ELSE 0 END)
                                    FROM ore_productions op
                                    LEFT JOIN materials m ON m.id = op.id_material
                                    WHERE EXTRACT(YEAR FROM tgl_production) < %s
                                ), 0) -
                                COALESCE((
                                    SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END)
                                    FROM ore_sellings_barging s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE EXTRACT(YEAR FROM date_hauling) < %s
                                ), 0) AS lim_awal,
                                -- Saprolite
                                COALESCE((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END)
                                    FROM ore_productions op
                                    LEFT JOIN materials m ON m.id = op.id_material
                                     WHERE EXTRACT(YEAR FROM tgl_production) < %s
                                ), 0) -
                                COALESCE((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END)
                                    FROM ore_sellings_barging s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE EXTRACT(YEAR FROM date_hauling) < %s
                                ), 0) AS sap_awal
                        ),
                        incoming AS (
                            SELECT
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN tonnage ELSE 0 END) AS lim_in,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END) AS sap_in
                            FROM ore_productions op
                            LEFT JOIN materials m ON m.id = op.id_material
                            WHERE EXTRACT(YEAR FROM tgl_production) = %s
                        ),
                        outgoing AS (
                            SELECT
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END) AS lim_out,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END) AS sap_out
                            FROM ore_sellings_barging s
                            LEFT JOIN materials m ON m.id = s.id_material
                            WHERE EXTRACT(YEAR FROM date_hauling) = %s
                        )
                        SELECT
                            -- LIM
                            COALESCE(i.lim_in, 0) AS lim_in,
                            COALESCE(o.lim_out, 0) AS lim_out,
                            sa.lim_awal + (COALESCE(i.lim_in, 0) - COALESCE(o.lim_out, 0)) AS lim_stock,

                            -- SAP
                            COALESCE(i.sap_in, 0) AS sap_in,
                            COALESCE(o.sap_out, 0) AS sap_out,
                            sa.sap_awal + (COALESCE(i.sap_in, 0) - COALESCE(o.sap_out, 0)) AS sap_stock,

                            -- TOTAL
                            COALESCE(i.lim_in, 0) + COALESCE(i.sap_in, 0) AS total_in,
                            COALESCE(o.lim_out, 0) + COALESCE(o.sap_out, 0) AS total_out,
                            (sa.lim_awal + sa.sap_awal) +
                            ((COALESCE(i.lim_in, 0) + COALESCE(i.sap_in, 0)) -
                            (COALESCE(o.lim_out, 0) + COALESCE(o.sap_out, 0))) AS total_stock
                        FROM incoming i, outgoing o, saldo_awal sa
                """
            else:
                query = """
                        WITH saldo_awal AS (
                            SELECT
                                -- Limonite
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN tonnage ELSE 0 END)
                                    FROM ore_productions op
                                    LEFT JOIN materials m ON m.id = op.id_material
                                    WHERE tgl_production < %s
                                ), 0) -
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END)
                                    FROM ore_sellings_barging s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_hauling < %s
                                ), 0) AS lim_awal,

                                -- Saprolite
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END)
                                    FROM ore_productions op
                                    LEFT JOIN materials m ON m.id = op.id_material
                                    WHERE tgl_production < %s
                                ), 0) -
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END)
                                    FROM ore_sellings_barging s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_hauling < %s
                                ), 0) AS sap_awal
                        ),
                        incoming AS (
                            SELECT
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN tonnage ELSE 0 END) AS lim_in,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END) AS sap_in
                            FROM ore_productions op
                            LEFT JOIN materials m ON m.id = op.id_material
                            WHERE YEAR(tgl_production) = %s
                        ),
                        outgoing AS (
                            SELECT
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END) AS lim_out,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END) AS sap_out
                            FROM ore_sellings_barging s
                            LEFT JOIN materials m ON m.id = s.id_material
                            WHERE YEAR(date_hauling) = %s
                        )
                        SELECT
                            ISNULL(i.lim_in, 0) AS lim_in,
                            ISNULL(o.lim_out, 0) AS lim_out,
                            sa.lim_awal + (ISNULL(i.lim_in, 0) - ISNULL(o.lim_out, 0)) AS lim_stock,

                            ISNULL(i.sap_in, 0) AS sap_in,
                            ISNULL(o.sap_out, 0) AS sap_out,
                            sa.sap_awal + (ISNULL(i.sap_in, 0) - ISNULL(o.sap_out, 0)) AS sap_stock,

                            ISNULL(i.lim_in, 0) + ISNULL(i.sap_in, 0) AS total_in,
                            ISNULL(o.lim_out, 0) + ISNULL(o.sap_out, 0) AS total_out,
                            (sa.lim_awal + sa.sap_awal)
                                + ((ISNULL(i.lim_in, 0) + ISNULL(i.sap_in, 0)) - (ISNULL(o.lim_out, 0) + ISNULL(o.sap_out, 0))) AS total_stock
                        FROM incoming i, outgoing o, saldo_awal sa
                """
            
            params = [year,year,year,year,year,year]

        elif filter_type =='all':
            if db_vendor == 'postgresql':
                query = """
                    WITH saldo_awal AS (
                        SELECT
                            COALESCE((
                                SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN tonnage ELSE 0 END)
                                FROM ore_productions op
                                LEFT JOIN materials m ON m.id = op.id_material
                                WHERE tgl_production < %s
                            ), 0) -
                            COALESCE((
                                SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END)
                                FROM ore_sellings_barging s
                                LEFT JOIN materials m ON m.id = s.id_material
                                WHERE date_hauling < %s
                            ), 0) AS lim_awal,

                            COALESCE((
                                SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END)
                                FROM ore_productions op
                                LEFT JOIN materials m ON m.id = op.id_material
                                WHERE tgl_production < %s
                            ), 0) -
                            COALESCE((
                                SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END)
                                FROM ore_sellings_barging s
                                LEFT JOIN materials m ON m.id = s.id_material
                                WHERE date_hauling < %s
                            ), 0) AS sap_awal
                    ),
                    incoming AS (
                        SELECT
                            SUM(CASE WHEN m.nama_material = 'LIM' THEN tonnage ELSE 0 END) AS lim_in,
                            SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END) AS sap_in
                        FROM ore_productions op
                        LEFT JOIN materials m ON m.id = op.id_material
                    ),
                    outgoing AS (
                        SELECT
                            SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END) AS lim_out,
                            SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END) AS sap_out
                        FROM ore_sellings_barging s
                        LEFT JOIN materials m ON m.id = s.id_material
                    )
                    SELECT
                        COALESCE(i.lim_in, 0) AS lim_in,
                        COALESCE(o.lim_out, 0) AS lim_out,
                        sa.lim_awal + (COALESCE(i.lim_in, 0) - COALESCE(o.lim_out, 0)) AS lim_stock,

                        COALESCE(i.sap_in, 0) AS sap_in,
                        COALESCE(o.sap_out, 0) AS sap_out,
                        sa.sap_awal + (COALESCE(i.sap_in, 0) - COALESCE(o.sap_out, 0)) AS sap_stock,

                        COALESCE(i.lim_in, 0) + COALESCE(i.sap_in, 0) AS total_in,
                        COALESCE(o.lim_out, 0) + COALESCE(o.sap_out, 0) AS total_out,
                        (sa.lim_awal + sa.sap_awal)
                            + ((COALESCE(i.lim_in, 0) + COALESCE(i.sap_in, 0)) -
                            (COALESCE(o.lim_out, 0) + COALESCE(o.sap_out, 0))) AS total_stock
                    FROM incoming i, outgoing o, saldo_awal sa
                """
            else:
                query = """
                        WITH saldo_awal AS (
                            SELECT
                                -- Limonite
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN tonnage ELSE 0 END)
                                    FROM ore_productions op
                                    LEFT JOIN materials m ON m.id = op.id_material
                                    WHERE tgl_production < %s
                                ), 0) -
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END)
                                    FROM ore_sellings_barging s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_hauling < %s
                                ), 0) AS lim_awal,

                                -- Saprolite
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END)
                                    FROM ore_productions op
                                    LEFT JOIN materials m ON m.id = op.id_material
                                    WHERE tgl_production < %s
                                ), 0) -
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END)
                                    FROM ore_sellings_barging s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_hauling < %s
                                ), 0) AS sap_awal
                        ),
                        incoming AS (
                            SELECT
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN tonnage ELSE 0 END) AS lim_in,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END) AS sap_in
                            FROM ore_productions op
                            LEFT JOIN materials m ON m.id = op.id_material
                        ),
                        outgoing AS (
                            SELECT
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END) AS lim_out,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END) AS sap_out
                            FROM ore_sellings_barging s
                            LEFT JOIN materials m ON m.id = s.id_material
                        )
                        SELECT
                            ISNULL(i.lim_in, 0) AS lim_in,
                            ISNULL(o.lim_out, 0) AS lim_out,
                            sa.lim_awal + (ISNULL(i.lim_in, 0) - ISNULL(o.lim_out, 0)) AS lim_stock,

                            ISNULL(i.sap_in, 0) AS sap_in,
                            ISNULL(o.sap_out, 0) AS sap_out,
                            sa.sap_awal + (ISNULL(i.sap_in, 0) - ISNULL(o.sap_out, 0)) AS sap_stock,

                            ISNULL(i.lim_in, 0) + ISNULL(i.sap_in, 0) AS total_in,
                            ISNULL(o.lim_out, 0) + ISNULL(o.sap_out, 0) AS total_out,
                            (sa.lim_awal + sa.sap_awal)
                                + ((ISNULL(i.lim_in, 0) + ISNULL(i.sap_in, 0)) - (ISNULL(o.lim_out, 0) + ISNULL(o.sap_out, 0))) AS total_stock
                        FROM incoming i, outgoing o, saldo_awal sa
                """
            params = ['1900-01-01'] * 4
        else:
            return JsonResponse({'error': 'Invalid or incomplete filter parameters'}, status=400)

        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()

        return JsonResponse({
            "lim_in": to_float1(row[0]),
            "lim_out": to_float1(row[1]),
            "lim_stock": to_float1(row[2]),
            "sap_in": to_float1(row[3]),
            "sap_out": to_float1(row[4]),
            "sap_stock": to_float1(row[5]),
            "total_in": to_float1(row[6]),
            "total_out": to_float1(row[7]),
            "total_stock": to_float1(row[8]),
        })

    except DatabaseError:
        logger.exception("Database query failed.")
        return JsonResponse({'error': 'Database error'}, status=500)
    except Exception as e:
        logger.exception("Unexpected error in get_inventory_summary")
        return JsonResponse({'error': str(e)}, status=500)

# Create Chart Ore
def get_chart_inventory(request):
    try:
        filter_type = request.GET.get('filter_type')
        year = request.GET.get('year')
        month = request.GET.get('month')
        week = request.GET.get('week')
        date_start = request.GET.get('date_start')
        date_end = request.GET.get('date_end')

        x_labels   = []
        data_stock = []
        data_out   = []
        balance    = []

        if filter_type =='range' and date_start and date_end: 
            if db_vendor == 'postgresql':
                query = """
                       WITH tanggal AS (
                                SELECT generate_series(%s::date, %s::date, interval '1 day') AS date
                            ),
                            incoming AS (
                                SELECT
                                    tgl_production::date AS date,
                                    SUM(tonnage) AS total_in
                                FROM ore_productions
                                WHERE tgl_production BETWEEN %s AND %s
                                GROUP BY tgl_production
                            ),
                            outgoing AS (
                                SELECT
                                    date_hauling::date AS date,
                                    SUM(tonnage) AS total_out
                                FROM ore_sellings_barging s
                                LEFT JOIN materials m ON m.id = s.id_material
                                WHERE date_hauling BETWEEN %s AND %s
                                GROUP BY date_hauling
                            ),
                            saldo_awal AS (
                                SELECT
                                    COALESCE((
                                        SELECT SUM(tonnage)
                                        FROM ore_productions
                                        WHERE tgl_production < %s
                                    ), 0) - COALESCE((
                                        SELECT SUM(tonnage)
                                        FROM ore_sellings_barging
                                        WHERE date_hauling < %s
                                    ), 0) AS value
                            )         
                            SELECT
                                TO_CHAR(t.date, 'YYYY-MM-DD') AS label,
                                COALESCE(i.total_in, 0) AS total_in,
                                COALESCE(o.total_out, 0) AS total_out,
                                SUM(COALESCE(i.total_in, 0) - COALESCE(o.total_out, 0))
                                    OVER (ORDER BY t.date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
                                    + (SELECT value FROM saldo_awal) AS running_balance
                            FROM tanggal t
                            LEFT JOIN incoming i ON t.date = i.date
                            LEFT JOIN outgoing o ON t.date = o.date
                            ORDER BY t.date 
                """
            else:
                 raise ValueError("Unsupported vendor")
             
            params = [
                      date_start, date_end,
                      date_start, date_end,
                      date_start, date_end,
                      date_start,date_start
                      ]

        elif filter_type =='weekly' and year and month and week:
            try:
                print("RECEIVED:", {"year": year, "month": month, "week": week})

                # Deteksi jika 'week' dalam format ISO (contoh: '2025-03')
                if '-' in str(week):
                    year_str, week_str = str(week).split('-')
                    year = int(year_str)
                    week = int(week_str)

                    # Hitung awal minggu (ISO): Senin minggu ke-X
                    start_date = datetime.strptime(f'{year}-W{week:02}-1', "%G-W%V-%u")
                    end_date = start_date + timedelta(days=6)
                else:
                    # Parsing normal year, month, week
                    year = int(year)
                    month = int(month)
                    week = int(week)

                    if not (1 <= month <= 12):
                        return JsonResponse({"error": "Bulan tidak valid (1–12)"}, status=400)
                    if not (1 <= week <= 5):
                        return JsonResponse({"error": "Minggu tidak valid (1–5)"}, status=400)

                    first_day = datetime(year, month, 1)
                    start_date = first_day + timedelta(days=(week - 1) * 7)
                    end_date = start_date + timedelta(days=6)

                    # Koreksi akhir bulan
                    if end_date.month != month:
                        next_month = datetime(year, month, 28) + timedelta(days=4)
                        end_date = datetime(next_month.year, next_month.month, 1) - timedelta(days=1)
            except Exception as e:
                return JsonResponse({"error": f"Format tahun/bulan/minggu tidak valid: {str(e)}"}, status=400)
            
            # SQL Query
            if db_vendor == 'postgresql':
                query = """
                    WITH tanggal AS (
                            SELECT generate_series(%s::date, %s::date, interval '1 day') AS date
                        ),
                        incoming AS (
                            SELECT
                                tgl_production::date AS date,
                                SUM(tonnage) AS total_in
                            FROM ore_productions
                            WHERE tgl_production BETWEEN %s AND %s
                            GROUP BY tgl_production
                        ),
                        outgoing AS (
                            SELECT
                                date_hauling::date AS date,
                                SUM(tonnage) AS total_out
                            FROM ore_sellings_barging s
                            LEFT JOIN materials m ON m.id = s.id_material
                            WHERE date_hauling BETWEEN %s AND %s
                            GROUP BY date_hauling
                        ),
                        daily AS (
                            SELECT
                                t.date,
                                COALESCE(i.total_in, 0) AS total_in,
                                COALESCE(o.total_out, 0) AS total_out
                            FROM tanggal t
                            LEFT JOIN incoming i ON t.date = i.date
                            LEFT JOIN outgoing o ON t.date = o.date
                        ),
                        saldo_awal AS (
                            SELECT
                                COALESCE((
                                    SELECT SUM(tonnage)
                                    FROM ore_productions
                                    WHERE tgl_production < %s
                                ), 0) - COALESCE((
                                    SELECT SUM(tonnage)
                                    FROM ore_sellings_barging
                                    WHERE date_hauling < %s
                                ), 0) AS value
                        )
                        SELECT
                            TRIM(TO_CHAR(date, 'Day')) AS label,
                            total_in,
                            total_out,
                            SUM(total_in - total_out) OVER (
                                ORDER BY date
                                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                            ) + (SELECT value FROM saldo_awal) AS running_balance
                        FROM daily
                        GROUP BY TRIM(TO_CHAR(date, 'Day')), total_in, total_out, date
                        ORDER BY ARRAY_POSITION(
                            ARRAY['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'],
                            TRIM(TO_CHAR(date, 'Day'))
                        )
                """
            else:
               raise ValueError("Unsupported vendor")

            params = [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'),
                      start_date.strftime('%Y-%m-%d'),end_date.strftime('%Y-%m-%d'),
                      start_date.strftime('%Y-%m-%d'),end_date.strftime('%Y-%m-%d'),
                      start_date.strftime('%Y-%m-%d'),start_date.strftime('%Y-%m-%d')
                      ]

        elif filter_type =='monthly' and year and month: 
            year = int(year)
            month = int(month)

            # Ambil jumlah hari terakhir dalam bulan
            last_day = calendar.monthrange(year, month)[1]

            # Bangun tanggal awal dan akhir bulan
            tgl_pertama  = datetime(year, month, 1).date()
            tgl_terakhir = datetime(year, month, last_day).date()

            # Siapkan parameter untuk query
            params = [tgl_pertama, tgl_terakhir,tgl_pertama, tgl_terakhir,tgl_pertama, tgl_terakhir,tgl_pertama,tgl_pertama]

            if db_vendor == 'postgresql':
                query = """
                        WITH tanggal AS (
                                SELECT generate_series(%s::date, %s::date, interval '1 day') AS date
                            ),
                            incoming AS (
                                SELECT
                                    tgl_production::date AS date,
                                    SUM(tonnage) AS total_in
                                FROM ore_productions
                                WHERE tgl_production BETWEEN %s AND %s
                                GROUP BY tgl_production
                            ),
                            outgoing AS (
                                SELECT
                                    date_hauling::date AS date,
                                    SUM(tonnage) AS total_out
                                FROM ore_sellings_barging s
                                LEFT JOIN materials m ON m.id = s.id_material
                                WHERE date_hauling BETWEEN %s AND %s
                                GROUP BY date_hauling
                            ),
                            saldo_awal AS (
                                SELECT
                                    COALESCE((
                                        SELECT SUM(tonnage)
                                        FROM ore_productions
                                        WHERE tgl_production < %s
                                    ), 0) - COALESCE((
                                        SELECT SUM(tonnage)
                                        FROM ore_sellings_barging
                                        WHERE date_hauling < %s
                                    ), 0) AS value
                            )
                            SELECT
                                TO_CHAR(t.date, 'DD') AS label,
                                COALESCE(i.total_in, 0) AS total_in,
                                COALESCE(o.total_out, 0) AS total_out,
                                SUM(COALESCE(i.total_in, 0) - COALESCE(o.total_out, 0))
                                    OVER (ORDER BY t.date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
                                    + (SELECT value FROM saldo_awal) AS running_balance
                            FROM tanggal t
                            LEFT JOIN incoming i ON t.date = i.date
                            LEFT JOIN outgoing o ON t.date = o.date
                            ORDER BY t.date 
                """
            else:
              raise ValueError("Unsupported vendor")
       
        elif filter_type =='yearly' and year: 
            year = int(year)
            if db_vendor == 'postgresql':
                query = """
                    WITH bulan AS (
                            SELECT generate_series(1, 12) AS month
                        ),
                        incoming AS (
                            SELECT
                                EXTRACT(MONTH FROM tgl_production)::int AS month,
                                SUM(tonnage) AS total_in
                            FROM ore_productions
                            WHERE EXTRACT(YEAR FROM tgl_production) = %s
                            GROUP BY EXTRACT(MONTH FROM tgl_production)
                        ),
                        outgoing AS (
                            SELECT
                                EXTRACT(MONTH FROM date_hauling)::int AS month,
                                SUM(tonnage) AS total_out
                            FROM ore_sellings_barging s
                            LEFT JOIN materials m ON m.id = s.id_material
                            WHERE EXTRACT(YEAR FROM date_hauling) = %s
                            GROUP BY EXTRACT(MONTH FROM date_hauling)
                        ),
                        saldo_awal AS (
                            SELECT
                                COALESCE((
                                    SELECT SUM(tonnage)
                                    FROM ore_productions
                                    WHERE EXTRACT(YEAR FROM tgl_production) < %s
                                ), 0) - COALESCE((
                                    SELECT SUM(tonnage)
                                    FROM ore_sellings_barging
                                    WHERE EXTRACT(YEAR FROM date_hauling) < %s
                                ), 0) AS value
                        )
                        SELECT
                            TO_CHAR(TO_DATE(bulan.month::text, 'MM'), 'Mon') AS label,
                            COALESCE(i.total_in, 0) AS total_in,
                            COALESCE(o.total_out, 0) AS total_out,
                            SUM(COALESCE(i.total_in, 0) - COALESCE(o.total_out, 0)) OVER (
                                ORDER BY bulan.month
                                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                            ) + (SELECT value FROM saldo_awal) AS running_balance
                        FROM bulan
                        LEFT JOIN incoming i ON bulan.month = i.month
                        LEFT JOIN outgoing o ON bulan.month = o.month
                        ORDER BY bulan.month;
                """
            else:
                raise ValueError("Unsupported vendor")
            
            params = [year,year,year,year]

        elif filter_type =='all':
            if db_vendor == 'postgresql':
                query = """
                    WITH incoming AS (
                        SELECT
                            EXTRACT(YEAR FROM tgl_production)::int AS year,
                            SUM(tonnage) AS total_in
                        FROM ore_productions
                        GROUP BY EXTRACT(YEAR FROM tgl_production)
                    ),
                    outgoing AS (
                        SELECT
                            EXTRACT(YEAR FROM date_hauling)::int AS year,
                            SUM(tonnage) AS total_out
                        FROM ore_sellings_barging s
                        LEFT JOIN materials m ON m.id = s.id_material
                        GROUP BY EXTRACT(YEAR FROM date_hauling)
                    )
                    SELECT
                        COALESCE(i.year, o.year) AS label,
                        COALESCE(i.total_in, 0) AS total_in,
                        COALESCE(o.total_out, 0) AS total_out,
                        SUM(COALESCE(i.total_in, 0) - COALESCE(o.total_out, 0))
                            OVER (ORDER BY COALESCE(i.year, o.year)) AS running_balance
                    FROM incoming i
                    FULL OUTER JOIN outgoing o ON i.year = o.year
                    ORDER BY label
                """
            else:
                raise ValueError("Unsupported vendor")
            params = []

        else:
            return JsonResponse({'error': 'Invalid or incomplete filter parameters'}, status=400)

        # Eksekusi query
        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            results = cursor.fetchall()

        for row in results:
            x_labels.append(str(row[0]))
            data_stock.append(round(float(row[1]), 0))
            data_out.append(round(float(row[2]), 0))
            balance.append(round(float(row[3]), 0))

        return JsonResponse({
            'x_data': x_labels,
            'y_data_stock': data_stock,
            'y_data_out': data_out,
            'y_data_balance': balance,
        })

    except DatabaseError:
        logger.exception("DB Error in get_chart_inventory")
        return JsonResponse({'error': 'Database error'}, status=500)
    
    except Exception as e:
        logger.exception("Unexpected error in get_chart_inventory")
        return JsonResponse({'error': str(e)}, status=500)

# Ach. Ore Production
def get_grade_class(ni, mgo, fe):
    if ni is None or mgo is None or fe is None:
        return "NULL"
    if ni >= 1.6 and mgo >= 9.0 and fe <= 27.0:
        return "HGS"
    elif 1.2 <= ni < 1.6 and mgo >= 9.0 and fe <= 27.0:
        return "MGS"
    elif ni < 1.2 and 9.0 <= mgo <= 20.0 and fe <= 27.0:
        return "LGS"
    elif ni >= 1.1 and mgo < 9.0 and fe >= 27.0:
        return "HGL"
    elif ni < 1.1 and mgo < 9.0 and fe >= 27.0:
        return "LGL"
    elif ni < 0.9 and mgo < 9.0 and fe < 27.0:
        return "OB"
    elif ni < 1.2 and mgo > 20.0 and fe >= 27.0:
        return "WASTE"
    else:
        return "???"

def get_grade_roa(request):
    try:
        filter_type = request.GET.get('filter_type')
        year = request.GET.get('year')
        month = request.GET.get('month')
        week = request.GET.get('week')
        date_start = request.GET.get('date_start')
        date_end = request.GET.get('date_end')
        filter_date = request.GET.get('filter_date')

        # WHERE clause dan parameter
        where_clause = "WHERE 1=1"
        params = []

        if filter_type =='daily' and filter_date:
            where_clause += " AND tgl_production = %s "
            params += [filter_date]
        if filter_type =='range' and date_start and date_end:
            where_clause += " AND tgl_production BETWEEN %s AND %s"
            params += [date_start, date_end]
        elif filter_type =='weekly' and week:
            where_clause += " AND TO_CHAR(tgl_production, 'IYYY-IW') = %s"
            params.append(week)
        elif filter_type =='monthly' and year and month:
            where_clause += " AND EXTRACT(YEAR FROM tgl_production) = %s AND EXTRACT(MONTH FROM tgl_production) = %s"
            params += [year, month]
        elif filter_type =='yearly' and year:
            where_clause += " AND EXTRACT(YEAR FROM tgl_production) = %s"
            params.append(year)
        elif filter_type =='all':
            pass  # Semua data
        elif filter_type not in ['daily', 'range', 'weekly', 'yearly', 'all']:
            return JsonResponse({'error': 'Invalid filter type'}, status=400)

        # Query utama
        sql_query = f"""
                    SELECT
                            nama_material,
                            SUM(tonnage) AS total_ore,
                            SUM(CASE WHEN ROA_Ni  IS NOT NULL AND sample_number  <> 'Unprepared' THEN tonnage ELSE 0 END) AS released,
                            COALESCE(ROUND((
                                SUM(tonnage * ROA_Ni) / NULLIF(SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                            )::numeric, 2), 0) as ni,
                            COALESCE(ROUND((
                                SUM(tonnage * ROA_Co) / NULLIF(SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                            )::numeric, 2), 0) as co,
                            COALESCE(ROUND((
                                SUM(tonnage * ROA_Al2O3) / NULLIF(SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                            )::numeric, 2), 0) as al2o3,
                            COALESCE(ROUND((
                                SUM(tonnage * ROA_CaO) / NULLIF(SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                            )::numeric, 2), 0) as cao,
                            COALESCE(ROUND((
                                SUM(tonnage * ROA_Cr2O3) / NULLIF(SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                            )::numeric, 2), 0) as cr2o3,
                            COALESCE(ROUND((
                                SUM(tonnage * ROA_Fe2O3) / NULLIF(SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                            )::numeric, 2), 0) as fe2o3,
                            COALESCE(ROUND((
                                SUM(tonnage * ROA_Fe) / NULLIF(SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                            )::numeric, 2), 0) as fe,
                            COALESCE(ROUND((
                                SUM(tonnage * ROA_MgO) / NULLIF(SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                            )::numeric, 2), 0) as mgo,
                            COALESCE(ROUND((
                                SUM(tonnage * ROA_MC) / NULLIF(SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                            )::numeric, 2), 0) as mc,
                            COALESCE(ROUND((
                                SUM(tonnage * ROA_SiO2) / NULLIF(SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                            )::numeric, 2), 0) as sio2,
                            ROUND(COALESCE(
                                (
                            SUM(tonnage * ROA_SiO2) / NULLIF(SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)) /
                            (NULLIF(SUM(tonnage * ROA_MgO) / NULLIF(SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0),0) + 0.000001), 0
                            )::numeric, 2) as sm
                        FROM details_roa
                    {where_clause}
                    GROUP BY nama_material
            """

        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(sql_query, params)
            columns = [col[0] for col in cursor.description]
            result = [dict(zip(columns, row)) for row in cursor.fetchall()]

        for row in result:
            row['total_ore'] = round(float(row['total_ore']), 1)
            row['released']  = round(float(row['released']), 1)
            row['ni']        = round(float(row['ni']), 2)
            row['co']        = round(float(row['co']), 2)
            row['al2o3']     = round(float(row['al2o3']), 2)
            row['cao']       = round(float(row['cao']), 2)
            row['cr2o3']     = round(float(row['cr2o3']), 2)
            row['fe']        = round(float(row['fe']), 2)
            row['mgo']       = round(float(row['mgo']), 2)
            row['sio2']      = round(float(row['sio2']), 2)
            row['mc']        = round(float(row['mc']), 2)
            row['sm']        = round(float(row['sm']), 2)
            row['grade']     = get_grade_class(row['ni'], row['mgo'], row['fe'])

        return JsonResponse({
            'data': result,
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
def get_stockpile_roa(request):
    try:
        per_page = int(request.GET.get('per_page', 10))  # misal default 10

        materialFilter = request.GET.get('material', '')
        filter_type = request.GET.get('filter_type')
        year = request.GET.get('year')
        month = request.GET.get('month')
        week = request.GET.get('week')
        date_start = request.GET.get('date_start')
        date_end = request.GET.get('date_end')
        filter_date = request.GET.get('filter_date')

        # WHERE clause dan parameter
        where_clause = "WHERE 1=1"
        params = []

        if materialFilter:
            where_clause += " AND nama_material = %s"
            params.append(materialFilter)
        
        if filter_type =='daily' and filter_date:
            where_clause += " AND tgl_production = %s "
            params += [filter_date]
        if filter_type =='range' and date_start and date_end:
            where_clause += " AND tgl_production BETWEEN %s AND %s"
            params += [date_start, date_end]
        elif filter_type =='weekly' and week:
            where_clause += " AND TO_CHAR(tgl_production, 'IYYY-IW') = %s"
            params.append(week)
        elif filter_type =='monthly' and year and month:
            where_clause += " AND EXTRACT(YEAR FROM tgl_production) = %s AND EXTRACT(MONTH FROM tgl_production) = %s"
            params += [year, month]
        elif filter_type =='yearly' and year:
            where_clause += " AND EXTRACT(YEAR FROM tgl_production) = %s"
            params.append(year)
        elif filter_type =='all':
            pass  # Semua data
        elif filter_type not in ['daily', 'range', 'weekly', 'yearly', 'all']:
            return JsonResponse({'error': 'Invalid filter type'}, status=400)

        # Query utama
        sql_query = f"""
                SELECT * FROM (
                    SELECT
                            stockpile,
                            nama_material,
                            SUM(tonnage) AS total_ore,
                            SUM(CASE WHEN ROA_Ni  IS NOT NULL AND sample_number  <> 'Unprepared' THEN tonnage ELSE 0 END) AS released,
                            COALESCE(ROUND((
                                SUM(tonnage * ROA_Ni) / NULLIF(SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                            )::numeric, 2), 0) as ni,
                            COALESCE(ROUND((
                                SUM(tonnage * ROA_Co) / NULLIF(SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                            )::numeric, 2), 0) as co,
                            COALESCE(ROUND((
                                SUM(tonnage * ROA_Al2O3) / NULLIF(SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                            )::numeric, 2), 0) as al2o3,
                            COALESCE(ROUND((
                                SUM(tonnage * ROA_CaO) / NULLIF(SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                            )::numeric, 2), 0) as cao,
                            COALESCE(ROUND((
                                SUM(tonnage * ROA_Cr2O3) / NULLIF(SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                            )::numeric, 2), 0) as cr2o3,
                            COALESCE(ROUND((
                                SUM(tonnage * ROA_Fe2O3) / NULLIF(SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                            )::numeric, 2), 0) as fe2o3,
                            COALESCE(ROUND((
                                SUM(tonnage * ROA_Fe) / NULLIF(SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                            )::numeric, 2), 0) as fe,
                            COALESCE(ROUND((
                                SUM(tonnage * ROA_MgO) / NULLIF(SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                            )::numeric, 2), 0) as mgo,
                            COALESCE(ROUND((
                                SUM(tonnage * ROA_MC) / NULLIF(SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                            )::numeric, 2), 0) as mc,
                            COALESCE(ROUND((
                                SUM(tonnage * ROA_SiO2) / NULLIF(SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                            )::numeric, 2), 0) as sio2,
                            ROUND(COALESCE(
                                (
                            SUM(tonnage * ROA_SiO2) / NULLIF(SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)) /
                            (NULLIF(SUM(tonnage * ROA_MgO) / NULLIF(SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0),0) + 0.000001), 0
                            )::numeric, 2) as sm
                        FROM details_roa
                    {where_clause}
                    GROUP BY stockpile, nama_material
                ) AS sub
                ORDER BY RANDOM()
                LIMIT %s
            """
        params.extend([per_page])

        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(sql_query, params)
            columns = [col[0] for col in cursor.description]
            result = [dict(zip(columns, row)) for row in cursor.fetchall()]

        grandTotalOre      = 0
        grandTotalRelease  = 0
        # Data untuk product grade
        data_Ni    = []
        data_Co    = []
        data_Al2O3 = []
        data_CaO   = []
        data_Cr2O3 = []
        data_Fe    = []
        data_Mgo   = []
        data_SiO2  = []
        data_MC    = []
        data_SM    = []

        # Menghitung grand total dan product grade
        for row in result:
                grandTotalOre += float(row['total_ore'])
                grandTotalRelease    += float(row['released'])

                # Hitung Product Grade
                data_Ni.append(row['released'] * float(row['ni']))
                data_Co.append(row['released'] * float(row['co']))
                data_Al2O3.append(row['released'] * float(row['al2o3']))
                data_CaO.append(row['released'] * float(row['cao']))
                data_Cr2O3.append(row['released'] * float(row['cr2o3']))
                data_Fe.append(row['released'] * float(row['fe']))
                data_Mgo.append(row['released'] * float(row['mgo']))
                data_SiO2.append(row['released'] * float(row['sio2']))
                data_MC.append(row['released'] * float(row['mc']))
                data_SM.append(row['released'] * float(row['sm']))
                row['grade'] = get_grade_class(float(row['ni']), float(row['mgo']), float(row['fe']))

        return JsonResponse({
            'data': result,
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
def get_dome_roa(request):
    try:
        per_page = int(request.GET.get('per_page', 6))  # misal default 10

        materialFilter = request.GET.get('material', '')
        filter_type = request.GET.get('filter_type')
        year = request.GET.get('year')
        month = request.GET.get('month')
        week = request.GET.get('week')
        date_start = request.GET.get('date_start')
        date_end = request.GET.get('date_end')
        filter_date = request.GET.get('filter_date')

        # WHERE clause dan parameter
        where_clause = "WHERE 1=1"
        params = []

        if materialFilter:
            where_clause += " AND nama_material = %s"
            params.append(materialFilter)

        if filter_type =='daily' and filter_date:
            where_clause += " AND tgl_production = %s "
            params += [filter_date]
        elif filter_type =='range' and date_start and date_end:
            where_clause += " AND tgl_production BETWEEN %s AND %s"
            params += [date_start, date_end]
        elif filter_type =='weekly' and week:
            where_clause += " AND TO_CHAR(tgl_production, 'IYYY-IW') = %s"
            params.append(week)
        elif filter_type =='monthly' and year and month:
            where_clause += " AND EXTRACT(YEAR FROM tgl_production) = %s AND EXTRACT(MONTH FROM tgl_production) = %s"
            params += [year, month]
        elif filter_type =='yearly' and year:
            where_clause += " AND EXTRACT(YEAR FROM tgl_production) = %s"
            params.append(year)
        elif filter_type =='all':
            pass  # Semua data
        elif filter_type not in ['daily', 'range', 'weekly', 'yearly', 'all']:
            return JsonResponse({'error': 'Invalid filter type'}, status=400)

        # Query utama
        sql_query = f"""
                SELECT * FROM (
                    SELECT
                            pile_id,
                            nama_material,
                            SUM(tonnage) AS total_ore,
                            SUM(CASE WHEN ROA_Ni  IS NOT NULL AND sample_number  <> 'Unprepared' THEN tonnage ELSE 0 END) AS released,
                            COALESCE(ROUND((
                                SUM(tonnage * ROA_Ni) / NULLIF(SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                            )::numeric, 2), 0) as ni,
                             COALESCE(ROUND((
                                SUM(tonnage * ROA_Fe) / NULLIF(SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                            )::numeric, 2), 0) as fe,
                            COALESCE(ROUND((
                                SUM(tonnage * ROA_MgO) / NULLIF(SUM(CASE WHEN sample_number <> 'Unprepared' AND ROA_Ni IS NOT NULL THEN tonnage ELSE 0 END), 0)
                            )::numeric, 2), 0) as mgo
                        FROM details_roa
                    {where_clause}
                    GROUP BY pile_id, nama_material
                ) AS sub
                ORDER BY RANDOM()
                LIMIT %s
            """
        params.extend([per_page])

        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(sql_query, params)
            columns = [col[0] for col in cursor.description]
            result = [dict(zip(columns, row)) for row in cursor.fetchall()]


        # Menghitung grand total dan product grade
        for row in result:
            row['total_ore'] = round(float(row['total_ore']), 1)
            row['released']  = round(float(row['released']), 1)
            row['ni']        = round(float(row['ni']), 2)
            row['mgo']       = round(float(row['mgo']), 2)
            row['grade']     = get_grade_class(row['ni'], row['mgo'], row['fe'])

        return JsonResponse({
            'data': result,
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Get Inventory
def get_data_inventory(request):
    saleFilter   = request.GET.get('saleFilter')
    areaFilter   = json.loads(request.GET.get('areaFilter', '[]'))
    pointFilter  = json.loads(request.GET.get('pointFilter', '[]'))

    # Pagination setup
    page = int(request.GET.get('page', 1))
    per_page = 100
    offset = (page - 1) * per_page

    # === Filter Dinamis ===
    filters = []
    params = []

    if saleFilter:
        filters.append("t1.sale_adjust = %s")
        params.append(saleFilter)

    if areaFilter:
        filters.append(f"t1.stockpile IN ({', '.join(['%s'] * len(areaFilter))})")
        params.extend(areaFilter)

    if pointFilter:
        filters.append(f"t1.pile_id IN ({', '.join(['%s'] * len(pointFilter))})")
        params.extend(pointFilter)

    where_clause = " AND " + " AND ".join(filters) if filters else ""

    # === Count Query pakai subquery + GROUP BY ===
    count_query = f"""
        SELECT COUNT(*)
        FROM (
            SELECT t1.stockpile, t1.pile_id
            FROM inventory_by_dome AS t1
            LEFT JOIN selling_by_dome AS t2
                ON t2.stockpile = t1.stockpile
                AND t2.dome = t1.pile_id
            WHERE t1.status_dome != 'Finished'
            {where_clause}
            GROUP BY t1.stockpile, t1.pile_id, t1.total_ore, t1.released,
                     t1.nama_material, t1.Ni, t1.Co, t1.Al2O3, t1.CaO,
                     t1.Cr2O3, t1.Fe, t1.Mgo, t1.SiO2, t1.MC, t1.SM
        ) AS sub
    """
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(count_query, params)
        total_data = cursor.fetchone()[0]

    # === Main Query pakai SUM CASE ===
    query = f"""
        SELECT
            t1.stockpile,
            t1.pile_id,
            t1.total_ore,
            t1.released,
            t1.nama_material,
            COALESCE(ROUND(SUM(
                CASE
                    WHEN t1.nama_material = 'LIM' AND t2.material = 'SAP' THEN t2.tonnage
                    WHEN t1.nama_material = 'SAP' AND t2.material = 'LIM' THEN t2.tonnage
                    WHEN t1.nama_material = t2.material THEN t2.tonnage
                    ELSE 0
                END
            )::numeric, 2), 0) AS total_selling,
            ROUND((t1.total_ore - COALESCE(SUM(
                CASE
                    WHEN t1.nama_material = 'LIM' AND t2.material = 'SAP' THEN t2.tonnage
                    WHEN t1.nama_material = 'SAP' AND t2.material = 'LIM' THEN t2.tonnage
                    WHEN t1.nama_material = t2.material THEN t2.tonnage
                    ELSE 0
                END
            ), 0))::numeric, 2) AS balance,
            t1.Ni, t1.Co, t1.Al2O3, t1.CaO, t1.Cr2O3,
            t1.Fe, t1.Mgo, t1.SiO2, t1.MC, t1.SM
        FROM inventory_by_dome AS t1
        LEFT JOIN selling_by_dome AS t2
            ON t2.stockpile = t1.stockpile
            AND t2.dome = t1.pile_id
        WHERE t1.status_dome != 'Finished'
        {where_clause}
        GROUP BY
            t1.stockpile, t1.pile_id, t1.total_ore, t1.released,
            t1.nama_material, t1.Ni, t1.Co, t1.Al2O3, t1.CaO,
            t1.Cr2O3, t1.Fe, t1.Mgo, t1.SiO2, t1.MC, t1.SM
        ORDER BY t1.nama_material ASC, t1.stockpile ASC
        LIMIT %s OFFSET %s;
    """
    params_with_paging = params + [per_page, offset]

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params_with_paging)
        columns = [col[0] for col in cursor.description]
        sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]

    # === Konversi angka ke float ===
    for item in sql_data:
        for field in [
            'total_ore', 'released', 'total_selling', 'balance',
            'ni', 'co', 'al2o3', 'cao', 'cr2o3', 'fe', 'mgo', 'sio2', 'mc', 'sm'
        ]:
            if field in item and item[field] is not None:
                item[field] = float(item[field])

    # === Summary sederhana ===
    total_released = sum(item['released'] for item in sql_data if item['released'])
    total_ore      = sum(item['total_ore'] for item in sql_data if item['total_ore'])
    total_selling  = sum(item['total_selling'] for item in sql_data if item['total_selling'])
    total_balance  = sum(item['balance'] for item in sql_data if item['balance'])

    def weighted_avg(field):
        return sum(item[field] * item['released'] for item in sql_data if item['released']) / total_released if total_released else 0

    summary = {
        'total_ore': total_ore,
        'total_released': total_released,
        'total_selling': total_selling,
        'total_balance': total_balance,
        'avg_ni': weighted_avg('ni'),
        'avg_co': weighted_avg('co'),
        'avg_al2o3': weighted_avg('al2o3'),
        'avg_cao': weighted_avg('cao'),
        'avg_cr2o3': weighted_avg('cr2o3'),
        'avg_fe': weighted_avg('fe'),
        'avg_mgo': weighted_avg('mgo'),
        'avg_sio2': weighted_avg('sio2'),
        'avg_mc': weighted_avg('mc'),
    }

    return JsonResponse({
        'data': sql_data,
        'summary': summary,
        'pagination': {
            'more': len(sql_data) == per_page,
            'total_pages': (total_data // per_page) + (1 if total_data % per_page > 0 else 0),
            'current_page': page,
            'total_data': total_data
        }
    })

def get_inventory_lim(request):
    areaFilter  = request.GET.get('areaFilter', '[]')
    pointFilter = request.GET.get('pointFilter', '[]')

    # Parsing JSON filter
    try:
        areaFilter  = json.loads(areaFilter) if areaFilter else []
        pointFilter = json.loads(pointFilter) if pointFilter else []
    except json.JSONDecodeError:
        areaFilter, pointFilter = [], []

    # Pagination setup
    page = int(request.GET.get('page', 1))
    per_page = 100
    offset = (page - 1) * per_page

    # Filters
    filters = ["t1.status_dome != 'Finished'", "t1.sale_adjust = 'HPAL'"]
    params = []

    if areaFilter:
        filters.append(f"t1.stockpile IN ({', '.join(['%s'] * len(areaFilter))})")
        params.extend(areaFilter)
    if pointFilter:
        filters.append(f"t1.pile_id IN ({', '.join(['%s'] * len(pointFilter))})")
        params.extend(pointFilter)

    where_clause = " AND ".join(filters)

    # == Count query dengan GROUP BY ==
    count_query = f"""
        SELECT COUNT(*)
        FROM (
            SELECT t1.stockpile, t1.pile_id
            FROM inventory_by_dome t1
            LEFT JOIN selling_by_dome t2
              ON t2.stockpile = t1.stockpile
             AND t2.dome = t1.pile_id
             AND t2.sale_adjust = 'HPAL'
            WHERE {where_clause}
            GROUP BY t1.stockpile, t1.pile_id, t1.total_ore, t1.released,
                     t1.nama_material, t1.Ni, t1.Co, t1.Al2O3, t1.CaO,
                     t1.Cr2O3, t1.Fe, t1.Mgo, t1.SiO2, t1.MC, t1.SM
        ) AS sub
    """

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(count_query, params)
        result = cursor.fetchone()
        total_data = result[0] if result else 0

    # == Query utama ==
    query = f"""
        SELECT
            t1.stockpile,
            t1.pile_id,
            t1.total_ore,
            t1.released,
            t1.nama_material,
            COALESCE(ROUND(SUM(
                CASE
                    WHEN t1.nama_material = t2.material THEN t2.tonnage
                    WHEN t1.nama_material = 'LIM' AND t2.material = 'SAP' THEN t2.tonnage
                    WHEN t1.nama_material = 'SAP' AND t2.material = 'LIM' THEN t2.tonnage
                    ELSE 0
                END
            )::numeric, 2), 0) AS total_selling,
            ROUND((
                t1.total_ore - COALESCE(SUM(
                    CASE
                        WHEN t1.nama_material = t2.material THEN t2.tonnage
                        WHEN t1.nama_material = 'LIM' AND t2.material = 'SAP' THEN t2.tonnage
                        WHEN t1.nama_material = 'SAP' AND t2.material = 'LIM' THEN t2.tonnage
                        ELSE 0
                    END
                ),0)
            )::numeric, 2) AS balance,
            t1.Ni, t1.Co, t1.Al2O3, t1.CaO, t1.Cr2O3,
            t1.Fe, t1.Mgo, t1.SiO2, t1.MC, t1.SM
        FROM inventory_by_dome t1
        LEFT JOIN selling_by_dome t2
          ON t2.stockpile = t1.stockpile
         AND t2.dome = t1.pile_id
         --AND t2.sale_adjust = 'HPAL'
        WHERE {where_clause}
        GROUP BY
            t1.stockpile, t1.pile_id, t1.total_ore, t1.released,
            t1.nama_material, t1.Ni, t1.Co, t1.Al2O3, t1.CaO,
            t1.Cr2O3, t1.Fe, t1.Mgo, t1.SiO2, t1.MC, t1.SM
        ORDER BY t1.nama_material ASC, t1.stockpile ASC
        LIMIT %s OFFSET %s;
    """

    params_with_paging = params + [per_page, offset]

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params_with_paging)
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            sql_data = []

    # === Konversi Decimal/str ke float ===
    for item in sql_data:
        for field in [
            'total_ore', 'released', 'total_selling', 'balance',
            'ni', 'co', 'al2o3', 'cao', 'cr2o3', 'fe', 'mgo', 'sio2', 'mc', 'sm'
        ]:
            val = item.get(field)
            if isinstance(val, Decimal):
                item[field] = float(val)
            elif isinstance(val, (float, int)):
                item[field] = float(val)
            elif isinstance(val, str) and val.replace('.', '', 1).isdigit():
                item[field] = float(val)

    # === Summary agregat ===
    total_released = sum(item['released'] for item in sql_data if item['released'])
    total_ore      = sum(item['total_ore'] for item in sql_data if item['total_ore'])
    total_selling  = sum(item['total_selling'] for item in sql_data if item['total_selling'])
    total_balance  = sum(item['balance'] for item in sql_data if item['balance'])

    def weighted_avg(field):
        return sum(item[field] * item['released'] for item in sql_data if item['released']) / total_released if total_released else 0

    sum_results = {
        'total_ore': total_ore,
        'total_released': total_released,
        'total_selling': total_selling,
        'total_balance': total_balance,
        'avg_ni': weighted_avg('ni'),
        'avg_co': weighted_avg('co'),
        'avg_al2o3': weighted_avg('al2o3'),
        'avg_cao': weighted_avg('cao'),
        'avg_cr2o3': weighted_avg('cr2o3'),
        'avg_fe': weighted_avg('fe'),
        'avg_mgo': weighted_avg('mgo'),
        'avg_sio2': weighted_avg('sio2'),
        'avg_mc': weighted_avg('mc')
    }

    # Pagination info
    more_data = len(sql_data) == per_page
    total_pages = (total_data // per_page) + (1 if total_data % per_page > 0 else 0)

    return JsonResponse({
        'data'      : sql_data,
        'summary'   : sum_results,
        'pagination': {
            'more'        : more_data,
            'total_pages' : total_pages,
            'current_page': page,
            'total_data'  : total_data
        }
    })

def get_inventory_sap(request):
    areaFilter  = request.GET.get('areaFilter', '[]')
    pointFilter = request.GET.get('pointFilter', '[]')

    # Parsing JSON filter
    try:
        areaFilter  = json.loads(areaFilter) if areaFilter else []
        pointFilter = json.loads(pointFilter) if pointFilter else []
    except json.JSONDecodeError:
        areaFilter, pointFilter = [], []

    # Pagination setup
    page = int(request.GET.get('page', 1))
    per_page = 100
    offset = (page - 1) * per_page

    # Filters
    filters = ["t1.status_dome != 'Finished'", "t1.sale_adjust = 'RKEF'"]
    params = []

    if areaFilter:
        filters.append(f"t1.stockpile IN ({', '.join(['%s'] * len(areaFilter))})")
        params.extend(areaFilter)
    if pointFilter:
        filters.append(f"t1.pile_id IN ({', '.join(['%s'] * len(pointFilter))})")
        params.extend(pointFilter)

    where_clause = " AND ".join(filters)

    # == Count query pakai subquery + GROUP BY ==
    count_query = f"""
        SELECT COUNT(*)
        FROM (
            SELECT t1.stockpile, t1.pile_id
            FROM inventory_by_dome t1
            LEFT JOIN selling_by_dome t2
                ON t2.stockpile = t1.stockpile
               AND t2.dome = t1.pile_id
               AND t2.sale_adjust = 'RKEF'
            WHERE {where_clause}
            GROUP BY t1.stockpile, t1.pile_id, t1.total_ore, t1.released, 
                     t1.nama_material, t1.Ni, t1.Co, t1.Al2O3, t1.CaO, 
                     t1.Cr2O3, t1.Fe, t1.Mgo, t1.SiO2, t1.MC, t1.SM
        ) AS sub
    """

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(count_query, params)
        result = cursor.fetchone()
        total_data = result[0] if result else 0

    # == Query utama (SUM CASE) ==
    query = f"""
        SELECT
            t1.stockpile,
            t1.pile_id,
            t1.total_ore,
            t1.released,
            t1.nama_material,
            COALESCE(ROUND(SUM(
                CASE
                    WHEN t1.nama_material = t2.material THEN t2.tonnage
                    WHEN t1.nama_material = 'LIM' AND t2.material = 'SAP' THEN t2.tonnage
                    WHEN t1.nama_material = 'SAP' AND t2.material = 'LIM' THEN t2.tonnage
                    ELSE 0
                END
            )::numeric, 2), 0) AS total_selling,
            ROUND((
                t1.total_ore - COALESCE(SUM(
                    CASE
                        WHEN t1.nama_material = t2.material THEN t2.tonnage
                        WHEN t1.nama_material = 'LIM' AND t2.material = 'SAP' THEN t2.tonnage
                        WHEN t1.nama_material = 'SAP' AND t2.material = 'LIM' THEN t2.tonnage
                        ELSE 0
                    END
                ),0)
            )::numeric, 2) AS balance,
            t1.Ni, t1.Co, t1.Al2O3, t1.CaO, t1.Cr2O3,
            t1.Fe, t1.Mgo, t1.SiO2, t1.MC, t1.SM
        FROM inventory_by_dome t1
        LEFT JOIN selling_by_dome t2
            ON t2.stockpile = t1.stockpile
           AND t2.dome = t1.pile_id
          --AND t2.sale_adjust = 'RKEF'
        WHERE {where_clause}
        GROUP BY
            t1.stockpile, t1.pile_id, t1.total_ore, t1.released, 
            t1.nama_material, t1.Ni, t1.Co, t1.Al2O3, t1.CaO, 
            t1.Cr2O3, t1.Fe, t1.Mgo, t1.SiO2, t1.MC, t1.SM
        ORDER BY t1.nama_material ASC, t1.stockpile ASC
        LIMIT %s OFFSET %s;
    """

    params_with_paging = params + [per_page, offset]

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params_with_paging)
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            sql_data = []

    # === Konversi Decimal ke float ===
    for item in sql_data:
        for field in [
            'total_ore', 'released', 'total_selling', 'balance',
            'ni', 'co', 'al2o3', 'cao', 'cr2o3', 'fe', 'mgo', 'sio2', 'mc', 'sm'
        ]:
            val = item.get(field)
            if isinstance(val, Decimal):
                item[field] = float(val)
            elif isinstance(val, (float, int)):
                item[field] = float(val)
            elif isinstance(val, str) and val.replace('.', '', 1).isdigit():
                item[field] = float(val)

    # === Summary agregat ===
    total_released = sum(item['released'] for item in sql_data if item['released'])
    total_ore      = sum(item['total_ore'] for item in sql_data if item['total_ore'])
    total_selling  = sum(item['total_selling'] for item in sql_data if item['total_selling'])
    total_balance  = sum(item['balance'] for item in sql_data if item['balance'])

    def weighted_avg(field):
        return sum(item[field] * item['released'] for item in sql_data if item['released']) / total_released if total_released else 0

    sum_results = {
        'total_ore': total_ore,
        'total_released': total_released,
        'total_selling': total_selling,
        'total_balance': total_balance,
        'avg_ni': weighted_avg('ni'),
        'avg_co': weighted_avg('co'),
        'avg_al2o3': weighted_avg('al2o3'),
        'avg_cao': weighted_avg('cao'),
        'avg_cr2o3': weighted_avg('cr2o3'),
        'avg_fe': weighted_avg('fe'),
        'avg_mgo': weighted_avg('mgo'),
        'avg_sio2': weighted_avg('sio2'),
        'avg_mc': weighted_avg('mc')
    }

    # Pagination info
    more_data = len(sql_data) == per_page
    total_pages = (total_data // per_page) + (1 if total_data % per_page > 0 else 0)

    return JsonResponse({
        'data'      : sql_data,
        'summary'   : sum_results,
        'pagination': {
            'more'        : more_data,
            'total_pages' : total_pages,
            'current_page': page,
            'total_data'  : total_data
        }
    })


def get_inventory_stockpile(request):
    saleFilter = request.GET.get('saleFilter')
    areaFilter  = request.GET.get('areaFilter', '[]')  # Menggunakan '[]' sebagai default jika None
    # Parsing JSON
    areaFilter  = json.loads(areaFilter)  # Parsing JSON menjadi list

    # Pagination setup
    page = int(request.GET.get('page', 1))
    per_page = 100
    offset = (page - 1) * per_page

    # Query to count total data
    count_query = """
        SELECT COUNT(*)
        FROM inventory_by_dome AS t1
        LEFT JOIN selling_by_dome AS t2 ON 
            t2.stockpile = t1.stockpile AND
            t2.dome = t1.pile_id
        WHERE t1.status_dome != 'Finished'
    """

    # Apply filters to the count query
    count_filters = []
    params = []

    if saleFilter:
        count_filters.append("t1.sale_adjust = %s")
        params.append(saleFilter)

    if areaFilter:  # Pastikan areaFilter tidak kosong
        count_filters.append(f"t1.stockpile IN ({', '.join(['%s'] * len(areaFilter))})")
        params.extend(areaFilter)

    if count_filters:
        count_query += " AND " + " AND ".join(count_filters)

    # Execute count query
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(count_query,params)
        result = cursor.fetchone()
        total_data = result[0] if result else 0 
   

        if db_vendor == 'postgresql':
            query = """
                SELECT
                    t1.stockpile,
                    SUM(t1.total_ore) AS total_ore,
                    SUM(t1.released) AS released,
                    t1.nama_material,
                    COALESCE(ROUND(SUM(t2.tonnage)::numeric, 2), 0) AS total_selling,
                    ROUND((SUM(t1.total_ore) - COALESCE(SUM(t2.tonnage), 0))::numeric, 2) AS balance,
                    t1.Ni,
                    t1.Co,
                    t1.Al2O3,
                    t1.CaO,
                    t1.Cr2O3,
                    t1.Fe,
                    t1.Mgo,
                    t1.SiO2,
                    t1.MC,
                    t1.SM
                FROM inventory_by_dome AS t1
                LEFT JOIN selling_by_dome AS t2 
                    ON t2.stockpile = t1.stockpile 
                    AND t2.dome = t1.pile_id
                WHERE t1.status_dome != 'Finished'
            """
        else:
            raise ValueError("Unsupported database vendor.")

        # Add filters if any
        if count_filters:
            query += " AND " + " AND ".join(count_filters)

        # Add the GROUP BY clause
        query += """
            GROUP BY 
                t1.stockpile, 
                t1.nama_material, 
                t1.Ni, 
                t1.Co, 
                t1.Al2O3, 
                t1.CaO, 
                t1.Cr2O3, 
                t1.Fe, 
                t1.Mgo, 
                t1.SiO2, 
                t1.MC, 
                t1.SM
        """

        # Add ordering and pagination (if needed)
        query += """
            ORDER BY t1.nama_material ASC, t1.stockpile ASC
        """

        if db_vendor == 'postgresql':
            query += f" LIMIT {per_page} OFFSET {offset};"
        elif db_vendor in ['mssql', 'microsoft']:
            query += f" OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY;"
        else:
            raise ValueError("Unsupported database vendor.")

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query,params)
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            sql_data = []

        for item in sql_data:
            for field in [
                'total_ore', 'released', 'total_selling', 'balance',
                'ni', 'co', 'al2o3', 'cao', 'cr2o3', 'fe', 'mgo', 'sio2', 'mc', 'sm'
            ]:
                val = item.get(field)
                if isinstance(val, Decimal):
                    item[field] = float(val)
                elif isinstance(val, (float, int)):
                    item[field] = float(val)
                elif isinstance(val, str) and val.replace('.', '', 1).isdigit():
                    item[field] = float(val)
    
    # Tambahkan ini setelah `sql_data` selesai dikonversi
    total_released = sum(item['released'] for item in sql_data if item['released'])
    total_ore      = sum(item['total_ore'] for item in sql_data if item['total_ore'])
    total_selling  = sum(item['total_selling'] for item in sql_data if item['total_selling'])
    total_balance  = sum(item['balance'] for item in sql_data if item['balance'])


    def weighted_avg(field):
        return sum(item[field] * item['released'] for item in sql_data if item['released']) / total_released if total_released else 0

    sum_results = {
            'total_ore': total_ore,
            'total_released': total_released,
            'total_selling': total_selling,
            'total_balance': total_balance,
            'avg_ni': weighted_avg('ni'),
            'avg_co': weighted_avg('co'),
            'avg_al2o3': weighted_avg('al2o3'),
            'avg_cao': weighted_avg('cao'),
            'avg_cr2o3': weighted_avg('cr2o3'),
            'avg_fe': weighted_avg('fe'),
            'avg_mgo': weighted_avg('mgo'),
            'avg_sio2': weighted_avg('sio2'),
            'avg_mc': weighted_avg('mc')
    }

    
    # Calculate if there is more data
    more_data = len(sql_data) == per_page
    total_pages = (total_data // per_page) + (1 if total_data % per_page > 0 else 0)

    return JsonResponse({
        'data'      : sql_data,
        'summary'   : sum_results,
        'pagination': {
            'more'  : more_data,
            'total_pages': total_pages,
            'current_page': page,
            'total_data': total_data
        }
    })

# Get Finish Inventory
def get_inventory_finished(request):
    saleFilter   = request.GET.get('saleFilter')
    # Ambil filter dari request
    areaFilter  = request.GET.get('areaFilter', '[]')  # Menggunakan '[]' sebagai default jika None
    pointFilter = request.GET.get('pointFilter', '[]')  # Menggunakan '[]' sebagai default jika None

    # Parsing JSON
    areaFilter  = json.loads(areaFilter)  # Parsing JSON menjadi list
    pointFilter = json.loads(pointFilter)  # Parsing JSON menjadi lis

    # Pagination setup
    page = int(request.GET.get('page', 1))
    per_page = 50
    offset = (page - 1) * per_page

    # Query to count total data
    count_query = """
        SELECT COUNT(*)
        FROM inventory_by_dome AS t1
        LEFT JOIN selling_by_dome AS t2 ON 
            t2.stockpile = t1.stockpile AND
            t2.dome = t1.pile_id
        WHERE t1.status_dome = 'Finished'
    """

    # Apply filters to the count query
    count_filters = []
    params = []

    if saleFilter:
        count_filters.append("t1.sale_adjust = %s")
        params.append(saleFilter)

    # Memeriksa dan menambahkan filter untuk stockpile
    if areaFilter: 
        count_filters.append(f"t1.stockpile IN ({', '.join(['%s'] * len(areaFilter))})")
        params.extend(areaFilter)

    # Memeriksa dan menambahkan filter untuk pile_id
    if pointFilter:  
        count_filters.append(f"t1.pile_id IN ({', '.join(['%s'] * len(pointFilter))})")
        params.extend(pointFilter)


    if count_filters:
        count_query += " AND " + " AND ".join(count_filters)

    # Execute count query
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(count_query,params)
        result = cursor.fetchone()
        total_data = result[0] if result else 0 


    # Main data query with pagination
    if db_vendor == 'postgresql':
        query = """
            SELECT
                t1.stockpile,
                t1.pile_id,
                t1.total_ore,
                t1.released,
                t1.nama_material,
                COALESCE(ROUND(t2.tonnage::numeric, 2), 0) AS total_selling,
                ROUND((t1.released - COALESCE(t2.tonnage, 0))::numeric, 2) AS balance,
                t1.Ni,
                t1.Co,
                t1.Al2O3,
                t1.CaO,
                t1.Cr2O3,
                t1.Fe,
                t1.Mgo,
                t1.SiO2,
                t1.MC,
                t1.SM
            FROM inventory_by_dome AS t1
            LEFT JOIN selling_by_dome AS t2 
                ON t2.stockpile = t1.stockpile 
                AND t2.dome = t1.pile_id
            WHERE t1.status_dome = 'Finished'
        """
    else:
        raise ValueError("Unsupported database vendor.")
    
    if count_filters:
        query += " AND " + " AND ".join(count_filters)

    # Add pagination and order by clauses
    query += " ORDER BY t1.nama_material ASC, t1.stockpile ASC"
    
    # Query untuk mengambil data 
    if db_vendor == 'postgresql':
        query += f" LIMIT {per_page} OFFSET {offset};"
       
    elif db_vendor in ['mssql', 'microsoft']:
        # Adding pagination (OFFSET-FETCH) SQL SERVER
        query += f" OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY;"
    else:
        raise ValueError("Unsupported database vendor.")

    # Fetch paginated data
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query,params)
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            sql_data = []

    
    for item in sql_data:
            for field in [
                'total_ore', 'released', 'total_selling', 'balance',
                'ni', 'co', 'al2o3', 'cao', 'cr2o3', 'fe', 'mgo', 'sio2', 'mc', 'sm'
            ]:
                val = item.get(field)
                if isinstance(val, Decimal):
                    item[field] = float(val)
                elif isinstance(val, (float, int)):
                    item[field] = float(val)
                elif isinstance(val, str) and val.replace('.', '', 1).isdigit():
                    item[field] = float(val)


    # Calculate if there is more data
    more_data = len(sql_data) == per_page
    total_pages = (total_data // per_page) + (1 if total_data % per_page > 0 else 0)

    return JsonResponse({
        'data': sql_data,
        'pagination': {
            'more': more_data,
            'total_pages': total_pages,
            'current_page': page,
            'total_data': total_data
        }
    })

def get_stockpile_finished(request):
    saleFilter = request.GET.get('saleFilter')
    areaFilter  = request.GET.get('areaFilter', '[]')  # Menggunakan '[]' sebagai default jika None
    # Parsing JSON
    areaFilter  = json.loads(areaFilter)  # Parsing JSON menjadi list

    # Pagination setup
    page = int(request.GET.get('page', 1))
    per_page = 50
    offset = (page - 1) * per_page

    # Query to count total data
    count_query = """
        SELECT COUNT(*)
        FROM inventory_by_dome AS t1
        LEFT JOIN selling_by_dome AS t2 ON 
            t2.stockpile = t1.stockpile AND
            t2.dome = t1.pile_id
        WHERE t1.status_dome = 'Finished'
    """

    # Apply filters to the count query
    count_filters = []
    params = []

    if saleFilter:
        count_filters.append("t1.sale_adjust = %s")
        params.append(saleFilter)

    if areaFilter:  # Pastikan areaFilter tidak kosong
        count_filters.append(f"t1.stockpile IN ({', '.join(['%s'] * len(areaFilter))})")
        params.extend(areaFilter)

    if count_filters:
        count_query += " AND " + " AND ".join(count_filters)

    # Execute count query
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(count_query,params)
        result = cursor.fetchone()
        total_data = result[0] if result else 0 
   

    if db_vendor == 'postgresql':
            query = """
                SELECT
                    t1.stockpile,
                    SUM(t1.total_ore) AS total_ore,
                    SUM(t1.released) AS released,
                    t1.nama_material,
                    COALESCE(ROUND(SUM(t2.tonnage)::numeric, 2), 0) AS total_selling,
                    COALESCE(ROUND((SUM(t1.total_ore) - SUM(t2.tonnage))::numeric, 2), 0) AS balance,
                    t1.Ni,
                    t1.Co,
                    t1.Al2O3,
                    t1.CaO,
                    t1.Cr2O3,
                    t1.Fe,
                    t1.Mgo,
                    t1.SiO2,
                    t1.MC,
                    t1.SM
                FROM inventory_by_dome AS t1
                LEFT JOIN selling_by_dome AS t2 
                    ON t2.stockpile = t1.stockpile 
                    AND t2.dome = t1.pile_id
                WHERE t1.status_dome='Finished'
            """
    else:
        raise ValueError("Unsupported database vendor.")
    
    if count_filters:
            query += " AND " + " AND ".join(count_filters)

    query += """
            GROUP BY 
                t1.stockpile, 
                t1.nama_material, 
                t2.sale_adjust, 
                t1.Ni, 
                t1.Co, 
                t1.Al2O3, 
                t1.CaO, 
                t1.Cr2O3, 
                t1.Fe, 
                t1.Mgo, 
                t1.SiO2, 
                t1.MC, 
                t1.SM
        """

    # Add ordering and pagination (if needed)
    query += """
            ORDER BY t1.nama_material ASC, t1.stockpile ASC
        """ 
    # Query untuk mengambil data dengan pagination
    if db_vendor == 'postgresql':
        query += f" LIMIT {per_page} OFFSET {offset};"
       
    elif db_vendor in ['mssql', 'microsoft']:
        # Adding pagination (OFFSET-FETCH) SQL SERVER
        query += f" OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY;"
    else:
        raise ValueError("Unsupported database vendor.")

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params)
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            sql_data = []

    
    for item in sql_data:
            for field in [
                'total_ore', 'released', 'total_selling', 'balance',
                'ni', 'co', 'al2o3', 'cao', 'cr2o3', 'fe', 'mgo', 'sio2', 'mc', 'sm'
            ]:
                val = item.get(field)
                if isinstance(val, Decimal):
                    item[field] = float(val)
                elif isinstance(val, (float, int)):
                    item[field] = float(val)
                elif isinstance(val, str) and val.replace('.', '', 1).isdigit():
                    item[field] = float(val)
    
    # Calculate if there is more data
    more_data   = len(sql_data) == per_page
    total_pages = (total_data // per_page) + (1 if total_data % per_page > 0 else 0)

    return JsonResponse({
        'data': sql_data,
        'pagination': {
            'more': more_data,
            'total_pages': total_pages,
            'current_page': page,
            'total_data': total_data
        }
    })