# views.py
import logging
from django.http import JsonResponse
from django.db import connections, DatabaseError
from prophet import Prophet
import pandas as pd
import calendar
from datetime import datetime, timedelta
from ....utils.utils import validate_month,validate_year
import itertools
from django.db.models import Sum
from django.utils.timezone import now
from django.db.models.functions import TruncWeek
logger = logging.getLogger(__name__)
from ....utils.db_utils import get_db_vendor
from decimal import Decimal

# Memanggil fungsi utility
db_vendor = get_db_vendor('kqms_db')

def to_float1(v):
    return round(float(v or 0), 1)


def decimal_to_float(value):
    return float(value) if isinstance(value, Decimal) else value

# Card Summary
def build_summary_query(db_vendor: str, where_clause: str) -> str:
    if db_vendor == 'postgresql':
        return f"""
            SELECT 
                COALESCE(ROUND(SUM(CASE WHEN sale_adjust IN ('HPAL', 'RKEF') THEN tonnage ELSE 0 END)::numeric, 2), 0) AS total,
                COALESCE(ROUND(SUM(CASE WHEN sale_adjust = 'HPAL' THEN tonnage ELSE 0 END)::numeric, 2), 0) AS total_lim,
                COALESCE(ROUND(SUM(CASE WHEN sale_adjust = 'RKEF' THEN tonnage ELSE 0 END)::numeric, 2), 0) AS total_sap
            FROM details_selling_barging
            {where_clause}
        """
    elif db_vendor in ['mysql', 'mssql', 'microsoft']:
        return f"""
            SELECT
                COALESCE(ROUND(SUM(CASE WHEN sale_adjust IN ('HPAL', 'RKEF') THEN tonnage ELSE 0 END), 2), 0) AS total,
                COALESCE(ROUND(SUM(CASE WHEN sale_adjust = 'HPAL' THEN tonnage ELSE 0 END), 2), 0) AS total_lim,
                COALESCE(ROUND(SUM(CASE WHEN sale_adjust = 'RKEF' THEN tonnage ELSE 0 END), 2), 0) AS total_sap
            FROM details_selling_barging
            {where_clause}
        """
    else:
        raise ValueError("Unsupported vendor")

def get_selling_summary(request):
    try:
        filter_type = request.GET.get('filter_type')
        year        = request.GET.get('year')
        month       = request.GET.get('month')
        week        = request.GET.get('week')
        date_start  = request.GET.get('date_start')
        date_end    = request.GET.get('date_end')
        filter_date = request.GET.get('filter_date')

        where_clause = "WHERE 1=1"
        params = []

        # Filter logika ...
        if filter_type =='daily' and filter_date:
            where_clause += " AND date_barge_out = %s"
            params += [filter_date]
        elif filter_type =='range' and date_start and date_end:
            where_clause += " AND date_barge_out BETWEEN %s AND %s"
            params += [date_start, date_end]
        elif filter_type =='weekly' and week:
            # Contoh week: '2025-26'
            where_clause += " AND TO_CHAR(date_barge_out, 'IYYY-IW') = %s" \
                if db_vendor == 'postgresql' else \
                " AND DATE_FORMAT(date_barge_out, '%%x-%%v') = %s"
            params += [week]
        elif filter_type =='monthly' and year and month:
            where_clause += " AND EXTRACT(YEAR FROM date_barge_out) = %s AND EXTRACT(MONTH FROM date_barge_out) = %s" \
                if db_vendor == 'postgresql' else \
                " AND YEAR(date_barge_out) = %s AND MONTH(date_barge_out) = %s"
            params += [year, month]
        elif filter_type =='yearly' and year:
            where_clause += " AND EXTRACT(YEAR FROM date_barge_out) = %s" \
                if db_vendor == 'postgresql' else \
                " AND YEAR(date_barge_out) = %s"
            params.append(year)
        elif filter_type =='all':
            pass
        elif filter_type not in ['1', '2', '3', '4', '5']:
            return JsonResponse({'error': 'Invalid filter type'}, status=400)

        query = build_summary_query(db_vendor, where_clause)

        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()

        return JsonResponse({
            "total_ore": to_float1(row[0]),
            "total_lim": to_float1(row[1]),
            "total_sap": to_float1(row[2]),
        })

    except DatabaseError:
        logger.exception("Database query failed.")
        return JsonResponse({'error': 'Database error'}, status=500)
    except Exception as e:
        logger.exception("Unexpected error in get_ore_summary")
        return JsonResponse({'error': str(e)}, status=500)

