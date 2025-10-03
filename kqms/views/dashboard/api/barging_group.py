# views.py
import logging
from django.http import JsonResponse
from django.db import connections, DatabaseError
import calendar
from datetime import datetime, timedelta
logger = logging.getLogger(__name__)
from ....utils.db_utils import get_db_vendor

# Memanggil fungsi utility
db_vendor = get_db_vendor('kqms_db')

def to_float1(v):
    return round(float(v or 0), 1)

# Card Summary
def build_summary_query_group(db_vendor: str, where_clause: str) -> str:
    if db_vendor == 'postgresql':
        return f"""
            SELECT 
                COALESCE(ROUND(SUM(CASE WHEN material IN ('LIM', 'SAP') THEN tonnage ELSE 0 END)::numeric, 2), 0) AS total,
                COALESCE(ROUND(SUM(CASE WHEN material = 'LIM' THEN tonnage ELSE 0 END)::numeric, 2), 0) AS total_lim,
                COALESCE(ROUND(SUM(CASE WHEN material = 'SAP' THEN tonnage ELSE 0 END)::numeric, 2), 0) AS total_sap
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

def get_barging_summary_group(request):
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

        query = build_summary_query_group(db_vendor, where_clause)

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
def get_chart_barging_group(request):
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
                                EXTRACT(HOUR FROM s.time_hauling)::int AS hour_label,
                                SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END) AS actual_lim,
                                SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END) AS actual_sap,
                                SUM(s.tonnage) AS actual_total
                            FROM ore_sellings_barging s
                            LEFT JOIN materials m ON m.id = s.id_material
                            WHERE s.date_hauling::date = %s::date
                            AND s.status_barging = 'Complete'
                            GROUP BY EXTRACT(HOUR FROM s.time_hauling)
                        ),
                        plan_total AS (
                            SELECT
                                SUM(CASE WHEN type_ore = 'LIM' THEN tonnage_plan ELSE 0 END) AS total_lim,
                                SUM(CASE WHEN type_ore = 'SAP' THEN tonnage_plan ELSE 0 END) AS total_sap
                            FROM ore_sellings_plan_barging
                            WHERE plan_date = %s::date
                        ),
                        plan AS (
                            SELECT
                                wh.hour_label,
                                ROUND((COALESCE(pt.total_lim, 0) / 24.0)::numeric, 2) AS plan_lim,
                                ROUND((COALESCE(pt.total_sap, 0) / 24.0)::numeric, 2) AS plan_sap
                            FROM working_hours wh
                            CROSS JOIN plan_total pt
                        ),
                        detail AS (
                            SELECT
                                EXTRACT(HOUR FROM s.time_hauling)::int AS hour_label,
                                mb.barge_code,
                                ROUND(SUM(s.tonnage)::numeric, 2) AS total,
                                ROUND(SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END)::numeric, 2) AS lim,
                                ROUND(SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END)::numeric, 2) AS sap
                            FROM ore_sellings_barging s
                            LEFT JOIN master_barge mb ON mb.id = s.barge_code
                            LEFT JOIN materials m ON m.id = s.id_material
                            WHERE s.date_hauling::date = %s::date
                            AND s.status_barging = 'Complete'
                            GROUP BY EXTRACT(HOUR FROM s.time_hauling), mb.barge_code
                        )
                        SELECT
                            wh.hour_label AS label,
                            ROUND(COALESCE(a.actual_total, 0), 2) AS actual_total,
                            ROUND(COALESCE(a.actual_lim, 0), 2) AS actual_lim,
                            ROUND(COALESCE(a.actual_sap, 0), 2) AS actual_sap,
                            ROUND(COALESCE(p.plan_lim, 0) + COALESCE(p.plan_sap, 0), 2) AS plan_total,
                            ROUND(COALESCE(p.plan_lim, 0), 2)   AS plan_lim,
                            ROUND(COALESCE(p.plan_sap, 0), 2)   AS plan_sap,
                            COALESCE(
                                json_agg(
                                    json_build_object(
                                        'barge_code', d.barge_code,
                                        'total', ROUND(d.total, 2),
                                        'lim',   ROUND(d.lim, 2),
                                        'sap',   ROUND(d.sap, 2)
                                    )
                                    ORDER BY d.barge_code
                                ) FILTER (WHERE d.barge_code IS NOT NULL),
                                '[]'
                            ) AS summary_by_barge
                        FROM working_hours wh
                        LEFT JOIN actual a ON a.hour_label = wh.hour_label
                        LEFT JOIN plan   p ON p.hour_label = wh.hour_label
                        LEFT JOIN detail d ON d.hour_label = wh.hour_label
                        GROUP BY wh.hour_label, wh.sort_order, a.actual_total, a.actual_lim, a.actual_sap, p.plan_lim, p.plan_sap
                        ORDER BY wh.sort_order;
                    """ 
            else:
                raise ValueError("Unsupported vendor")

            params = [filter_date, filter_date, filter_date]

        elif filter_type =='range' and date_start and date_end:

            if db_vendor == 'postgresql':
                query = """
                  WITH tanggal AS (
                        SELECT generate_series(%s::date, %s::date, interval '1 day') AS date
                    ),
                    actual AS (
                        SELECT
                            s.date_hauling::date AS date,
                            ROUND(SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END)::numeric, 2) AS lim,
                            ROUND(SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END)::numeric, 2) AS sap,
                            ROUND(SUM(s.tonnage)::numeric, 2) AS total
                        FROM ore_sellings_barging s
                        LEFT JOIN materials m ON m.id = s.id_material
                        WHERE s.date_hauling BETWEEN %s AND %s
                        AND s.status_barging = 'Complete'
                        GROUP BY s.date_hauling::date
                    ),
                    plan AS (
                        SELECT
                            p.plan_date::date AS date,
                            ROUND(SUM(CASE WHEN p.type_ore = 'LIM' THEN p.tonnage_plan ELSE 0 END)::numeric, 2) AS lim_plan,
                            ROUND(SUM(CASE WHEN p.type_ore = 'SAP' THEN p.tonnage_plan ELSE 0 END)::numeric, 2) AS sap_plan,
                            ROUND(SUM(p.tonnage_plan)::numeric, 2) AS total_plan
                        FROM ore_sellings_plan p
                        WHERE p.plan_date BETWEEN %s AND %s
                        GROUP BY p.plan_date::date
                    ),
                    detail AS (
                        SELECT
                            s.date_hauling::date AS date,
                            mb.barge_code,
                            ROUND(SUM(s.tonnage)::numeric, 2) AS total,
                            ROUND(SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END)::numeric, 2) AS lim,
                            ROUND(SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END)::numeric, 2) AS sap
                        FROM ore_sellings_barging s
                        LEFT JOIN master_barge mb ON mb.id = s.barge_code
                        LEFT JOIN materials m ON m.id = s.id_material
                        WHERE s.date_hauling BETWEEN %s AND %s
                        AND s.status_barging = 'Complete'
                        GROUP BY s.date_hauling::date, mb.barge_code
                    )
                    SELECT
                        TO_CHAR(tanggal.date, 'YYYY-MM-DD') AS label,
                        ROUND(COALESCE(a.total, 0), 2)       AS actual_total,
                        ROUND(COALESCE(a.lim, 0), 2)         AS actual_lim,
                        ROUND(COALESCE(a.sap, 0), 2)         AS actual_sap,
                        ROUND(COALESCE(p.total_plan, 0), 2)  AS plan_total,
                        ROUND(COALESCE(p.lim_plan, 0), 2)    AS plan_lim,
                        ROUND(COALESCE(p.sap_plan, 0), 2)    AS plan_sap,
                        COALESCE(
                            json_agg(
                                json_build_object(
                                    'barge_code', d.barge_code,
                                    'total', ROUND(d.total, 2),
                                    'lim',   ROUND(d.lim, 2),
                                    'sap',   ROUND(d.sap, 2)
                                )
                                ORDER BY d.barge_code
                            ) FILTER (WHERE d.barge_code IS NOT NULL),
                            '[]'
                        ) AS summary_by_barge
                    FROM tanggal
                    LEFT JOIN actual a ON tanggal.date = a.date
                    LEFT JOIN plan p   ON tanggal.date = p.date
                    LEFT JOIN detail d ON tanggal.date = d.date
                    GROUP BY tanggal.date, a.total, a.lim, a.sap, p.total_plan, p.lim_plan, p.sap_plan
                    ORDER BY tanggal.date;

                """
            else:
                raise ValueError("Unsupported vendor")
            
            params = [date_start, date_end,date_start, date_end,date_start, date_end,date_start, date_end]

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
                            s.date_hauling::date AS date,
                            SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END) AS lim,
                            SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END) AS sap,
                            SUM(s.tonnage) AS total
                        FROM ore_sellings_barging s
                        LEFT JOIN materials m ON m.id = s.id_material
                        WHERE s.date_hauling BETWEEN %s AND %s
                        GROUP BY s.date_hauling::date
                    ),
                    plan AS (
                        SELECT
                            p.plan_date::date AS date,
                            SUM(CASE WHEN p.type_ore = 'LIM' THEN p.tonnage_plan ELSE 0 END) AS lim_plan,
                            SUM(CASE WHEN p.type_ore = 'SAP' THEN p.tonnage_plan ELSE 0 END) AS sap_plan,
                            SUM(p.tonnage_plan) AS total_plan
                        FROM ore_sellings_plan p
                        WHERE p.plan_date BETWEEN %s AND %s
                        GROUP BY p.plan_date::date
                    ),
                    combine AS (
                        SELECT
                            t.date,
                            TO_CHAR(t.date, 'FMDay') AS day_name,
                            COALESCE(a.lim, 0) AS lim,
                            COALESCE(a.sap, 0) AS sap,
                            COALESCE(a.total, 0) AS total,
                            COALESCE(p.lim_plan, 0) AS lim_plan,
                            COALESCE(p.sap_plan, 0) AS sap_plan,
                            COALESCE(p.total_plan, 0) AS total_plan
                        FROM tanggal t
                        LEFT JOIN actual a ON t.date = a.date
                        LEFT JOIN plan p   ON t.date = p.date
                    ),
                    detail AS (
                        SELECT
                            s.date_hauling::date AS date,
                            TO_CHAR(s.date_hauling, 'FMDay') AS day_name,
                            mb.barge_code,
                            SUM(s.tonnage) AS total,
                            SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END) AS lim,
                            SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END) AS sap
                        FROM ore_sellings_barging s
                        LEFT JOIN master_barge mb ON mb.id = s.barge_code
                        LEFT JOIN materials m ON m.id = s.id_material
                        WHERE s.date_hauling BETWEEN %s AND %s
                        --AND s.status_barging = 'Complete'
                        GROUP BY s.date_hauling::date, mb.barge_code
                    )
                    SELECT
                        c.day_name AS label,
                        ROUND(SUM(c.total), 2)       AS actual_total,
                        ROUND(SUM(c.lim), 2)         AS actual_lim,
                        ROUND(SUM(c.sap), 2)         AS actual_sap,
                        ROUND(SUM(c.total_plan), 2)  AS plan_total,
                        ROUND(SUM(c.lim_plan), 2)    AS plan_lim,
                        ROUND(SUM(c.sap_plan), 2)    AS plan_sap,
                        COALESCE(
                            json_agg(
                                json_build_object(
                                    'barge_code', d.barge_code,
                                    'total', ROUND(SUM(d.total), 2),
                                    'lim',   ROUND(SUM(d.lim), 2),
                                    'sap',   ROUND(SUM(d.sap), 2)
                                )
                                ORDER BY d.barge_code
                            ) FILTER (WHERE d.barge_code IS NOT NULL),
                            '[]'
                        ) AS summary_by_barge
                    FROM combine c
                    LEFT JOIN detail d ON c.date = d.date
                    GROUP BY c.day_name
                    ORDER BY ARRAY_POSITION(
                        ARRAY['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'],
                        c.day_name
                    );

                """
            else:
                raise ValueError("Unsupported vendor")
        
            params = [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'),
                      start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'),
                      start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'),
                      start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'),
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
            params = [tgl_pertama, tgl_terakhir,
                       tgl_pertama, tgl_terakhir,
                       tgl_pertama, tgl_terakhir
                       ]
            if db_vendor == 'postgresql':
                query = """
                   WITH tanggal AS (
                        SELECT generate_series(%s::date, %s::date, interval '1 day') AS date
                    ),
                    detail AS (
                        SELECT
                            s.date_hauling::date AS date,
                            mb.barge_code,
                            ROUND(SUM(s.tonnage)::numeric, 2) AS total,
                            ROUND(SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END)::numeric, 2) AS lim,
                            ROUND(SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END)::numeric, 2) AS sap
                        FROM ore_sellings_barging s
                        LEFT JOIN master_barge mb ON mb.id = s.barge_code
                        LEFT JOIN materials m ON m.id = s.id_material
                        WHERE s.date_hauling BETWEEN %s AND %s
                        AND s.status_barging = 'Complete'
                        GROUP BY s.date_hauling::date, mb.barge_code
                    ),
                    plan AS (
                        SELECT
                            p.plan_date::date AS date,
                            ROUND(SUM(p.tonnage_plan)::numeric, 2) AS total_plan,
                            ROUND(SUM(CASE WHEN p.type_ore = 'LIM' THEN p.tonnage_plan ELSE 0 END)::numeric, 2) AS lim_plan,
                            ROUND(SUM(CASE WHEN p.type_ore = 'SAP' THEN p.tonnage_plan ELSE 0 END)::numeric, 2) AS sap_plan
                        FROM ore_sellings_plan_barging p
                        WHERE p.plan_date BETWEEN %s AND %s
                        GROUP BY p.plan_date::date
                    )
                    SELECT
                        TO_CHAR(t.date, 'DD') AS label,
                        ROUND(COALESCE(SUM(d.total), 0), 2)  AS actual_total,
                        ROUND(COALESCE(SUM(d.lim), 0), 2)    AS actual_lim,
                        ROUND(COALESCE(SUM(d.sap), 0), 2)    AS actual_sap,
                        ROUND(COALESCE(p.total_plan, 0), 2)  AS plan_total,
                        ROUND(COALESCE(p.lim_plan, 0), 2)    AS plan_lim,
                        ROUND(COALESCE(p.sap_plan, 0), 2)    AS plan_sap,
                        COALESCE(
                            json_agg(
                                json_build_object(
                                    'barge_code', d.barge_code,
                                    'total', ROUND(d.total, 2),
                                    'lim',   ROUND(d.lim, 2),
                                    'sap',   ROUND(d.sap, 2)
                                )
                                ORDER BY d.barge_code
                            ) FILTER (WHERE d.barge_code IS NOT NULL),
                            '[]'
                        ) AS summary_by_barge
                    FROM tanggal t
                    LEFT JOIN detail d ON t.date = d.date
                    LEFT JOIN plan p   ON t.date = p.date
                    GROUP BY t.date, p.total_plan, p.lim_plan, p.sap_plan
                    ORDER BY t.date;
                """
            else:
                raise ValueError("Unsupported vendor")
       
        elif filter_type =='yearly' and year: 
            if db_vendor == 'postgresql':
                query = """
                   WITH bulan AS (
                        SELECT generate_series(1, 12) AS month
                    ),
                    detail AS (
                        SELECT
                            EXTRACT(MONTH FROM s.date_hauling)::int AS month,
                            mb.barge_code,
                            ROUND(SUM(s.tonnage)::numeric, 2) AS total,
                            ROUND(SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END)::numeric, 2) AS lim,
                            ROUND(SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END)::numeric, 2) AS sap
                        FROM ore_sellings_barging s
                        LEFT JOIN master_barge mb ON mb.id = s.barge_code
                        LEFT JOIN materials m ON m.id = s.id_material
                        WHERE EXTRACT(YEAR FROM s.date_hauling) = %s
                        GROUP BY EXTRACT(MONTH FROM s.date_hauling), mb.barge_code
                    ),
                    plan AS (
                        SELECT
                            EXTRACT(MONTH FROM p.plan_date)::int AS month,
                            ROUND(SUM(p.tonnage_plan)::numeric, 2) AS total_plan,
                            ROUND(SUM(CASE WHEN p.type_ore = 'LIM' THEN p.tonnage_plan ELSE 0 END)::numeric, 2) AS lim_plan,
                            ROUND(SUM(CASE WHEN p.type_ore = 'SAP' THEN p.tonnage_plan ELSE 0 END)::numeric, 2) AS sap_plan
                        FROM ore_sellings_plan_barging p
                        WHERE EXTRACT(YEAR FROM p.plan_date) = %s
                        GROUP BY EXTRACT(MONTH FROM p.plan_date)
                    )
                    SELECT
                        TO_CHAR(TO_DATE(bulan.month::text, 'MM'), 'Mon') AS label,
                        ROUND(COALESCE(SUM(d.total), 0), 2) AS actual_total,
                        ROUND(COALESCE(SUM(d.lim), 0), 2)   AS actual_lim,
                        ROUND(COALESCE(SUM(d.sap), 0), 2)   AS actual_sap,
                        ROUND(COALESCE(p.total_plan, 0), 2) AS plan_total,
                        ROUND(COALESCE(p.lim_plan, 0), 2)   AS plan_lim,
                        ROUND(COALESCE(p.sap_plan, 0), 2)   AS plan_sap,
                        COALESCE(
                            json_agg(
                                json_build_object(
                                    'barge_code', d.barge_code,
                                    'total', ROUND(d.total, 2),
                                    'lim',   ROUND(d.lim, 2),
                                    'sap',   ROUND(d.sap, 2)
                                )
                                ORDER BY d.barge_code
                            ) FILTER (WHERE d.barge_code IS NOT NULL),
                            '[]'
                        ) AS summary_by_barge
                    FROM bulan
                    LEFT JOIN detail d ON bulan.month = d.month
                    LEFT JOIN plan   p ON bulan.month = p.month
                    GROUP BY bulan.month, p.total_plan, p.lim_plan, p.sap_plan
                    ORDER BY bulan.month;
                """
            else:
                raise ValueError("Unsupported vendor")
            params = [year,year]

        elif filter_type =='all':
            if db_vendor == 'postgresql':
                query = """
                   WITH tahun AS (
                        SELECT DISTINCT EXTRACT(YEAR FROM date_hauling)::int AS year
                        FROM ore_sellings_barging
                        UNION
                        SELECT DISTINCT EXTRACT(YEAR FROM plan_date)::int AS year
                        FROM ore_sellings_plan
                    ),
                    actual AS (
                        SELECT
                            EXTRACT(YEAR FROM s.date_hauling)::int AS year,
                            mb.barge_code,
                            ROUND(SUM(s.tonnage)::numeric, 2) AS total,
                            ROUND(SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END)::numeric, 2) AS lim,
                            ROUND(SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END)::numeric, 2) AS sap
                        FROM ore_sellings_barging s
                        LEFT JOIN master_barge mb ON mb.id = s.barge_code
                        LEFT JOIN materials m ON m.id = s.id_material
                        GROUP BY EXTRACT(YEAR FROM s.date_hauling), mb.barge_code
                    ),
                    plan AS (
                        SELECT
                            EXTRACT(YEAR FROM p.plan_date)::int AS year,
                            ROUND(SUM(p.tonnage_plan)::numeric, 2) AS total_plan,
                            ROUND(SUM(CASE WHEN p.type_ore = 'LIM' THEN p.tonnage_plan ELSE 0 END)::numeric, 2) AS lim_plan,
                            ROUND(SUM(CASE WHEN p.type_ore = 'SAP' THEN p.tonnage_plan ELSE 0 END)::numeric, 2) AS sap_plan
                        FROM ore_sellings_plan p
                        GROUP BY EXTRACT(YEAR FROM p.plan_date)
                    )
                    SELECT
                        t.year::text AS label,
                        ROUND(COALESCE(SUM(a.total), 0), 2) AS actual_total,
                        ROUND(COALESCE(SUM(a.lim), 0), 2)   AS actual_lim,
                        ROUND(COALESCE(SUM(a.sap), 0), 2)   AS actual_sap,
                        ROUND(COALESCE(p.total_plan, 0), 2) AS plan_total,
                        ROUND(COALESCE(p.lim_plan, 0), 2)   AS plan_lim,
                        ROUND(COALESCE(p.sap_plan, 0), 2)   AS plan_sap,
                    '[]'::json AS summary_by_barge   -- << alias kosong biar frontend tetap aman
                    FROM tahun t
                    LEFT JOIN actual a ON t.year = a.year
                    LEFT JOIN plan p  ON t.year = p.year
                    GROUP BY t.year, p.total_plan, p.lim_plan, p.sap_plan
                    ORDER BY t.year;
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

        details = []

        for row in results:
            print(f"ROW: {row} ({len(row)} fields)")

            label        = str(row[0])
            total_actual = float(row[1] or 0)
            lim_value    = float(row[2] or 0)
            sap_value    = float(row[3] or 0)
            total_plan   = float(row[4] or 0)
            lim_target   = float(row[5] or 0)
            sap_target   = float(row[6] or 0)
            barges       = row[7] if row[7] else []   # << ini ambil JSON dari query

            details.append({
                'label'        : label,
                'total_actual' : round(total_actual, 2),
                'lim_actual'   : round(lim_value, 2),
                'sap_actual'   : round(sap_value, 2),
                'total_plan'   : round(total_plan, 2),
                'lim_plan'     : round(lim_target, 2),
                'sap_plan'     : round(sap_target, 2),
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
