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

# Memanggil fungsi utility
db_vendor = get_db_vendor('kqms_db')

def to_float1(v):
    return round(float(v or 0), 1)

# Card Summary
def build_summary_query(db_vendor: str, where_clause: str) -> str:
    if db_vendor == 'postgresql':
        return f"""
            SELECT 
                COALESCE(ROUND(SUM(CASE WHEN sale_adjust IN ('HPAL', 'RKEF') THEN tonnage ELSE 0 END)::numeric, 2), 0) AS total,
                COALESCE(ROUND(SUM(CASE WHEN sale_adjust = 'HPAL' THEN tonnage ELSE 0 END)::numeric, 2), 0) AS total_lim,
                COALESCE(ROUND(SUM(CASE WHEN sale_adjust = 'RKEF' THEN tonnage ELSE 0 END)::numeric, 2), 0) AS total_sap
            FROM details_selling
            {where_clause}
        """
    elif db_vendor in ['mysql', 'mssql', 'microsoft']:
        return f"""
            SELECT
                COALESCE(ROUND(SUM(CASE WHEN sale_adjust IN ('HPAL', 'RKEF') THEN tonnage ELSE 0 END), 2), 0) AS total,
                COALESCE(ROUND(SUM(CASE WHEN sale_adjust = 'HPAL' THEN tonnage ELSE 0 END), 2), 0) AS total_lim,
                COALESCE(ROUND(SUM(CASE WHEN sale_adjust = 'RKEF' THEN tonnage ELSE 0 END), 2), 0) AS total_sap
            FROM details_selling
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

        where_clause = "WHERE 1=1"
        params = []

        # Filter logika ...
        if filter_type =='range' and date_start and date_end:
            where_clause += " AND date_wb BETWEEN %s AND %s"
            params += [date_start, date_end]
        elif filter_type =='weekly' and week:
            # Contoh week: '2025-26'
            where_clause += " AND TO_CHAR(date_wb, 'IYYY-IW') = %s" \
                if db_vendor == 'postgresql' else \
                " AND DATE_FORMAT(date_wb, '%%x-%%v') = %s"
            params += [week]
        elif filter_type =='monthly' and year and month:
            where_clause += " AND EXTRACT(YEAR FROM date_wb) = %s AND EXTRACT(MONTH FROM date_wb) = %s" \
                if db_vendor == 'postgresql' else \
                " AND YEAR(date_wb) = %s AND MONTH(date_wb) = %s"
            params += [year, month]
        elif filter_type =='yearly' and year:
            where_clause += " AND EXTRACT(YEAR FROM date_wb) = %s" \
                if db_vendor == 'postgresql' else \
                " AND YEAR(date_wb) = %s"
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
        daily       = request.GET.get('daily')

        if filter_type =='daily' and daily : 
            if db_vendor == 'postgresql':
                query = """
                        WITH working_hours AS (
                            SELECT
                                hour_label,
                                CASE
                                    WHEN hour_label >= 7 THEN hour_label
                                    ELSE hour_label + 24
                                END AS sort_order
                            FROM generate_series(0, 23) AS hour_label
                        ),
                        actual AS (
                            SELECT
                                EXTRACT(HOUR FROM time_hauling) AS hour_label,
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN os.netto_weigth_f ELSE 0 END) AS actual_lim,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN os.netto_weigth_f ELSE 0 END) AS actual_sap
                            FROM ore_sellings os
                            LEFT JOIN materials m ON m.id = os.id_material
                            WHERE DATE(date_wb) = %s::date
                            GROUP BY EXTRACT(HOUR FROM time_hauling)
                        ),
                        plan_total AS (
                            SELECT
                                SUM(CASE WHEN type_ore = 'LIM' THEN tonnage_plan ELSE 0 END) AS total_lim,
                                SUM(CASE WHEN type_ore = 'SAP' THEN tonnage_plan ELSE 0 END) AS total_sap
                            FROM ore_sellings_plan
                            WHERE plan_date = %s::date
                        ),
                        plan AS (
                            SELECT
                                wh.hour_label,
                                ROUND((COALESCE(pt.total_lim, 0) / 24.0)::numeric, 2) AS plan_lim,
                                ROUND((COALESCE(pt.total_sap, 0) / 24.0)::numeric, 2) AS plan_sap
                            FROM working_hours wh
                            CROSS JOIN plan_total pt
                        )
                        SELECT
                            wh.hour_label as label,
                            COALESCE(a.actual_lim, 0) AS actual_lim,
                            COALESCE(p.plan_lim, 0) AS plan_lim,
                            COALESCE(a.actual_sap, 0) AS actual_sap,
                            COALESCE(p.plan_sap, 0) AS plan_sap
                        FROM working_hours wh
                        LEFT JOIN actual a ON a.hour_label = wh.hour_label
                        LEFT JOIN plan p ON p.hour_label = wh.hour_label
                        ORDER BY wh.sort_order;
                    """ 
            elif db_vendor in ['mssql', 'microsoft']:
                query = """
                    WITH working_hours AS (
                        SELECT hour_label, 
                            CASE 
                                WHEN hour_label >= 7 THEN hour_label 
                                ELSE hour_label + 24 
                            END AS sort_order
                        FROM (
                            VALUES 
                                (0), (1), (2), (3), (4), (5), (6), (7), (8), (9), (10), (11),
                                (12), (13), (14), (15), (16), (17), (18), (19), (20), (21), (22), (23)
                        ) AS hours(hour_label)
                    ),
                    actual AS (
                        SELECT 
                            DATEPART(HOUR, time_hauling) AS hour_label,
                            SUM(CASE WHEN m.nama_material = 'LIM' THEN os.netto_weigth_f ELSE 0 END) AS actual_lim,
                            SUM(CASE WHEN m.nama_material = 'SAP' THEN os.netto_weigth_f ELSE 0 END) AS actual_sap
                        FROM ore_sellings os
                        LEFT JOIN materials m ON m.id = os.id_material
                        WHERE CAST(date_wb AS DATE) = %s
                        GROUP BY DATEPART(HOUR, time_hauling)
                    ),
                    plan_total AS (
                        SELECT 
                            SUM(CASE WHEN type_ore = 'LIM' THEN tonnage_plan ELSE 0 END) AS total_lim,
                            SUM(CASE WHEN type_ore = 'SAP' THEN tonnage_plan ELSE 0 END) AS total_sap
                        FROM ore_sellings_plan
                        WHERE CAST(plan_date AS DATE) = %s
                    ),
                    plan AS (
                        SELECT
                            wh.hour_label,
                            ROUND(ISNULL(pt.total_lim, 0) / 24.0, 2) AS plan_lim,
                            ROUND(ISNULL(pt.total_sap, 0) / 24.0, 2) AS plan_sap
                        FROM working_hours wh
                        CROSS JOIN plan_total pt
                    )
                    SELECT 
                        wh.hour_label AS label,
                        ISNULL(a.actual_lim, 0) AS actual_lim,
                        ISNULL(p.plan_lim, 0) AS plan_lim,
                        ISNULL(a.actual_sap, 0) AS actual_sap,
                        ISNULL(p.plan_sap, 0) AS plan_sap
                    FROM working_hours wh
                    LEFT JOIN actual a ON a.hour_label = wh.hour_label
                    LEFT JOIN plan p ON p.hour_label = wh.hour_label
                    ORDER BY wh.sort_order;
                """
            else:
                raise ValueError("Unsupported vendor")

            params = [daily, daily]

        elif filter_type =='range' and date_start and date_end: 
            query = """
                SELECT 
                    COALESCE(actual.date_wb::date, plan.plan_date) AS label,
                    COALESCE(actual.lim, 0) AS actual_lim,
                    COALESCE(plan.lim_plan, 0) AS plan_lim,
                    COALESCE(actual.sap, 0) AS actual_sap,
                    COALESCE(plan.sap_plan, 0) AS plan_sap
                FROM (
                    SELECT 
                        date_wb::date,
                        SUM(CASE WHEN nama_material = 'LIM' THEN netto_weigth_f ELSE 0 END) AS lim,
                        SUM(CASE WHEN nama_material = 'SAP' THEN netto_weigth_f ELSE 0 END) AS sap
                    FROM ore_sellings os 
                    left join materials m on m.id=os.id_material
                    WHERE date_wb BETWEEN %s AND %s
                    GROUP BY date_wb::date
                ) AS actual
                FULL OUTER JOIN (
                    SELECT 
                        plan_date,
                        SUM(CASE WHEN type_ore = 'LIM' THEN tonnage_plan ELSE 0 END) AS lim_plan,
                        SUM(CASE WHEN type_ore = 'SAP' THEN tonnage_plan ELSE 0 END) AS sap_plan
                    FROM ore_sellings_plan
                    WHERE plan_date BETWEEN %s AND %s
                    GROUP BY plan_date
                ) AS plan
                ON actual.date_wb::date = plan.plan_date
                ORDER BY label

            """ if db_vendor == 'postgresql' else """
                SELECT 
                        COALESCE(CONVERT(date, actual.date_wb), plan.plan_date) AS label,
                        COALESCE(actual.lim, 0) AS actual_lim,
                        COALESCE(plan.lim_plan, 0) AS plan_lim,
                        COALESCE(actual.sap, 0) AS actual_sap,
                        COALESCE(plan.sap_plan, 0) AS plan_sap
                    FROM (
                        SELECT 
                            CONVERT(date, s.date_wb) AS date_wb,
                            SUM(CASE WHEN m.nama_material = 'LIM' THEN s.netto_weigth_f ELSE 0 END) AS lim,
                            SUM(CASE WHEN m.nama_material = 'SAP' THEN s.netto_weigth_f ELSE 0 END) AS sap
                        FROM ore_sellings s
                        LEFT JOIN materials m ON m.id = s.id_material
                        WHERE s.date_wb BETWEEN %s AND %s
                        GROUP BY CONVERT(date, s.date_wb)
                    ) AS actual
                    FULL OUTER JOIN (
                        SELECT 
                            plan_date,
                            SUM(CASE WHEN type_ore = 'LIM' THEN tonnage_plan ELSE 0 END) AS lim_plan,
                            SUM(CASE WHEN type_ore = 'SAP' THEN tonnage_plan ELSE 0 END) AS sap_plan
                        FROM ore_sellings_plan
                        WHERE plan_date BETWEEN %s AND %s
                        GROUP BY plan_date
                    ) AS plan
                        ON CONVERT(date, actual.date_wb) = plan.plan_date
                    ORDER BY label
            """
            params = [date_start, date_end,date_start, date_end]

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
                    SELECT
                        hari.label,
                        COALESCE(actual.lim, 0) AS actual_lim,
                        COALESCE(plan.lim_plan, 0) AS plan_lim,
                        COALESCE(actual.sap, 0) AS actual_sap,
                        COALESCE(plan.sap_plan, 0) AS plan_sap
                    FROM (
                        SELECT unnest(ARRAY['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']) AS label
                    ) hari
                    LEFT JOIN (
                        SELECT 
                            TRIM(TO_CHAR(date_wb, 'Day')) AS hari,
                            SUM(CASE WHEN m.nama_material = 'LIM' THEN s.netto_weigth_f ELSE 0 END) AS lim,
                            SUM(CASE WHEN m.nama_material = 'SAP' THEN s.netto_weigth_f ELSE 0 END) AS sap
                        FROM ore_sellings s
                        LEFT JOIN materials m ON m.id = s.id_material
                        WHERE date_wb BETWEEN %s AND %s
                        GROUP BY hari
                    ) actual ON hari.label = actual.hari
                    LEFT JOIN (
                        SELECT 
                            TRIM(TO_CHAR(plan_date, 'Day')) AS hari,
                            SUM(CASE WHEN type_ore = 'LIM' THEN tonnage_plan ELSE 0 END) AS lim_plan,
                            SUM(CASE WHEN type_ore = 'SAP' THEN tonnage_plan ELSE 0 END) AS sap_plan
                        FROM ore_sellings_plan
                        WHERE plan_date BETWEEN %s AND %s
                        GROUP BY hari
                    ) plan ON hari.label = plan.hari
                    ORDER BY ARRAY_POSITION(
                        ARRAY['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'],
                        hari.label
                    )
                """
            else:
                query = """
                   SELECT
                        hari.label,
                        COALESCE(actual.lim, 0) AS actual_lim,
                        COALESCE(plan.lim_plan, 0) AS plan_lim,
                        COALESCE(actual.sap, 0) AS actual_sap,
                        COALESCE(plan.sap_plan, 0) AS plan_sap
                    FROM (
                        SELECT unnest(ARRAY['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']) AS label
                    ) hari
                    LEFT JOIN (
                        SELECT 
                            TRIM(TO_CHAR(date_wb, 'Day')) AS hari,
                            SUM(CASE WHEN m.nama_material = 'LIM' THEN s.netto_weigth_f ELSE 0 END) AS lim,
                            SUM(CASE WHEN m.nama_material = 'SAP' THEN s.netto_weigth_f ELSE 0 END) AS sap
                        FROM ore_sellings s
                        LEFT JOIN materials m ON m.id = s.id_material
                        WHERE date_wb BETWEEN %s AND %s
                        GROUP BY hari
                    ) actual ON hari.label = actual.hari
                    LEFT JOIN (
                        SELECT 
                            TRIM(TO_CHAR(plan_date, 'Day')) AS hari,
                            SUM(CASE WHEN type_ore = 'LIM' THEN tonnage_plan ELSE 0 END) AS lim_plan,
                            SUM(CASE WHEN type_ore = 'SAP' THEN tonnage_plan ELSE 0 END) AS sap_plan
                        FROM ore_sellings_plan
                        WHERE plan_date BETWEEN %s AND %s
                        GROUP BY hari
                    ) plan ON hari.label = plan.hari
                    ORDER BY ARRAY_POSITION(
                        ARRAY['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'],
                        hari.label
                    )
                """
            params = [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'),start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]

        elif filter_type =='monthly' and year and month: 
            year = int(year)
            month = int(month)

            # Ambil jumlah hari terakhir dalam bulan
            last_day = calendar.monthrange(year, month)[1]

            # Bangun tanggal awal dan akhir bulan
            tgl_pertama = datetime(year, month, 1).date()
            tgl_terakhir = datetime(year, month, last_day).date()

            

            # Siapkan parameter untuk query
            # params = [tgl_pertama, tgl_terakhir, tgl_terakhir.day]
            params = [tgl_pertama, tgl_terakhir, tgl_pertama, tgl_terakhir, tgl_terakhir.day]


            if db_vendor == 'postgresql':
                query = """
                   SELECT
                        tanggal.left_date AS label,
                        COALESCE(actual.total_lim, 0) AS actual_lim,
                        COALESCE(plan.lim_plan, 0) AS plan_lim,
                        COALESCE(actual.total_sap, 0) AS actual_sap,
                        COALESCE(plan.sap_plan, 0) AS plan_sap
                    FROM tanggal
                    LEFT JOIN (
                        SELECT
                            left_date,
                            SUM(CASE WHEN m.nama_material = 'LIM' THEN s.netto_weigth_f ELSE 0 END) AS total_lim,
                            SUM(CASE WHEN m.nama_material = 'SAP' THEN s.netto_weigth_f ELSE 0 END) AS total_sap
                        FROM ore_sellings s
                        LEFT JOIN materials m ON m.id = s.id_material
                        WHERE s.date_wb BETWEEN %s AND %s
                        GROUP BY left_date
                    ) AS actual ON tanggal.left_date = actual.left_date
                    LEFT JOIN (
                        SELECT
                            left_date,
                            SUM(CASE WHEN type_ore = 'LIM' THEN tonnage_plan ELSE 0 END) AS lim_plan,
                            SUM(CASE WHEN type_ore = 'SAP' THEN tonnage_plan ELSE 0 END) AS sap_plan
                        FROM ore_sellings_plan
                        WHERE plan_date BETWEEN %s AND %s
                        GROUP BY left_date
                    ) AS plan ON tanggal.left_date = plan.left_date
                    WHERE tanggal.left_date <= %s
                    ORDER BY tanggal.left_date

                """
            else:
                query = """
                   SELECT
                        tanggal.left_date AS label,
                        COALESCE(actual.total_lim, 0) AS actual_lim,
                        COALESCE(plan.lim_plan, 0) AS plan_lim,
                        COALESCE(actual.total_sap, 0) AS actual_sap,
                        COALESCE(plan.sap_plan, 0) AS plan_sap
                    FROM tanggal
                    LEFT JOIN (
                        SELECT
                            s.left_date,
                            SUM(CASE WHEN m.nama_material = 'LIM' THEN s.netto_weigth_f ELSE 0 END) AS total_lim,
                            SUM(CASE WHEN m.nama_material = 'SAP' THEN s.netto_weigth_f ELSE 0 END) AS total_sap
                        FROM ore_sellings s
                        LEFT JOIN materials m ON m.id = s.id_material
                        WHERE s.date_wb BETWEEN %s AND %s
                        GROUP BY s.left_date
                    ) AS actual ON tanggal.left_date = actual.left_date
                    LEFT JOIN (
                        SELECT
                            left_date,
                            SUM(CASE WHEN type_ore = 'LIM' THEN tonnage_plan ELSE 0 END) AS lim_plan,
                            SUM(CASE WHEN type_ore = 'SAP' THEN tonnage_plan ELSE 0 END) AS sap_plan
                        FROM ore_sellings_plan
                        WHERE plan_date BETWEEN %s AND %s
                        GROUP BY left_date
                    ) AS plan ON tanggal.left_date = plan.left_date
                    WHERE tanggal.left_date <= %s
                    ORDER BY tanggal.left_date
                """
       
        elif filter_type =='yearly' and year: 
            query = """
                SELECT 
                    TO_CHAR(COALESCE(actual.month_date, plan.month_date), 'Mon YYYY') AS label,
                    COALESCE(actual.lim, 0) AS actual_lim,
                    COALESCE(plan.lim_plan, 0) AS plan_lim,
                    COALESCE(actual.sap, 0) AS actual_sap,
                    COALESCE(plan.sap_plan, 0) AS plan_sap
                FROM (
                    SELECT 
                        DATE_TRUNC('month', date_wb) AS month_date,
                        SUM(CASE WHEN nama_material = 'LIM' THEN netto_weigth_f ELSE 0 END) AS lim,
                        SUM(CASE WHEN nama_material = 'SAP' THEN netto_weigth_f ELSE 0 END) AS sap
                    FROM ore_sellings os
                    LEFT JOIN materials m ON m.id = os.id_material
                    WHERE EXTRACT(YEAR FROM date_wb) = %s
                    GROUP BY DATE_TRUNC('month', date_wb)
                ) AS actual
                FULL OUTER JOIN (
                    SELECT 
                        DATE_TRUNC('month', plan_date) AS month_date,
                        SUM(CASE WHEN type_ore = 'LIM' THEN tonnage_plan ELSE 0 END) AS lim_plan,
                        SUM(CASE WHEN type_ore = 'SAP' THEN tonnage_plan ELSE 0 END) AS sap_plan
                    FROM ore_sellings_plan
                    WHERE EXTRACT(YEAR FROM plan_date) = %s
                    GROUP BY DATE_TRUNC('month', plan_date)
                ) AS plan
                ON actual.month_date = plan.month_date
                ORDER BY COALESCE(actual.month_date, plan.month_date)

            """ if db_vendor == 'postgresql' else """
                        SELECT 
                            FORMAT(COALESCE(actual.month_date, plan.month_date), 'MMM yyyy') AS label,
                            COALESCE(actual.lim, 0) AS actual_lim,
                            COALESCE(plan.lim_plan, 0) AS plan_lim,
                            COALESCE(actual.sap, 0) AS actual_sap,
                            COALESCE(plan.sap_plan, 0) AS plan_sap
                        FROM (
                            SELECT 
                                DATEFROMPARTS(YEAR(s.date_wb), MONTH(s.date_wb), 1) AS month_date,
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN s.netto_weigth_f ELSE 0 END) AS lim,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN s.netto_weigth_f ELSE 0 END) AS sap
                            FROM ore_sellings s
                            LEFT JOIN materials m ON m.id = s.id_material
                            WHERE YEAR(s.date_wb) = ?
                            GROUP BY YEAR(s.date_wb), MONTH(s.date_wb)
                        ) AS actual
                        FULL OUTER JOIN (
                            SELECT 
                                DATEFROMPARTS(YEAR(plan_date), MONTH(plan_date), 1) AS month_date,
                                SUM(CASE WHEN type_ore = 'LIM' THEN tonnage_plan ELSE 0 END) AS lim_plan,
                                SUM(CASE WHEN type_ore = 'SAP' THEN tonnage_plan ELSE 0 END) AS sap_plan
                            FROM ore_sellings_plan
                            WHERE YEAR(plan_date) = ?
                            GROUP BY YEAR(plan_date), MONTH(plan_date)
                        ) AS plan
                        ON actual.month_date = plan.month_date
                        ORDER BY COALESCE(actual.month_date, plan.month_date)

                """
            params = [year,year]

        elif filter_type =='all':
            query = """
                SELECT 
                    COALESCE(actual.year_label, plan.year_label) AS label,
                    COALESCE(actual.lim, 0) AS actual_lim,
                    COALESCE(plan.lim_plan, 0) AS plan_lim,
                    COALESCE(actual.sap, 0) AS actual_sap,
                    COALESCE(plan.sap_plan, 0) AS plan_sap
                FROM (
                    SELECT 
                        TO_CHAR(date_wb, 'YYYY') AS year_label,
                        SUM(CASE WHEN nama_material = 'LIM' THEN netto_weigth_f ELSE 0 END) AS lim,
                        SUM(CASE WHEN nama_material = 'SAP' THEN netto_weigth_f ELSE 0 END) AS sap
                    FROM ore_sellings os
                    LEFT JOIN materials m ON m.id = os.id_material
                    GROUP BY TO_CHAR(date_wb, 'YYYY')
                ) AS actual
                FULL OUTER JOIN (
                    SELECT 
                        TO_CHAR(plan_date, 'YYYY') AS year_label,
                        SUM(CASE WHEN type_ore = 'LIM' THEN tonnage_plan ELSE 0 END) AS lim_plan,
                        SUM(CASE WHEN type_ore = 'SAP' THEN tonnage_plan ELSE 0 END) AS sap_plan
                    FROM ore_sellings_plan
                    GROUP BY TO_CHAR(plan_date, 'YYYY')
                ) AS plan
                ON actual.year_label = plan.year_label
                ORDER BY label

            """ if db_vendor == 'postgresql' else """
            SELECT 
                COALESCE(actual.year_label, plan.year_label) AS label,
                COALESCE(actual.lim, 0) AS actual_lim,
                COALESCE(plan.lim_plan, 0) AS plan_lim,
                COALESCE(actual.sap, 0) AS actual_sap,
                COALESCE(plan.sap_plan, 0) AS plan_sap
            FROM (
                SELECT 
                    CAST(YEAR(s.date_wb) AS VARCHAR) AS year_label,
                    SUM(CASE WHEN m.nama_material = 'LIM' THEN s.netto_weigth_f ELSE 0 END) AS lim,
                    SUM(CASE WHEN m.nama_material = 'SAP' THEN s.netto_weigth_f ELSE 0 END) AS sap
                FROM ore_sellings s
                LEFT JOIN materials m ON m.id = s.id_material
                GROUP BY YEAR(s.date_wb)
            ) AS actual
            FULL OUTER JOIN (
                SELECT 
                    CAST(YEAR(plan_date) AS VARCHAR) AS year_label,
                    SUM(CASE WHEN type_ore = 'LIM' THEN tonnage_plan ELSE 0 END) AS lim_plan,
                    SUM(CASE WHEN type_ore = 'SAP' THEN tonnage_plan ELSE 0 END) AS sap_plan
                FROM ore_sellings_plan
                GROUP BY YEAR(plan_date)
            ) AS plan
            ON actual.year_label = plan.year_label
            ORDER BY label
            """
            params = []

        else:
            return JsonResponse({'error': 'Invalid or incomplete filter parameters'}, status=400)

        # Eksekusi query
        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            results = cursor.fetchall()

        x_labels     = []
        actual_total = []
        plan_total   = []

        # Data per material (opsional kalau mau tetap simpan)
        actual_lim = []
        plan_lim   = []
        actual_sap = []
        plan_sap   = []

        for row in results:
            print(f"ROW: {row} ({len(row)} fields)")
            # if len(row) < 5:
            #     continue  # skip jika data tidak lengkap

            label       = str(row[0])
            lim_actual  = float(row[1] or 0)
            lim_plan    = float(row[2] or 0)
            sap_actual  = float(row[3] or 0)
            sap_plan    = float(row[4] or 0)
            
            total_actual = lim_actual + sap_actual
            total_plan   = lim_plan + sap_plan

            x_labels.append(label)
            actual_lim.append(lim_actual)
            plan_lim.append(lim_plan)
            actual_sap.append(sap_actual)
            plan_sap.append(sap_plan)
            actual_total.append(total_actual)
            plan_total.append(total_plan)


        return JsonResponse({
            'x_data'       : x_labels,
            'y_data_plan'  : plan_total,
            'y_data_actual': actual_total,
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
            filter_sql += " AND date_wb BETWEEN %s AND %s"
            params = [date_start, date_end]

        elif filter_type =='weekly' and year and month and week:  # Weekly
            year, month, week = int(year), int(month), int(week)
            first_day = datetime(year, month, 1)
            start_date = first_day + timedelta(days=(week - 1) * 7)
            end_date = start_date + timedelta(days=6)
            if end_date.month != month:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            filter_sql += " AND date_wb BETWEEN %s AND %s"
            params = [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]

        elif filter_type =='monthly' and year and month:  # Monthly
            filter_sql += " AND EXTRACT(YEAR FROM date_wb) = %s AND EXTRACT(MONTH FROM date_wb) = %s" \
                if db_vendor == 'postgresql' else " AND YEAR(date_wb) = %s AND MONTH(date_wb) = %s"
            params = [year, month]

        elif filter_type =='yearly' and year:  # Yearly
            filter_sql += " AND EXTRACT(YEAR FROM date_wb) = %s" \
                if db_vendor == 'postgresql' else " AND YEAR(date_wb) = %s"
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