# Create Chart Ore
def get_chart_selling(request):
    try:
        filter_type = request.GET.get('filter_type')
        year        = request.GET.get('year')
        month       = request.GET.get('month')
        week        = request.GET.get('week')
        date_start  = request.GET.get('date_start')
        date_end    = request.GET.get('date_end')
        filter_date = request.GET.get('filter_date')

        if filter_type =='daily' and filter_date : 
            if db_vendor == 'postgresql':
                query = """
                        WITH working_hours AS (
                            SELECT
                                hour_label,
                                CASE WHEN hour_label >= 7 THEN hour_label ELSE hour_label+24 END AS sort_order
                            FROM generate_series(0,23) AS hour_label
                        ),
                        -- 🔹 Total actual per hari
                        actual_daily AS (
                            SELECT
                                SUM(CASE WHEN sale_adjust='HPAL' THEN os.tonnage ELSE 0 END) AS actual_lim,
                                SUM(CASE WHEN sale_adjust='RKEF' THEN os.tonnage ELSE 0 END) AS actual_sap
                            FROM ore_sellings_barging os
                            LEFT JOIN materials m ON m.id = os.id_material
                            WHERE DATE(date_barge_out)=%s::date
                        ),
                        -- 🔹 Distribusi actual per jam (dibagi 22 jam kerja)
                        actual_hourly AS (
                            SELECT
                                wh.hour_label,
                                (ad.actual_lim/22.0) AS actual_lim,
                                (ad.actual_sap/22.0) AS actual_sap
                            FROM working_hours wh
                            CROSS JOIN actual_daily ad
                            WHERE wh.hour_label BETWEEN 7 AND 23 OR wh.hour_label BETWEEN 0 AND 4
                        ),
                        -- 🔹 Total plan per hari
                        plan_daily AS (
                            SELECT
                                SUM(CASE WHEN type_ore='LIM' THEN tonnage_plan ELSE 0 END) AS plan_lim,
                                SUM(CASE WHEN type_ore='SAP' THEN tonnage_plan ELSE 0 END) AS plan_sap
                            FROM ore_sellings_plan_barging
                            WHERE plan_date=%s::date
                        ),
                        -- 🔹 Distribusi plan per jam (dibagi 22 jam kerja)
                        plan_hourly AS (
                            SELECT
                                wh.hour_label,
                                (pd.plan_lim/22.0) AS plan_lim,
                                (pd.plan_sap/22.0) AS plan_sap
                            FROM working_hours wh
                            CROSS JOIN plan_daily pd
                            WHERE wh.hour_label BETWEEN 7 AND 23 OR wh.hour_label BETWEEN 0 AND 4
                        )
                        -- 🔹 Output final
                        SELECT
                            wh.hour_label AS label,
                            COALESCE(a.actual_lim,0)+COALESCE(a.actual_sap,0) AS actual_total,
                            COALESCE(a.actual_lim,0) AS actual_lim,
                            COALESCE(a.actual_sap,0) AS actual_sap
                            COALESCE(p.plan_lim,0)+COALESCE(p.plan_sap,0) AS plan_total,
                            COALESCE(p.plan_lim,0) AS plan_lim,
                            COALESCE(p.plan_sap,0) AS plan_sap
                        FROM working_hours wh
                        LEFT JOIN actual_hourly a ON a.hour_label=wh.hour_label
                        LEFT JOIN plan_hourly   p ON p.hour_label=wh.hour_label
                        ORDER BY wh.sort_order;
                    """ 
            else:
                raise ValueError("Unsupported vendor")

            params = [filter_date, filter_date]

        elif filter_type =='range' and date_start and date_end:

            if db_vendor == 'postgresql':
                query = """
                   WITH tanggal AS (
                        SELECT generate_series(%s::date, %s::date, interval '1 day') AS date
                    ),
                    -- 🔹 Actual per tanggal
                    actual AS (
                        SELECT
                            date_barge_out::date AS date,
                            SUM(CASE WHEN sale_adjust='HPAL' THEN s.tonnage ELSE 0 END) AS lim,
                            SUM(CASE WHEN sale_adjust='RKEF' THEN s.tonnage ELSE 0 END) AS sap
                        FROM ore_sellings_barging s
                        LEFT JOIN materials m ON m.id = s.id_material
                        WHERE date_barge_out BETWEEN %s AND %s
                        GROUP BY date_barge_out::date
                    ),
                    -- 🔹 Plan per tanggal
                    plan AS (
                        SELECT
                            plan_date::date AS date,
                            SUM(CASE WHEN type_ore = 'LIM' THEN tonnage_plan ELSE 0 END) AS lim,
                            SUM(CASE WHEN type_ore = 'SAP' THEN tonnage_plan ELSE 0 END) AS sap
                        FROM ore_sellings_plan_barging
                        WHERE plan_date BETWEEN %s AND %s
                        GROUP BY plan_date::date
                    ),
                    -- 🔹 Detail per tanggal + barge_code
                    detail AS (
                        SELECT
                            date_barge_out::date AS date,
                            mb.barge_code,
                            SUM(CASE WHEN sale_adjust='HPAL' THEN s.tonnage ELSE 0 END) AS lim,
                            SUM(CASE WHEN sale_adjust='RKEF' THEN s.tonnage ELSE 0 END) AS sap,
                            SUM(s.tonnage) AS total
                        FROM ore_sellings_barging s
                        LEFT JOIN materials m ON m.id = s.id_material
                        LEFT JOIN master_barge mb ON mb.id = s.barge_code
                        WHERE date_barge_out BETWEEN %s AND %s
                        GROUP BY date_barge_out::date, mb.barge_code
                    )
                    SELECT
                        TO_CHAR(tanggal.date, 'YYYY-MM-DD') AS label,
                        COALESCE(a.lim, 0) + COALESCE(a.sap, 0) AS actual_total,
                        COALESCE(a.lim, 0) AS actual_lim,
                        COALESCE(a.sap, 0) AS actual_sap,
                        COALESCE(p.lim, 0) + COALESCE(p.sap, 0) AS plan_total,
                        COALESCE(p.lim, 0) AS plan_lim,
                        COALESCE(p.sap, 0) AS plan_sap,
                        COALESCE(json_agg(
                            json_build_object(
                                'barge_code', d.barge_code,
                                'lim', d.lim,
                                'sap', d.sap,
                                'total', d.total
                            )
                            ORDER BY d.barge_code
                        ) FILTER (WHERE d.barge_code IS NOT NULL), '[]') AS barges
                    FROM tanggal
                    LEFT JOIN actual a ON tanggal.date = a.date
                    LEFT JOIN plan p ON tanggal.date = p.date
                    LEFT JOIN detail d ON tanggal.date = d.date
                    GROUP BY tanggal.date, a.lim, a.sap, p.lim, p.sap
                    ORDER BY tanggal.date;
                """
            else:
                raise ValueError("Unsupported vendor")
            
            params = [date_start, date_end,
                      date_start, date_end,
                      date_start, date_end,
                      date_start, date_end]

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
                    -- 🔹 Actual per tanggal
                    actual AS (
                        SELECT
                            date_barge_out::date AS date,
                            SUM(CASE WHEN sale_adjust='HPAL' THEN tonnage ELSE 0 END) AS actual_lim,
                            SUM(CASE WHEN sale_adjust='RKEF' THEN tonnage ELSE 0 END) AS actual_sap
                        FROM ore_sellings_barging s
                        LEFT JOIN materials m ON m.id = s.id_material
                        WHERE date_barge_out BETWEEN %s AND %s
                        GROUP BY date_barge_out
                    ),
                    -- 🔹 Plan per tanggal
                    plan AS (
                        SELECT
                            plan_date::date AS date,
                            SUM(CASE WHEN type_ore = 'LIM' THEN tonnage_plan ELSE 0 END) AS plan_lim,
                            SUM(CASE WHEN type_ore = 'SAP' THEN tonnage_plan ELSE 0 END) AS plan_sap
                        FROM ore_sellings_plan_barging
                        WHERE plan_date BETWEEN %s AND %s
                        GROUP BY plan_date
                    ),
                    -- 🔹 Detail barge per tanggal
                    detail AS (
                        SELECT
                            date_barge_out::date AS date,
                            mb.barge_code,
                            SUM(CASE WHEN sale_adjust='HPAL' THEN tonnage ELSE 0 END) AS lim,
                            SUM(CASE WHEN sale_adjust='RKEF' THEN tonnage ELSE 0 END) AS sap,
                            SUM(tonnage) AS total
                        FROM ore_sellings_barging s
                        LEFT JOIN master_barge mb ON mb.id = s.barge_code
                        WHERE date_barge_out BETWEEN %s AND %s
                        GROUP BY date_barge_out, mb.barge_code
                    ),
                    -- 🔹 Gabungkan semua (actual + plan + detail)
                    combine AS (
                        SELECT
                            tanggal.date,
                            TO_CHAR(tanggal.date, 'FMDay') AS day_name,
                            COALESCE(a.actual_lim, 0) AS actual_lim,
                            COALESCE(a.actual_sap, 0) AS actual_sap,
                            COALESCE(p.plan_lim, 0) AS plan_lim,
                            COALESCE(p.plan_sap, 0) AS plan_sap,
                            COALESCE(json_agg(
                                json_build_object(
                                    'barge_code', d.barge_code,
                                    'lim', d.lim,
                                    'sap', d.sap,
                                    'total', d.total
                                )
                                ORDER BY d.barge_code
                            ) FILTER (WHERE d.barge_code IS NOT NULL), '[]') AS barges
                        FROM tanggal
                        LEFT JOIN actual a ON tanggal.date = a.date
                        LEFT JOIN plan p   ON tanggal.date = p.date
                        LEFT JOIN detail d ON tanggal.date = d.date
                        GROUP BY tanggal.date, day_name, a.actual_lim, a.actual_sap, p.plan_lim, p.plan_sap
                    )
                    -- 🔹 Agregasi by day_name
                    SELECT
                        day_name AS label,
                        SUM(actual_lim + actual_sap) AS actual_total,
                        SUM(actual_lim) AS actual_lim,
                        SUM(actual_sap) AS actual_sap,
                        SUM(plan_lim + plan_sap) AS plan_total,
                        SUM(plan_lim) AS plan_lim,
                        SUM(plan_sap) AS plan_sap,
                        json_agg(
                            json_build_object(
                                'date', to_char(date, 'YYYY-MM-DD'),
                                'lim', actual_lim,
                                'sap', actual_sap,
                                'total', actual_lim + actual_sap,
                                'plan_lim', plan_lim,
                                'plan_sap', plan_sap,
                                'plan_total', plan_lim + plan_sap,
                                'barges', barges
                            )
                            ORDER BY date
                        ) AS details
                    FROM combine
                    GROUP BY day_name
                    ORDER BY ARRAY_POSITION(
                        ARRAY['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'],
                        day_name
                    );
                """
            else:
                raise ValueError("Unsupported vendor")
        
            params = [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'),
                      start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'),
                      start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'),
                      start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
                      ]

        elif filter_type =='monthly' and year and month: 
            year  = int(year)
            month = int(month)
            # Ambil jumlah hari terakhir dalam bulan
            last_day = calendar.monthrange(year, month)[1]
            # Bangun tanggal awal dan akhir bulan
            tgl_pertama  = datetime(year, month, 1).date()
            tgl_terakhir = datetime(year, month, last_day).date()

            # Siapkan parameter untuk query
            params = [
                      tgl_pertama, tgl_terakhir, 
                      tgl_pertama, tgl_terakhir,
                      tgl_pertama, tgl_terakhir,
                      tgl_pertama, tgl_terakhir
                      ]
            
            if db_vendor == 'postgresql':
                query = """
                  WITH tanggal AS (
                        SELECT generate_series(%s::date, %s::date, interval '1 day')::date AS date
                    ),
                    summary AS (
                        SELECT
                            date_barge_out::date AS date,
                            ROUND(SUM(tonnage)::numeric, 2) AS total,
                            ROUND(SUM(CASE WHEN sale_adjust='HPAL' THEN tonnage ELSE 0 END)::numeric, 2) AS lim,
                            ROUND(SUM(CASE WHEN sale_adjust='RKEF' THEN tonnage ELSE 0 END)::numeric, 2) AS sap
                        FROM ore_sellings_barging s
                        WHERE date_barge_out BETWEEN %s AND %s
                        GROUP BY date_barge_out::date
                    ),
                    detail AS (
                        SELECT
                            date_barge_out::date AS date,
                            mb.barge_code,
                            ROUND(SUM(CASE WHEN sale_adjust='HPAL' THEN tonnage ELSE 0 END)::numeric, 2) AS lim,
                            ROUND(SUM(CASE WHEN sale_adjust='RKEF' THEN tonnage ELSE 0 END)::numeric, 2) AS sap,
                            ROUND(SUM(tonnage)::numeric, 2) AS total
                        FROM ore_sellings_barging s
                        LEFT JOIN master_barge mb ON mb.id = s.barge_code
                        WHERE date_barge_out BETWEEN %s AND %s
                        GROUP BY date_barge_out::date, mb.barge_code
                    ),
                    plan AS (
                        SELECT
                            plan_date::date AS date,
                            ROUND(SUM(CASE WHEN type_ore = 'LIM' THEN tonnage_plan ELSE 0 END)::numeric, 2) AS lim_plan,
                            ROUND(SUM(CASE WHEN type_ore = 'SAP' THEN tonnage_plan ELSE 0 END)::numeric, 2) AS sap_plan,
                            ROUND(SUM(tonnage_plan)::numeric, 2) AS total_plan
                        FROM ore_sellings_plan_barging
                        WHERE plan_date::date BETWEEN %s AND %s
                        GROUP BY plan_date::date
                    )
                    SELECT
                        TO_CHAR(tanggal.date, 'DD') AS label,
                        COALESCE(s.total, 0) AS total,
                        COALESCE(s.lim, 0) AS lim,
                        COALESCE(s.sap, 0) AS sap,
                        COALESCE(p.total_plan, 0) AS total_plan,
                        COALESCE(p.lim_plan, 0) AS lim_plan,
                        COALESCE(p.sap_plan, 0) AS sap_plan,
                        COALESCE(json_agg(
                            json_build_object(
                                'barge_code', d.barge_code,
                                'lim', d.lim,
                                'sap', d.sap,
                                'total', d.total
                            )
                            ORDER BY d.barge_code
                        ) FILTER (WHERE d.barge_code IS NOT NULL), '[]') AS barges
                    FROM tanggal
                    LEFT JOIN summary s ON tanggal.date = s.date
                    LEFT JOIN detail d ON tanggal.date = d.date
                    LEFT JOIN plan p ON tanggal.date = p.date
                    GROUP BY tanggal.date, s.total, s.lim, s.sap, p.total_plan, p.lim_plan, p.sap_plan
                    ORDER BY tanggal.date;
                """
            else:
                raise ValueError("Unsupported vendor")
       
        elif filter_type =='yearly' and year: 
            if db_vendor == 'postgresql':
                query = """
                    WITH bulan AS (
                        SELECT generate_series(1, 12) AS month
                    ),
                    -- 🔹 Summary actual per bulan
                    summary AS (
                        SELECT
                            EXTRACT(MONTH FROM date_barge_out)::int AS month,
                            ROUND(SUM(tonnage)::numeric, 2) AS total,
                            ROUND(SUM(CASE WHEN sale_adjust='HPAL' THEN tonnage ELSE 0 END)::numeric, 2) AS lim,
                            ROUND(SUM(CASE WHEN sale_adjust='RKEF' THEN tonnage ELSE 0 END)::numeric, 2) AS sap
                        FROM ore_sellings_barging s
                        LEFT JOIN materials m ON m.id = s.id_material
                        LEFT JOIN master_barge mb ON mb.id = s.barge_code
                        WHERE EXTRACT(YEAR FROM date_barge_out) = %s
                        GROUP BY EXTRACT(MONTH FROM date_barge_out)
                    ),
                    -- 🔹 Detail per bulan + barge_code
                    detail AS (
                        SELECT
                            EXTRACT(MONTH FROM date_barge_out)::int AS month,
                            mb.barge_code,
                            ROUND(SUM(CASE WHEN sale_adjust='HPAL' THEN tonnage ELSE 0 END)::numeric, 2) AS lim,
                            ROUND(SUM(CASE WHEN sale_adjust='RKEF' THEN tonnage ELSE 0 END)::numeric, 2) AS sap,
                            ROUND(SUM(tonnage)::numeric, 2) AS total
                        FROM ore_sellings_barging s
                        LEFT JOIN materials m ON m.id = s.id_material
                        LEFT JOIN master_barge mb ON mb.id = s.barge_code
                        WHERE EXTRACT(YEAR FROM date_barge_out) = %s
                        GROUP BY EXTRACT(MONTH FROM date_barge_out), mb.barge_code
                    ),
                    -- 🔹 Plan per bulan
                    plan AS (
                        SELECT
                            EXTRACT(MONTH FROM plan_date)::int AS month,
                            ROUND(SUM(CASE WHEN type_ore = 'LIM' THEN tonnage_plan ELSE 0 END)::numeric, 2) AS lim_plan,
                            ROUND(SUM(CASE WHEN type_ore = 'SAP' THEN tonnage_plan ELSE 0 END)::numeric, 2) AS sap_plan,
                            ROUND(SUM(tonnage_plan)::numeric, 2) AS total_plan
                        FROM ore_sellings_plan_barging
                        WHERE EXTRACT(YEAR FROM plan_date) = %s
                        GROUP BY EXTRACT(MONTH FROM plan_date)
                    )
                    SELECT
                        TO_CHAR(TO_DATE(bulan.month::text, 'MM'), 'Mon') AS label,
                        COALESCE(s.total, 0)::float AS total,
                        COALESCE(s.lim, 0)::float AS lim,
                        COALESCE(s.sap, 0)::float AS sap,
                        COALESCE(p.total_plan, 0)::float AS total_plan,
                        COALESCE(p.lim_plan, 0)::float AS lim_plan,
                        COALESCE(p.sap_plan, 0)::float AS sap_plan,
                        COALESCE(json_agg(
                            json_build_object(
                                'barge_code', d.barge_code,
                                'lim', d.lim,
                                'sap', d.sap,
                                'total', d.total
                            )
                            ORDER BY d.barge_code
                        ) FILTER (WHERE d.barge_code IS NOT NULL), '[]') AS barges
                    FROM bulan
                    LEFT JOIN summary s ON bulan.month = s.month
                    LEFT JOIN detail d ON bulan.month = d.month
                    LEFT JOIN plan p ON bulan.month = p.month
                    GROUP BY bulan.month, s.total, s.lim, s.sap, p.total_plan, p.lim_plan, p.sap_plan
                    ORDER BY bulan.month;
                """
            else:
                raise ValueError("Unsupported vendor")
            params = [year,year,year]

        elif filter_type =='all':
            if db_vendor == 'postgresql':
                query = """
                    WITH tahun AS (
                        SELECT generate_series(
                            (SELECT MIN(EXTRACT(YEAR FROM date_barge_out))::int FROM ore_sellings_barging),
                            (SELECT MAX(EXTRACT(YEAR FROM date_barge_out))::int FROM ore_sellings_barging)
                        ) AS year
                    ),
                    -- 🔹 Summary actual per tahun
                    summary AS (
                        SELECT
                            EXTRACT(YEAR FROM date_barge_out)::int AS year,
                            ROUND(SUM(tonnage)::numeric, 2) AS total,
                            ROUND(SUM(CASE WHEN sale_adjust='HPAL' THEN tonnage ELSE 0 END)::numeric, 2) AS lim,
                            ROUND(SUM(CASE WHEN sale_adjust='RKEF' THEN tonnage ELSE 0 END)::numeric, 2) AS sap
                        FROM ore_sellings_barging s
                        LEFT JOIN master_barge mb ON mb.id = s.barge_code
                        GROUP BY EXTRACT(YEAR FROM date_barge_out)
                    ),
                    -- 🔹 Detail per tahun + barge_code
                    detail AS (
                        SELECT
                            EXTRACT(YEAR FROM date_barge_out)::int AS year,
                            mb.barge_code,
                            ROUND(SUM(CASE WHEN sale_adjust='HPAL' THEN tonnage ELSE 0 END)::numeric, 2) AS lim,
                            ROUND(SUM(CASE WHEN sale_adjust='RKEF' THEN tonnage ELSE 0 END)::numeric, 2) AS sap,
                            ROUND(SUM(tonnage)::numeric, 2) AS total
                        FROM ore_sellings_barging s
                        LEFT JOIN master_barge mb ON mb.id = s.barge_code
                        GROUP BY EXTRACT(YEAR FROM date_barge_out), mb.barge_code
                    ),
                    -- 🔹 Plan per tahun
                    plan AS (
                        SELECT
                            EXTRACT(YEAR FROM plan_date)::int AS year,
                            ROUND(SUM(CASE WHEN type_ore = 'LIM' THEN tonnage_plan ELSE 0 END)::numeric, 2) AS lim_plan,
                            ROUND(SUM(CASE WHEN type_ore = 'SAP' THEN tonnage_plan ELSE 0 END)::numeric, 2) AS sap_plan,
                            ROUND(SUM(tonnage_plan)::numeric, 2) AS total_plan
                        FROM ore_sellings_plan_barging
                        GROUP BY EXTRACT(YEAR FROM plan_date)
                    )
                    SELECT
                        tahun.year::text AS label,
                        COALESCE(s.total, 0)::float AS total,
                        COALESCE(s.lim, 0)::float AS lim,
                        COALESCE(s.sap, 0)::float AS sap,
                        COALESCE(p.total_plan, 0)::float AS total_plan,
                        COALESCE(p.lim_plan, 0)::float AS lim_plan,
                        COALESCE(p.sap_plan, 0)::float AS sap_plan,
                        COALESCE(json_agg(
                            json_build_object(
                                'barge_code', d.barge_code,
                                'lim', d.lim,
                                'sap', d.sap,
                                'total', d.total
                            )
                            ORDER BY d.barge_code
                        ) FILTER (WHERE d.barge_code IS NOT NULL), '[]') AS barges
                    FROM tahun
                    LEFT JOIN summary s ON tahun.year = s.year
                    LEFT JOIN detail d ON tahun.year = d.year
                    LEFT JOIN plan p ON tahun.year = p.year
                    GROUP BY tahun.year, s.total, s.lim, s.sap, p.total_plan, p.lim_plan, p.sap_plan
                    ORDER BY tahun.year;
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

        def round_barges(barges_list):
            for b in barges_list:
                for key in ['lim', 'sap', 'total']:
                    if key in b and b[key] is not None:
                        b[key] = round(float(b[key]), 1)
                if 'barges' in b and isinstance(b['barges'], list):
                    round_barges(b['barges'])

        details = []

        print("Params:", params)
        print("First row:", results[0] if results else None)

        for row in results:
            barges = row[7] if row[7] else []
            round_barges(barges)

            details.append({
                'label'        : str(row[0]),
                'total_actual' : round(float(row[1] or 0), 1),
                'lim_actual'   : round(float(row[2] or 0), 1),
                'sap_actual'   : round(float(row[3] or 0), 1),
                'total_plan'   : round(float(row[4] or 0), 1),
                'lim_plan'     : round(float(row[5] or 0), 1),
                'sap_plan'     : round(float(row[6] or 0), 1),
                'barges'       : barges
            })

        return JsonResponse({
            'summary': {
                'x_data'       : [d['label'] for d in details],
                'y_data_actual': [d['total_actual'] for d in details],
                'y_data_lim'   : [d['lim_actual'] for d in details],
                'y_data_sap'   : [d['sap_actual'] for d in details],
                'y_plan_total' : [d['total_plan'] for d in details],
                'y_plan_lim'   : [d['lim_plan'] for d in details],
                'y_plan_sap'   : [d['sap_plan'] for d in details],
            },
            'details': details
        })

    except DatabaseError:
        logger.exception("DB Error in chart selling")
        return JsonResponse({'error': 'Database error'}, status=500)
    except Exception as e:
        logger.exception("Unexpected error in chart selling")
        return JsonResponse({'error': str(e)}, status=500)

