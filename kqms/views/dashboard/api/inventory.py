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
                                    SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN s.netto_weigth_f ELSE 0 END)
                                    FROM ore_sellings s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_wb < %s
                                ), 0) AS lim_awal,
                                -- Saprolite
                                COALESCE((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END)
                                    FROM ore_productions op
                                    LEFT JOIN materials m ON m.id = op.id_material
                                    WHERE tgl_production < %s
                                ), 0) -
                                COALESCE((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN s.netto_weigth_f ELSE 0 END)
                                    FROM ore_sellings s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_wb < %s
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
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN s.netto_weigth_f ELSE 0 END) AS lim_out,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN s.netto_weigth_f ELSE 0 END) AS sap_out
                            FROM ore_sellings s
                            LEFT JOIN materials m ON m.id = s.id_material
                            WHERE date_wb BETWEEN %s AND %s
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
                                    SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN s.netto_weigth_f ELSE 0 END)
                                    FROM ore_sellings s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_wb < %s
                                ), 0) AS lim_awal,

                                -- Saprolite
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END)
                                    FROM ore_productions op
                                    LEFT JOIN materials m ON m.id = op.id_material
                                    WHERE tgl_production < %s
                                ), 0) -
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN s.netto_weigth_f ELSE 0 END)
                                    FROM ore_sellings s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_wb < %s
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
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN s.netto_weigth_f ELSE 0 END) AS lim_out,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN s.netto_weigth_f ELSE 0 END) AS sap_out
                            FROM ore_sellings s
                            LEFT JOIN materials m ON m.id = s.id_material
                            WHERE date_wb BETWEEN %s AND %s
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
                                    SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN s.netto_weigth_f ELSE 0 END)
                                    FROM ore_sellings s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_wb < %s
                                ), 0) AS lim_awal,
                                -- Saprolite
                                COALESCE((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END)
                                    FROM ore_productions op
                                    LEFT JOIN materials m ON m.id = op.id_material
                                    WHERE tgl_production < %s
                                ), 0) -
                                COALESCE((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN s.netto_weigth_f ELSE 0 END)
                                    FROM ore_sellings s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_wb < %s
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
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN s.netto_weigth_f ELSE 0 END) AS lim_out,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN s.netto_weigth_f ELSE 0 END) AS sap_out
                            FROM ore_sellings s
                            LEFT JOIN materials m ON m.id = s.id_material
                            WHERE date_wb BETWEEN %s AND %s
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
                                    SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN s.netto_weigth_f ELSE 0 END)
                                    FROM ore_sellings s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_wb < %s
                                ), 0) AS lim_awal,

                                -- Saprolite
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END)
                                    FROM ore_productions op
                                    LEFT JOIN materials m ON m.id = op.id_material
                                    WHERE tgl_production < %s
                                ), 0) -
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN s.netto_weigth_f ELSE 0 END)
                                    FROM ore_sellings s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_wb < %s
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
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN s.netto_weigth_f ELSE 0 END) AS lim_out,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN s.netto_weigth_f ELSE 0 END) AS sap_out
                            FROM ore_sellings s
                            LEFT JOIN materials m ON m.id = s.id_material
                            WHERE date_wb BETWEEN %s AND %s
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
                start_date.strftime('%Y-%m-%d'),  # 2: date_wb < %s
                start_date.strftime('%Y-%m-%d'),  # 3: tgl_production < %s
                start_date.strftime('%Y-%m-%d'),  # 4: date_wb < %s
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
                                    SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN s.netto_weigth_f ELSE 0 END)
                                    FROM ore_sellings s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_wb < %s
                                ), 0) AS lim_awal,
                                -- Saprolite
                                COALESCE((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END)
                                    FROM ore_productions op
                                    LEFT JOIN materials m ON m.id = op.id_material
                                    WHERE tgl_production < %s
                                ), 0) -
                                COALESCE((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN s.netto_weigth_f ELSE 0 END)
                                    FROM ore_sellings s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_wb < %s
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
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN s.netto_weigth_f ELSE 0 END) AS lim_out,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN s.netto_weigth_f ELSE 0 END) AS sap_out
                            FROM ore_sellings s
                            LEFT JOIN materials m ON m.id = s.id_material
                            WHERE date_wb BETWEEN %s AND %s
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
                                    SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN s.netto_weigth_f ELSE 0 END)
                                    FROM ore_sellings s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_wb < %s
                                ), 0) AS lim_awal,

                                -- Saprolite
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END)
                                    FROM ore_productions op
                                    LEFT JOIN materials m ON m.id = op.id_material
                                    WHERE tgl_production < %s
                                ), 0) -
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN s.netto_weigth_f ELSE 0 END)
                                    FROM ore_sellings s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_wb < %s
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
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN s.netto_weigth_f ELSE 0 END) AS lim_out,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN s.netto_weigth_f ELSE 0 END) AS sap_out
                            FROM ore_sellings s
                            LEFT JOIN materials m ON m.id = s.id_material
                            WHERE date_wb BETWEEN %s AND %s
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
                                    SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN s.netto_weigth_f ELSE 0 END)
                                    FROM ore_sellings s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE EXTRACT(YEAR FROM date_wb) < %s
                                ), 0) AS lim_awal,
                                -- Saprolite
                                COALESCE((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END)
                                    FROM ore_productions op
                                    LEFT JOIN materials m ON m.id = op.id_material
                                     WHERE EXTRACT(YEAR FROM tgl_production) < %s
                                ), 0) -
                                COALESCE((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN s.netto_weigth_f ELSE 0 END)
                                    FROM ore_sellings s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE EXTRACT(YEAR FROM date_wb) < %s
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
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN s.netto_weigth_f ELSE 0 END) AS lim_out,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN s.netto_weigth_f ELSE 0 END) AS sap_out
                            FROM ore_sellings s
                            LEFT JOIN materials m ON m.id = s.id_material
                            WHERE EXTRACT(YEAR FROM date_wb) = %s
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
                                    SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN s.netto_weigth_f ELSE 0 END)
                                    FROM ore_sellings s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_wb < %s
                                ), 0) AS lim_awal,

                                -- Saprolite
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END)
                                    FROM ore_productions op
                                    LEFT JOIN materials m ON m.id = op.id_material
                                    WHERE tgl_production < %s
                                ), 0) -
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN s.netto_weigth_f ELSE 0 END)
                                    FROM ore_sellings s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_wb < %s
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
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN s.netto_weigth_f ELSE 0 END) AS lim_out,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN s.netto_weigth_f ELSE 0 END) AS sap_out
                            FROM ore_sellings s
                            LEFT JOIN materials m ON m.id = s.id_material
                            WHERE YEAR(date_wb) = %s
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
                                SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN s.netto_weigth_f ELSE 0 END)
                                FROM ore_sellings s
                                LEFT JOIN materials m ON m.id = s.id_material
                                WHERE date_wb < %s
                            ), 0) AS lim_awal,

                            COALESCE((
                                SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END)
                                FROM ore_productions op
                                LEFT JOIN materials m ON m.id = op.id_material
                                WHERE tgl_production < %s
                            ), 0) -
                            COALESCE((
                                SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN s.netto_weigth_f ELSE 0 END)
                                FROM ore_sellings s
                                LEFT JOIN materials m ON m.id = s.id_material
                                WHERE date_wb < %s
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
                            SUM(CASE WHEN m.nama_material = 'LIM' THEN s.netto_weigth_f ELSE 0 END) AS lim_out,
                            SUM(CASE WHEN m.nama_material = 'SAP' THEN s.netto_weigth_f ELSE 0 END) AS sap_out
                        FROM ore_sellings s
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
                                    SELECT SUM(CASE WHEN m.nama_material = 'LIM' THEN s.netto_weigth_f ELSE 0 END)
                                    FROM ore_sellings s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_wb < %s
                                ), 0) AS lim_awal,

                                -- Saprolite
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END)
                                    FROM ore_productions op
                                    LEFT JOIN materials m ON m.id = op.id_material
                                    WHERE tgl_production < %s
                                ), 0) -
                                ISNULL((
                                    SELECT SUM(CASE WHEN m.nama_material = 'SAP' THEN s.netto_weigth_f ELSE 0 END)
                                    FROM ore_sellings s
                                    LEFT JOIN materials m ON m.id = s.id_material
                                    WHERE date_wb < %s
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
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN s.netto_weigth_f ELSE 0 END) AS lim_out,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN s.netto_weigth_f ELSE 0 END) AS sap_out
                            FROM ore_sellings s
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
                                    date_wb::date AS date,
                                    SUM(netto_weigth_f) AS total_out
                                FROM ore_sellings s
                                LEFT JOIN materials m ON m.id = s.id_material
                                WHERE date_wb BETWEEN %s AND %s
                                GROUP BY date_wb
                            ),
                            saldo_awal AS (
                                SELECT
                                    COALESCE((
                                        SELECT SUM(tonnage)
                                        FROM ore_productions
                                        WHERE tgl_production < %s
                                    ), 0) - COALESCE((
                                        SELECT SUM(netto_weigth_f)
                                        FROM ore_sellings
                                        WHERE date_wb < %s
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
                 query = """
                        WITH tanggal AS (
                            SELECT CAST(%s AS DATE) AS date
                            UNION ALL
                            SELECT DATEADD(DAY, 1, date)
                            FROM tanggal
                            WHERE date < %s
                        ),
                        incoming AS (
                            SELECT
                                CAST(tgl_production AS DATE) AS date,
                                SUM(tonnage) AS total_in
                            FROM ore_productions
                            WHERE tgl_production BETWEEN %s AND %s
                            GROUP BY CAST(tgl_production AS DATE)
                        ),
                        outgoing AS (
                            SELECT
                                CAST(date_wb AS DATE) AS date,
                                SUM(netto_weigth_f) AS total_out
                            FROM ore_sellings s
                            LEFT JOIN materials m ON m.id = s.id_material
                            WHERE date_wb BETWEEN %s AND %s
                            GROUP BY CAST(date_wb AS DATE)
                        )
                        SELECT
                            CONVERT(VARCHAR, t.date, 23) AS label,
                            ISNULL(i.total_in, 0) AS total_in,
                            ISNULL(o.total_out, 0) AS total_out
                        FROM tanggal t
                        LEFT JOIN incoming i ON t.date = i.date
                        LEFT JOIN outgoing o ON t.date = o.date
                        ORDER BY t.date
                        OPTION (MAXRECURSION 1000)
                    """
             
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
                                date_wb::date AS date,
                                SUM(netto_weigth_f) AS total_out
                            FROM ore_sellings s
                            LEFT JOIN materials m ON m.id = s.id_material
                            WHERE date_wb BETWEEN %s AND %s
                            GROUP BY date_wb
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
                                    SELECT SUM(netto_weigth_f)
                                    FROM ore_sellings
                                    WHERE date_wb < %s
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
                query = """
                    WITH tanggal AS (
                        SELECT CAST(%s AS DATE) AS date
                        UNION ALL
                        SELECT DATEADD(DAY, 1, date)
                        FROM tanggal
                        WHERE date < %s
                    ),
                    incoming AS (
                        SELECT
                            CAST(tgl_production AS DATE) AS date,
                            SUM(tonnage) AS total_in
                        FROM ore_productions
                        WHERE tgl_production BETWEEN %s AND %s
                        GROUP BY CAST(tgl_production AS DATE)
                    ),
                    outgoing AS (
                        SELECT
                            CAST(date_wb AS DATE) AS date,
                            SUM(netto_weigth_f) AS total_out
                        FROM ore_sellings s
                        LEFT JOIN materials m ON m.id = s.id_material
                        WHERE date_wb BETWEEN %s AND %s
                        GROUP BY CAST(date_wb AS DATE)
                    ),
                    daily AS (
                        SELECT
                            t.date,
                            ISNULL(i.total_in, 0) AS total_in,
                            ISNULL(o.total_out, 0) AS total_out
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
                                SELECT SUM(netto_weigth_f)
                                FROM ore_sellings
                                WHERE date_wb < %s
                            ), 0) AS value
                    )
                    SELECT 
                        DATENAME(WEEKDAY, date) AS label, -- Nama hari (Sunday, Monday, ...)
                        COALESCE(i.total_in, 0) AS total_in,
                        COALESCE(o.total_out, 0) AS total_out,
                        SUM(COALESCE(i.total_in, 0) - COALESCE(o.total_out, 0))
                            OVER (ORDER BY t.date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
                            + (SELECT value FROM saldo_awal) AS running_balance
                    FROM daily
                    GROUP BY DATENAME(WEEKDAY, date), DATEPART(WEEKDAY, date)
                    ORDER BY DATEPART(WEEKDAY, date)
                    OPTION (MAXRECURSION 1000);
                """

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
                                    date_wb::date AS date,
                                    SUM(netto_weigth_f) AS total_out
                                FROM ore_sellings s
                                LEFT JOIN materials m ON m.id = s.id_material
                                WHERE date_wb BETWEEN %s AND %s
                                GROUP BY date_wb
                            ),
                            saldo_awal AS (
                                SELECT
                                    COALESCE((
                                        SELECT SUM(tonnage)
                                        FROM ore_productions
                                        WHERE tgl_production < %s
                                    ), 0) - COALESCE((
                                        SELECT SUM(netto_weigth_f)
                                        FROM ore_sellings
                                        WHERE date_wb < %s
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
                query = """
                        WITH tanggal AS (
                            SELECT CAST(%s AS DATE) AS date
                            UNION ALL
                            SELECT DATEADD(DAY, 1, date)
                            FROM tanggal
                            WHERE date < %s
                        ),
                        incoming AS (
                            SELECT
                                CAST(tgl_production AS DATE) AS date,
                                SUM(tonnage) AS total_in
                            FROM ore_productions
                            WHERE tgl_production BETWEEN %s AND %s
                            GROUP BY CAST(tgl_production AS DATE)
                        ),
                        outgoing AS (
                            SELECT
                                CAST(date_wb AS DATE) AS date,
                                SUM(netto_weigth_f) AS total_out
                            FROM ore_sellings s
                            LEFT JOIN materials m ON m.id = s.id_material
                            WHERE date_wb BETWEEN %s AND %s
                            GROUP BY CAST(date_wb AS DATE)
                        )
                        SELECT
                            CONVERT(VARCHAR, t.date, 23) AS label,
                            ISNULL(i.total_in, 0) AS total_in,
                            ISNULL(o.total_out, 0) AS total_out
                        FROM tanggal t
                        LEFT JOIN incoming i ON t.date = i.date
                        LEFT JOIN outgoing o ON t.date = o.date
                        ORDER BY t.date
                        OPTION (MAXRECURSION 1000)
                    """
       
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
                                EXTRACT(MONTH FROM date_wb)::int AS month,
                                SUM(netto_weigth_f) AS total_out
                            FROM ore_sellings s
                            LEFT JOIN materials m ON m.id = s.id_material
                            WHERE EXTRACT(YEAR FROM date_wb) = %s
                            GROUP BY EXTRACT(MONTH FROM date_wb)
                        ),
                        saldo_awal AS (
                            SELECT
                                COALESCE((
                                    SELECT SUM(tonnage)
                                    FROM ore_productions
                                    WHERE EXTRACT(YEAR FROM tgl_production) < %s
                                ), 0) - COALESCE((
                                    SELECT SUM(netto_weigth_f)
                                    FROM ore_sellings
                                    WHERE EXTRACT(YEAR FROM date_wb) < %s
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
                query = """
                    WITH bulan AS (
                        SELECT 1 AS month
                        UNION ALL SELECT 2
                        UNION ALL SELECT 3
                        UNION ALL SELECT 4
                        UNION ALL SELECT 5
                        UNION ALL SELECT 6
                        UNION ALL SELECT 7
                        UNION ALL SELECT 8
                        UNION ALL SELECT 9
                        UNION ALL SELECT 10
                        UNION ALL SELECT 11
                        UNION ALL SELECT 12
                    ),
                    incoming AS (
                        SELECT
                            MONTH(tgl_production) AS month,
                            SUM(tonnage) AS total_in
                        FROM ore_productions
                        WHERE YEAR(tgl_production) = %s
                        GROUP BY MONTH(tgl_production)
                    ),
                    outgoing AS (
                        SELECT
                            MONTH(date_wb) AS month,
                            SUM(netto_weigth_f) AS total_out
                        FROM ore_sellings s
                        LEFT JOIN materials m ON m.id = s.id_material
                        WHERE YEAR(date_wb) = %s
                        GROUP BY MONTH(date_wb)
                    )
                    SELECT
                        DATENAME(MONTH, DATEFROMPARTS(%s, b.month, 1)) AS label,
                        ISNULL(i.total_in, 0) AS total_in,
                        ISNULL(o.total_out, 0) AS total_out
                    FROM bulan b
                    LEFT JOIN incoming i ON b.month = i.month
                    LEFT JOIN outgoing o ON b.month = o.month
                    ORDER BY b.month
                """
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
                            EXTRACT(YEAR FROM date_wb)::int AS year,
                            SUM(netto_weigth_f) AS total_out
                        FROM ore_sellings s
                        LEFT JOIN materials m ON m.id = s.id_material
                        GROUP BY EXTRACT(YEAR FROM date_wb)
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
                query = """
                    WITH incoming AS (
                        SELECT
                            YEAR(tgl_production) AS year,
                            SUM(tonnage) AS total_in
                        FROM ore_productions
                        GROUP BY YEAR(tgl_production)
                    ),
                    outgoing AS (
                        SELECT
                            YEAR(date_wb) AS year,
                            SUM(netto_weigth_f) AS total_out
                        FROM ore_sellings s
                        LEFT JOIN materials m ON m.id = s.id_material
                        GROUP BY YEAR(date_wb)
                    )
                    SELECT
                        ISNULL(i.year, o.year) AS label,
                        ISNULL(i.total_in, 0) AS total_in,
                        ISNULL(o.total_out, 0) AS total_out
                    FROM incoming i
                    FULL OUTER JOIN outgoing o ON i.year = o.year
                    ORDER BY label
                """
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
    if ni >= 1.6 and mgo >= 7.0 and fe <= 27.0:
        return "HGS"
    elif 1.2 <= ni < 1.6 and mgo >= 7.0 and fe <= 27.0:
        return "MGS"
    elif ni < 1.2 and 7.0 <= mgo <= 20.0 and fe <= 27.0:
        return "LGS"
    elif ni >= 1.1 and mgo < 7.0 and fe >= 27.0:
        return "HGL"
    elif ni < 1.1 and mgo < 7.0 and fe >= 27.0:
        return "LGL"
    elif ni < 0.9 and mgo < 7.0 and fe < 27.0:
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

