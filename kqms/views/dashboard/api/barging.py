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

def get_barging_summary(request):
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
            where_clause += " AND date_hauling = %s"
            params += [filter_date]
        elif filter_type =='range' and date_start and date_end:
            where_clause += " AND date_hauling BETWEEN %s AND %s"
            params += [date_start, date_end]
        elif filter_type =='weekly' and week:
            # Contoh week: '2025-26'
            where_clause += " AND TO_CHAR(date_hauling, 'IYYY-IW') = %s" \
                if db_vendor == 'postgresql' else \
                " AND DATE_FORMAT(date_hauling, '%%x-%%v') = %s"
            params += [week]
        elif filter_type =='monthly' and year and month:
            where_clause += " AND EXTRACT(YEAR FROM date_hauling) = %s AND EXTRACT(MONTH FROM date_hauling) = %s" \
                if db_vendor == 'postgresql' else \
                " AND YEAR(date_hauling) = %s AND MONTH(date_hauling) = %s"
            params += [year, month]
        elif filter_type =='yearly' and year:
            where_clause += " AND EXTRACT(YEAR FROM date_hauling) = %s" \
                if db_vendor == 'postgresql' else \
                " AND YEAR(date_hauling) = %s"
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

# Create Chart Barging
def get_chart_barging(request):
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
                                CASE
                                    WHEN hour_label >= 7 THEN hour_label
                                    ELSE hour_label + 24
                                END AS sort_order
                            FROM generate_series(0, 23) AS hour_label
                        ),
                        actual AS (
                            SELECT
                                EXTRACT(HOUR FROM time_hauling) AS hour_label,
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN os.tonnage ELSE 0 END) AS actual_lim,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN os.tonnage ELSE 0 END) AS actual_sap
                            FROM ore_sellings_barging os
                            LEFT JOIN materials m ON m.id = os.id_material
                            WHERE DATE(date_hauling) = %s::date
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
                            COALESCE(a.actual_lim, 0) + COALESCE(a.actual_sap, 0) AS actual_total,
                            COALESCE(a.actual_lim, 0) AS actual_lim,
                            COALESCE(a.actual_sap, 0) AS actual_sap,
                            COALESCE(p.plan_lim, 0) + COALESCE(p.plan_sap, 0) AS plan_total,
                            COALESCE(p.plan_lim, 0) AS plan_lim,
                            COALESCE(p.plan_sap, 0) AS plan_sap
                        FROM working_hours wh
                        LEFT JOIN actual a ON a.hour_label = wh.hour_label
                        LEFT JOIN plan p ON p.hour_label = wh.hour_label
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
                    actual AS (
                        SELECT
                            date_hauling::date AS date,
                            SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END) AS lim,
                            SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END) AS sap
                        FROM ore_sellings_barging s
                        LEFT JOIN materials m ON m.id = s.id_material
                        WHERE date_hauling BETWEEN %s AND %s
                        GROUP BY date_hauling::date
                    ),
                    plan AS (
                        SELECT
                            plan_date::date AS date,
                            SUM(CASE WHEN type_ore = 'LIM' THEN tonnage_plan ELSE 0 END) AS lim_plan,
                            SUM(CASE WHEN type_ore = 'SAP' THEN tonnage_plan ELSE 0 END) AS sap_plan
                        FROM ore_sellings_plan
                        WHERE plan_date BETWEEN %s AND %s
                        GROUP BY plan_date::date
                    )
                    SELECT
                            TO_CHAR(tanggal.date, 'YYYY-MM-DD') AS label,
                            COALESCE(a.lim, 0) + COALESCE(a.sap, 0) AS actual_total,
                            COALESCE(a.lim, 0) AS actual_lim,
                            COALESCE(a.sap, 0) AS actual_sap,
                            COALESCE(p.lim_plan, 0) + COALESCE(p.sap_plan, 0) AS plan_total,
                            COALESCE(p.lim_plan, 0) AS plan_lim,
                            COALESCE(p.sap_plan, 0) AS plan_sap
                    FROM tanggal
                    LEFT JOIN actual a ON tanggal.date = a.date
                    LEFT JOIN plan p ON tanggal.date = p.date
                    ORDER BY tanggal.date;
                """
            else:
                raise ValueError("Unsupported vendor")
            
            params = [date_start, date_end,date_start, date_end,date_start, date_end]

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
                    actual AS (
                        SELECT
                            date_hauling::date AS date,
                            SUM(CASE WHEN m.nama_material = 'LIM' THEN tonnage ELSE 0 END) AS lim,
                            SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END) AS sap
                        FROM ore_sellings_barging s
                        LEFT JOIN materials m ON m.id = s.id_material
                        WHERE date_hauling BETWEEN %s AND %s
                        GROUP BY date_hauling
                    ),
                    plan AS (
                        SELECT
                            plan_date::date AS date,
                            SUM(CASE WHEN type_ore = 'LIM' THEN tonnage_plan ELSE 0 END) AS lim_plan,
                            SUM(CASE WHEN type_ore = 'SAP' THEN tonnage_plan ELSE 0 END) AS sap_plan
                        FROM ore_sellings_plan
                        WHERE plan_date BETWEEN %s AND %s
                        GROUP BY plan_date
                    ),
                    combine AS (
                        SELECT
                            tanggal.date,
                            TO_CHAR(tanggal.date, 'FMDay') AS day_name,
                            COALESCE(a.lim, 0) AS lim,
                            COALESCE(a.sap, 0) AS sap,
                            COALESCE(p.lim_plan, 0) AS lim_plan,
                            COALESCE(p.sap_plan, 0) AS sap_plan
                        FROM tanggal
                        LEFT JOIN actual a ON tanggal.date = a.date
                        LEFT JOIN plan p ON tanggal.date = p.date
                    )
                    SELECT
                        day_name AS label,
                        SUM(lim + sap) AS actual_total,
                        SUM(lim) AS actual_lim,
                        SUM(sap) AS actual_sap,
                        SUM(lim_plan + sap_plan) AS plan_total,
                        SUM(lim_plan) AS plan_lim,
                        SUM(sap_plan) AS plan_sap
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
            params = [tgl_pertama, tgl_terakhir, tgl_pertama, tgl_terakhir,  tgl_pertama, tgl_terakhir]
            if db_vendor == 'postgresql':
                query = """
                   WITH tanggal AS (
                        SELECT generate_series(%s::date, %s::date, interval '1 day') AS date
                    ),
                    incoming AS (
                        SELECT
                            date_hauling::date AS date,
                            ROUND(SUM(tonnage)::numeric, 2) AS total,
                            ROUND(SUM(CASE WHEN material = 'LIM' THEN tonnage ELSE 0 END)::numeric, 2) AS lim,
                            ROUND(SUM(CASE WHEN material = 'SAP' THEN tonnage ELSE 0 END)::numeric, 2) AS sap
                        FROM details_selling_barging
                        WHERE date_hauling BETWEEN %s AND %s
                        GROUP BY date_hauling
                    ),
                    plan AS (
                        SELECT
                            plan_date::date AS date,
                            ROUND(SUM(CASE WHEN type_ore = 'LIM' THEN tonnage_plan ELSE 0 END)::numeric, 2) AS lim_plan,
                            ROUND(SUM(CASE WHEN type_ore = 'SAP' THEN tonnage_plan ELSE 0 END)::numeric, 2) AS sap_plan,
                            ROUND(SUM(tonnage_plan)::numeric, 2) AS total_plan
                        FROM ore_sellings_plan
                        WHERE plan_date BETWEEN %s AND %s
                        GROUP BY plan_date
                    )
                    SELECT
                        TO_CHAR(tanggal.date, 'DD') AS label,
                        COALESCE(i.total, 0) AS total_actual,
                        COALESCE(i.lim, 0) AS lim_actual,
                        COALESCE(i.sap, 0) AS sap_actual,
                        COALESCE(p.total_plan, 0) AS total_plan,
                        COALESCE(p.lim_plan, 0) AS lim_plan,
                        COALESCE(p.sap_plan, 0) AS sap_plan
                    FROM tanggal
                    LEFT JOIN incoming i ON tanggal.date = i.date
                    LEFT JOIN plan p ON tanggal.date = p.date
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
                   incoming AS (
                        SELECT
                            EXTRACT(MONTH FROM date_hauling)::int AS month,
                    		ROUND(SUM(tonnage)::numeric, 2) AS total,
                            ROUND(SUM(CASE WHEN nama_material = 'LIM' THEN tonnage ELSE 0 END)::numeric, 2) AS lim,
                            ROUND(SUM(CASE WHEN nama_material = 'SAP' THEN tonnage ELSE 0 END)::numeric, 2) AS sap
                        FROM ore_sellings_barging s
                        LEFT JOIN materials m ON m.id = s.id_material
                        WHERE EXTRACT(YEAR FROM date_hauling) = %s
                      GROUP BY EXTRACT(MONTH FROM date_hauling)
                     ),
                  plan AS (
                      SELECT
                          EXTRACT(MONTH FROM plan_date)::int AS month,
                          ROUND(SUM(tonnage_plan)::numeric, 2) AS total_plan,
                          ROUND(SUM(CASE WHEN type_ore = 'LIM' THEN tonnage_plan ELSE 0 END)::numeric, 2) AS lim_plan,
                          ROUND(SUM(CASE WHEN type_ore = 'SAP' THEN tonnage_plan ELSE 0 END)::numeric, 2) AS sap_plan
                      FROM ore_sellings_plan
                      WHERE EXTRACT(YEAR FROM plan_date) = %s
                      GROUP BY EXTRACT(MONTH FROM plan_date)
                  )
                  SELECT
                      TO_CHAR(TO_DATE(bulan.month::text, 'MM'), 'Mon') AS label,
                      COALESCE(i.total, 0) AS total_actual,
                      COALESCE(i.lim, 0) AS lim_actual,
                      COALESCE(i.sap, 0) AS sap_actual,
                      COALESCE(p.total_plan, 0) AS total_plan,
                      COALESCE(p.lim_plan, 0) AS lim_plan,
                      COALESCE(p.sap_plan, 0) AS sap_plan
                  FROM bulan
                  LEFT JOIN incoming i ON bulan.month = i.month
                  LEFT JOIN plan p ON bulan.month = p.month
                  ORDER BY bulan.month;
                """
            else:
                raise ValueError("Unsupported vendor")
            params = [year,year]

        elif filter_type =='all':
            if db_vendor == 'postgresql':
                query = """
                    SELECT 
                        COALESCE(actual.year_label, plan.year_label) AS label,
                        COALESCE(actual.lim, 0) + COALESCE(actual.sap, 0) AS actual_total,
                        COALESCE(actual.lim, 0) AS actual_lim,
                        COALESCE(actual.sap, 0) AS actual_sap,
                        COALESCE(plan.lim_plan, 0) + COALESCE(plan.sap_plan, 0) AS plan_total,
                        COALESCE(plan.lim_plan, 0) AS plan_lim,
                        COALESCE(plan.sap_plan, 0) AS plan_sap
                    FROM (
                        SELECT 
                            TO_CHAR(date_hauling, 'YYYY') AS year_label,
                            SUM(CASE WHEN m.nama_material = 'LIM' THEN tonnage ELSE 0 END) AS lim,
                            SUM(CASE WHEN m.nama_material = 'SAP' THEN tonnage ELSE 0 END) AS sap
                        FROM ore_sellings_barging os
                        LEFT JOIN materials m ON m.id = os.id_material
                        GROUP BY TO_CHAR(date_hauling, 'YYYY')
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
                    ORDER BY label;
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

        x_labels     = []
        actual_total = []
        lim_actual   = []
        sap_actual   = []
        plan_total   = []
        lim_plan     = []
        sap_plan     = []


        for row in results:
            print(f"ROW: {row} ({len(row)} fields)")
  
            label        = str(row[0])
            total_actual = float(row[1] or 0)
            lim_value    = float(row[2] or 0)
            sap_value    = float(row[3] or 0)
            total_plan   = float(row[4] or 0)
            lim_target   = float(row[5] or 0)
            sap_target   = float(row[6] or 0)

            x_labels.append(label)
            actual_total.append(total_actual)
            lim_actual.append(lim_value)
            sap_actual.append(sap_value)
            plan_total.append(total_plan)
            lim_plan.append(lim_target)
            sap_plan.append(sap_target)

        return JsonResponse({
            'x_data'        : x_labels,
            'y_data_actual' : actual_total,
            'y_lim_actual'  : lim_actual,
            'y_sap_actual'  : sap_actual,
            'y_data_plan'   : plan_total,
            'y_lim_plan'    : lim_plan,
            'y_sap_plan'    : sap_plan,
        })

    except DatabaseError:
        logger.exception("DB Error in chart selling")
        return JsonResponse({'error': 'Database error'}, status=500)
    except Exception as e:
        logger.exception("Unexpected error in chart selling")
        return JsonResponse({'error': str(e)}, status=500)