def get_chart_selling_class(request):
    try:
            
        filter_type = request.GET.get('filter_type')
        year = request.GET.get('year')
        month = request.GET.get('month')
        week = request.GET.get('week')
        date_start = request.GET.get('date_start')
        date_end = request.GET.get('date_end')

        filter_sql = "WHERE 1=1"
        params = []

        # Tentukan kondisi filter SQL dan parameter
        if filter_type =='range' and date_start and date_end:  # Range
            filter_sql += " AND date_barge_out BETWEEN %s AND %s"
            params = [date_start, date_end]

        elif filter_type =='weekly' and year and month and week:  # Weekly
            year, month, week = int(year), int(month), int(week)
            first_day = datetime(year, month, 1)
            start_date = first_day + timedelta(days=(week - 1) * 7)
            end_date = start_date + timedelta(days=6)
            if end_date.month != month:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            filter_sql += " AND date_barge_out BETWEEN %s AND %s"
            params = [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]

        elif filter_type =='monthly' and year and month:  # Monthly
            filter_sql += " AND EXTRACT(YEAR FROM date_barge_out) = %s AND EXTRACT(MONTH FROM date_barge_out) = %s" \
                if db_vendor == 'postgresql' else " AND YEAR(date_barge_out) = %s AND MONTH(date_barge_out) = %s"
            params = [year, month]

        elif filter_type =='yearly' and year:  # Yearly
            filter_sql += " AND EXTRACT(YEAR FROM date_barge_out) = %s" \
                if db_vendor == 'postgresql' else " AND YEAR(date_barge_out) = %s"
            params = [year]

        elif filter_type =='all':  # All
            pass  # Tidak ada tambahan filter

        else:
            return JsonResponse({'error': 'Invalid or incomplete filter parameters'}, status=400)

        # Query berdasarkan vendor
        if db_vendor == 'postgresql':
            query = f"""
                SELECT
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'LGLO' THEN tonnage ELSE 0 END)::NUMERIC, 2), 0) AS LGLO,
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'MGLO' THEN tonnage ELSE 0 END)::NUMERIC, 2), 0) AS MGLO,
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'HGLO' THEN tonnage ELSE 0 END)::NUMERIC, 2), 0) AS HGLO,
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'LGSO' THEN tonnage ELSE 0 END)::NUMERIC, 2), 0) AS LGSO,
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'MGSO' THEN tonnage ELSE 0 END)::NUMERIC, 2), 0) AS MGSO,
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'HGSO' THEN tonnage ELSE 0 END)::NUMERIC, 2), 0) AS HGSO
                FROM ore_sellingss
                {filter_sql}
            """
        elif db_vendor in ['mysql', 'mssql', 'microsoft']:
            query = f"""
                SELECT
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'LGLO' THEN tonnage ELSE 0 END), 2), 0) AS LGLO,
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'MGLO' THEN tonnage ELSE 0 END), 2), 0) AS MGLO,
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'HGLO' THEN tonnage ELSE 0 END), 2), 0) AS HGLO,
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'LGSO' THEN tonnage ELSE 0 END), 2), 0) AS LGSO,
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'MGSO' THEN tonnage ELSE 0 END), 2), 0) AS MGSO,
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'HGSO' THEN tonnage ELSE 0 END), 2), 0) AS HGSO
                FROM ore_sellingss
                {filter_sql}
            """
        else:
            raise ValueError(f"Unsupported database vendor: {db_vendor}")

        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchone()  # karena hasil SUM hanya satu baris

        # Konversi hasil menjadi list
        y_data = [float(val) for val in chart_data] if chart_data else [0, 0, 0, 0, 0, 0]


        return JsonResponse({
            'labels': ['LGLO', 'MGLO', 'HGLO', 'LGSO', 'MGSO', 'HGSO'],
            'y_data': y_data,
        })

    except DatabaseError:
        logger.exception("Database query failed.")
        return JsonResponse({'error': 'Internal server error'}, status=500)

    except Exception as e:
        logger.exception("Unexpected error occurred.")
        return JsonResponse({'error': str(e)}, status=500)

def forecast_selling(request):
    query = """
            SELECT * FROM weekly_production_summary
        """
    try:
        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query)  
            data = cursor.fetchall()

        # Konversi ke DataFrame
        df = pd.DataFrame(list(data), columns=['ds', 'y'])
        df['ds'] = pd.to_datetime(df['ds'])  # Pastikan kolom tanggal berbentuk datetime
        # Pastikan semua tanggal adalah Senin
        # df['ds'] = df['ds'] - pd.to_timedelta(df['ds'].dt.weekday, unit='d')  # Geser ke Senin

        # Ganti NaN dengan 0 pada kolom 'y'
        df['y'] = df['y'].fillna(0)

        # Model Prophet
        model = Prophet()
        model.fit(df)

        # Prediksi 1 minggu ke depan
        # future = model.make_future_dataframe(periods=1, freq='W') #parameter freq='W' yang secara default mengacu pada minggu
        # Prediksi 1 minggu ke depan, mulai dari Senin
        future = model.make_future_dataframe(periods=1, freq='W-MON')  # Mengatur minggu dimulai dari Senin

        forecast = model.predict(future)

        # Pastikan yhat_lower tidak bernilai negatif
        forecast['yhat_lower'] = forecast['yhat_lower'].clip(lower=0)

        # Gabungkan data actual dan forecast
        actual = df[['ds', 'y']].rename(columns={'y': 'actual'})  # Data historis

        forecast_data = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].rename(columns={'yhat': 'forecast'})

        # Replace NaN in both actual and forecast columns with None
        forecast_data = forecast_data.where(pd.notnull(forecast_data), None)
        actual = actual.where(pd.notnull(actual), None)

        # Gabungkan data actual dan forecast
        merged_data = pd.merge(forecast_data, actual, on='ds', how='left')

        # Debugging: Periksa isi merged_data dan kolom-kolomnya
        # print(merged_data.head())

        # Pastikan data aktual untuk setiap tanggal ada
        merged_data['actual'] = merged_data['actual'].fillna(0)  # Ganti NaN dengan 0

        # Kirim data JSON ke template menggunakan JsonResponse
        return JsonResponse({
            'dates'     : merged_data['ds'].astype(str).tolist(),
            'actual'    : merged_data['actual'].tolist(),  # Aktifkan ini
            'forecast'  : merged_data['forecast'].tolist(),
            'yhat_lower': merged_data['yhat_lower'].tolist(),
            'yhat_upper': merged_data['yhat_upper'].tolist()
        })
       
    
    except DatabaseError:
        logger.exception("Database query failed.")
        return JsonResponse({'error': 'Internal server error'}, status=500)


