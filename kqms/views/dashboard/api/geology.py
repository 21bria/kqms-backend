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

def get_month_label(month_number):
    month_labels = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr',
        5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug',
        9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }
    return month_labels.get(month_number, '')

# Card Summary
def build_summary_query(db_vendor: str, where_clause: str) -> str:
    if db_vendor == 'postgresql':
        return f"""
            SELECT 
                --COALESCE(ROUND(SUM(CASE WHEN stockpile != 'Temp-Rompile_KM09' THEN tonnage ELSE 0 END)::numeric, 2), 0) AS total,
                COALESCE(ROUND(SUM(CASE WHEN nama_material IN ('LIM', 'SAP') THEN tonnage ELSE 0 END)::numeric, 2), 0) AS total,
                COALESCE(ROUND(SUM(CASE WHEN nama_material = 'LIM' THEN tonnage ELSE 0 END)::numeric, 2), 0) AS total_lim,
                COALESCE(ROUND(SUM(CASE WHEN nama_material = 'SAP' THEN tonnage ELSE 0 END)::numeric, 2), 0) AS total_sap
            FROM ore_production
            {where_clause}
        """
    elif db_vendor in ['mysql', 'mssql', 'microsoft']:
        return f"""
            SELECT
                --COALESCE(ROUND(SUM(CASE WHEN stockpile != 'Temp-Rompile_KM09' THEN tonnage ELSE 0 END), 2), 0) AS total,
                COALESCE(ROUND(SUM(CASE WHEN nama_material IN ('LIM', 'SAP') THEN tonnage ELSE 0 END), 2), 0) AS total,
                COALESCE(ROUND(SUM(CASE WHEN nama_material = 'LIM' THEN tonnage ELSE 0 END), 2), 0) AS total_lim,
                COALESCE(ROUND(SUM(CASE WHEN nama_material = 'SAP' THEN tonnage ELSE 0 END), 2), 0) AS total_sap
            FROM ore_production
            {where_clause}
        """
    else:
        raise ValueError("Unsupported vendor")

def get_ore_summary(request):
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
            where_clause += " AND tgl_production = %s"
            params += [filter_date]
        elif filter_type =='range' and date_start and date_end:
            where_clause += " AND tgl_production BETWEEN %s AND %s"
            params += [date_start, date_end]
        elif filter_type =='weekly' and week:
            # Contoh week: '2025-26'
            where_clause += " AND TO_CHAR(tgl_production, 'IYYY-IW') = %s" \
                if db_vendor == 'postgresql' else \
                " AND DATE_FORMAT(tgl_production, '%%x-%%v') = %s"
            params += [week]
        elif filter_type =='monthly' and year and month:
            where_clause += " AND EXTRACT(YEAR FROM tgl_production) = %s AND EXTRACT(MONTH FROM tgl_production) = %s" \
                if db_vendor == 'postgresql' else \
                " AND YEAR(tgl_production) = %s AND MONTH(tgl_production) = %s"
            params += [year, month]
        elif filter_type =='yearly' and year:
            where_clause += " AND EXTRACT(YEAR FROM tgl_production) = %s" \
                if db_vendor == 'postgresql' else \
                " AND YEAR(tgl_production) = %s"
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
def get_chart_ore(request):
    try:
        filter_type = request.GET.get('filter_type')
        year = request.GET.get('year')
        month = request.GET.get('month')
        week = request.GET.get('week')
        date_start = request.GET.get('date_start')
        date_end   = request.GET.get('date_end')

        x_labels = []
        data_lim = []
        data_sap = []

        if filter_type =='range' and date_start and date_end: 
            if db_vendor == 'postgresql':
                query = """
                    WITH tanggal AS (
                        SELECT generate_series(%s::date, %s::date, interval '1 day') AS date
                        ),
                        incoming AS (
                            SELECT
                                tgl_production::date AS date,
                                SUM(CASE WHEN nama_material = 'LIM' THEN tonnage ELSE 0 END) AS lim,
                                SUM(CASE WHEN nama_material = 'SAP' THEN tonnage ELSE 0 END) AS sap
                            FROM ore_production
                            WHERE tgl_production BETWEEN %s AND %s
                            GROUP BY tgl_production
                        )
                    SELECT
                            TO_CHAR(tanggal.date, 'YYYY-MM-DD') AS label,
                            COALESCE(i.lim, 0) AS lim,
                            COALESCE(i.sap, 0) AS sap
                        FROM tanggal
                        LEFT JOIN incoming i ON tanggal.date = i.date
                        ORDER BY tanggal.date
                """ 
            elif db_vendor in ['mssql', 'microsoft']:
                query = """
                WITH tanggal AS (
                        SELECT CAST(%s AS DATE) AS date
                        UNION ALL
                        SELECT DATEADD(DAY, 1, date)
                        FROM tanggal
                        WHERE DATEADD(DAY, 1, date) <= %s
                    ),
                    incoming AS (
                        SELECT
                            CAST(tgl_production AS DATE) AS date,
                            SUM(CASE WHEN nama_material = 'LIM' THEN tonnage ELSE 0 END) AS lim,
                            SUM(CASE WHEN nama_material = 'SAP' THEN tonnage ELSE 0 END) AS sap
                        FROM ore_production
                        WHERE tgl_production BETWEEN %s AND %s
                        GROUP BY CAST(tgl_production AS DATE)
                    )
                    SELECT 
                        CONVERT(VARCHAR(10), t.date, 120) AS label, -- format YYYY-MM-DD
                        ISNULL(i.lim, 0) AS lim,
                        ISNULL(i.sap, 0) AS sap
                    FROM tanggal t
                    LEFT JOIN incoming i ON t.date = i.date
                    ORDER BY t.date
                    OPTION (MAXRECURSION 1000);
                """ 
            else:
                    raise ValueError("Unsupported database vendor.")
            params = [date_start, date_end, date_start, date_end]

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
                        end_date   = datetime(next_month.year, next_month.month, 1) - timedelta(days=1)

            except Exception as e:
                return JsonResponse({"error": f"Format tahun/bulan/minggu tidak valid: {str(e)}"}, status=400)

            if db_vendor == 'postgresql':
                query = """
                    WITH tanggal AS (
                            SELECT generate_series(%s::date, %s::date, interval '1 day') AS date
                        ),
                        incoming AS (
                            SELECT
                                tgl_production::date AS date,
                                TRIM(TO_CHAR(tgl_production, 'Day')) AS day,
                                SUM(CASE WHEN nama_material = 'LIM' THEN tonnage ELSE 0 END) AS lim,
                                SUM(CASE WHEN nama_material = 'SAP' THEN tonnage ELSE 0 END) AS sap
                            FROM ore_production
                            WHERE tgl_production BETWEEN %s AND %s
                            GROUP BY tgl_production
                        ),
                        combine AS (
                            SELECT
                                tanggal.date,
                                TRIM(TO_CHAR(tanggal.date, 'Day')) AS day_name,
                                COALESCE(i.lim, 0) AS lim,
                                COALESCE(i.sap, 0) AS sap
                            FROM tanggal
                            LEFT JOIN incoming i ON tanggal.date = i.date
                        )
                        SELECT
                            day_name AS label,
                            SUM(lim) AS lim,
                            SUM(sap) AS sap
                        FROM combine
                        GROUP BY day_name
                        ORDER BY ARRAY_POSITION(
                            ARRAY['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'],
                            day_name
                            )
                """ 
                params = [
                            start_date.strftime('%Y-%m-%d'),
                            end_date.strftime('%Y-%m-%d'),
                            start_date.strftime('%Y-%m-%d'), 
                            end_date.strftime('%Y-%m-%d')
                          ]
            elif db_vendor in ['mssql', 'microsoft']:
                query = """
                        WITH hari (day_number, day_name) AS (
                        SELECT 1, 'Sunday' UNION ALL
                        SELECT 2, 'Monday' UNION ALL
                        SELECT 3, 'Tuesday' UNION ALL
                        SELECT 4, 'Wednesday' UNION ALL
                        SELECT 5, 'Thursday' UNION ALL
                        SELECT 6, 'Friday' UNION ALL
                        SELECT 7, 'Saturday'
                    ),
                    incoming AS (
                        SELECT 
                            DATENAME(WEEKDAY, tgl_production) AS day_name,
                            SUM(CASE WHEN nama_material = 'LIM' THEN tonnage ELSE 0 END) AS lim,
                            SUM(CASE WHEN nama_material = 'SAP' THEN tonnage ELSE 0 END) AS sap
                        FROM ore_production
                        WHERE tgl_production BETWEEN ? AND ?
                        GROUP BY DATENAME(WEEKDAY, tgl_production)
                    )
                    SELECT
                        h.day_name AS label,
                        ISNULL(i.lim, 0) AS lim,
                        ISNULL(i.sap, 0) AS sap
                    FROM hari h
                    LEFT JOIN incoming i ON h.day_name = i.day_name
                    ORDER BY h.day_number   
                """ 
                params = [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]
            else:
                raise ValueError("Unsupported database vendor.")
        elif filter_type =='monthly' and year and month: 
            year = int(year)
            month = int(month)
            # Ambil jumlah hari terakhir dalam bulan
            last_day = calendar.monthrange(year, month)[1]
            # Bangun tanggal awal dan akhir bulan
            tgl_pertama  = datetime(year, month, 1).date()
            tgl_terakhir = datetime(year, month, last_day).date()
            # Siapkan parameter untuk query
            params = [tgl_pertama, tgl_terakhir,tgl_pertama, tgl_terakhir]

            if db_vendor == 'postgresql':
                    query = """
                     WITH tanggal AS (
                            SELECT generate_series(%s::date, %s::date, interval '1 day') AS date
                        ),
                        incoming AS (
                            SELECT
                                tgl_production::date AS date,
                                SUM(CASE WHEN nama_material = 'LIM' THEN tonnage ELSE 0 END) AS lim,
                                SUM(CASE WHEN nama_material = 'SAP' THEN tonnage ELSE 0 END) AS sap
                            FROM ore_production
                            WHERE tgl_production BETWEEN %s AND %s
                            GROUP BY tgl_production
                        )
                        SELECT
                            TO_CHAR(tanggal.date, 'DD') AS label,
                            COALESCE(i.lim, 0) AS lim,
                            COALESCE(i.sap, 0) AS sap
                        FROM tanggal
                        LEFT JOIN incoming i ON tanggal.date = i.date
                        ORDER BY tanggal.date
                    """ 
            elif db_vendor in ['mssql', 'microsoft']:
                        query = """
                           WITH tanggal AS (
                                SELECT %s AS date
                                UNION ALL
                                SELECT DATEADD(DAY, 1, date)
                                FROM tanggal
                                WHERE DATEADD(DAY, 1, date) <= %s
                            ),
                            incoming AS (
                                SELECT
                                    CAST(tgl_production AS DATE) AS date,
                                    SUM(CASE WHEN nama_material = 'LIM' THEN tonnage ELSE 0 END) AS lim,
                                    SUM(CASE WHEN nama_material = 'SAP' THEN tonnage ELSE 0 END) AS sap
                                FROM ore_production
                                WHERE tgl_production BETWEEN %s AND %s
                                GROUP BY CAST(tgl_production AS DATE)
                            )
                            SELECT
                                FORMAT(tanggal.date, 'dd') AS label,
                                ISNULL(i.lim, 0) AS lim,
                                ISNULL(i.sap, 0) AS sap
                            FROM tanggal
                            LEFT JOIN incoming i ON tanggal.date = i.date
                            ORDER BY tanggal.date
                            OPTION (MAXRECURSION 1000);
                        """ 
            else:
                raise ValueError("Unsupported database vendor.")
        elif filter_type =='yearly' and year: 
            if db_vendor == 'postgresql':
                query = """
                    WITH bulan AS (
                        SELECT generate_series(1, 12) AS month
                    ),
                    incoming AS (
                        SELECT
                            EXTRACT(MONTH FROM tgl_production)::int AS month,
                            SUM(CASE WHEN nama_material = 'LIM' THEN tonnage ELSE 0 END) AS lim,
                            SUM(CASE WHEN nama_material = 'SAP' THEN tonnage ELSE 0 END) AS sap
                        FROM ore_production
                        WHERE EXTRACT(YEAR FROM tgl_production) = %s
                        GROUP BY EXTRACT(MONTH FROM tgl_production)
                    )
                    SELECT
                        TO_CHAR(TO_DATE(bulan.month::text, 'MM'), 'Mon ') AS label,
                        COALESCE(i.lim, 0) AS lim,
                        COALESCE(i.sap, 0) AS sap
                    FROM bulan
                    LEFT JOIN incoming i ON bulan.month = i.month
                    ORDER BY bulan.month
                """ 
                params = [year]
            elif db_vendor in ['mssql', 'microsoft']:
                    query = """
                        WITH bulan (month) AS (
                            SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6
                            UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9 UNION ALL SELECT 10 UNION ALL SELECT 11 UNION ALL SELECT 12
                        ),
                        incoming AS (
                            SELECT
                                MONTH(tgl_production) AS month,
                                SUM(CASE WHEN nama_material = 'LIM' THEN tonnage ELSE 0 END) AS lim,
                                SUM(CASE WHEN nama_material = 'SAP' THEN tonnage ELSE 0 END) AS sap
                            FROM ore_production
                            WHERE YEAR(tgl_production) = %s
                            GROUP BY MONTH(tgl_production)
                        )
                        SELECT
                            FORMAT(DATEFROMPARTS(%s, bulan.month, 1), 'MMM') AS label,
                            ISNULL(i.lim, 0) AS lim,
                            ISNULL(i.sap, 0) AS sap
                        FROM bulan
                        LEFT JOIN incoming i ON bulan.month = i.month
                        ORDER BY bulan.month
                    """ 
                    params = [year, year]
            else:
                raise ValueError("Unsupported database vendor.")
        elif filter_type =='all':
            if db_vendor == 'postgresql':
                query = """
                        SELECT TO_CHAR(tgl_production, 'YYYY') AS label,
                            SUM(CASE WHEN nama_material = 'LIM' THEN tonnage ELSE 0 END) AS lim,
                            SUM(CASE WHEN nama_material = 'SAP' THEN tonnage ELSE 0 END) AS sap
                        FROM ore_production
                        GROUP BY TO_CHAR(tgl_production, 'YYYY')
                        ORDER BY TO_CHAR(tgl_production, 'YYYY')
                    """ 
            elif db_vendor in ['mssql', 'microsoft']:
                query = """
                        SELECT 
                            CAST(YEAR(tgl_production) AS VARCHAR) AS label,
                            SUM(CASE WHEN nama_material = 'LIM' THEN tonnage ELSE 0 END) AS lim,
                            SUM(CASE WHEN nama_material = 'SAP' THEN tonnage ELSE 0 END) AS sap
                        FROM ore_production
                        GROUP BY YEAR(tgl_production)
                        ORDER BY YEAR(tgl_production)
                    """ 
            else:
                    raise ValueError("Unsupported database vendor.")
            params = []
        else:
            return JsonResponse({'error': 'Invalid or incomplete filter parameters'}, status=400)

        # Eksekusi query
        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            results = cursor.fetchall()

        for row in results:
            x_labels.append(str(row[0]))
            data_lim.append(float(row[1]))
            data_sap.append(float(row[2]))

        return JsonResponse({
            'x_data': x_labels,
            'y_data_lim': data_lim,
            'y_data_sap': data_sap,
        })

    except DatabaseError:
        logger.exception("DB Error in get_chart_ore")
        return JsonResponse({'error': 'Database error'}, status=500)
    except Exception as e:
        logger.exception("Unexpected error in get_chart_ore")
        return JsonResponse({'error': str(e)}, status=500)

def get_chart_ore_class(request):
    try:
        filter_type = request.GET.get('filter_type')
        year = request.GET.get('year')
        month = request.GET.get('month')
        week = request.GET.get('week')
        date_start = request.GET.get('date_start')
        date_end = request.GET.get('date_end')
        filter_date= request.GET.get('filter_date')

        filter_sql = "WHERE 1=1"
        params = []

        # Tentukan kondisi filter SQL dan parameter
        if filter_type =='daily' and filter_date:  # Range
            filter_sql += " AND tgl_production = %s"
            params = [filter_date]

        elif filter_type =='range' and date_start and date_end:  # Range
            filter_sql += " AND tgl_production BETWEEN %s AND %s"
            params = [date_start, date_end]

        elif filter_type =='weekly' and year and month and week:  # Weekly
            try:
                # Deteksi jika 'week' dalam format ISO (contoh: '2025-03')
                if '-' in str(week):
                    year_str, week_str = str(week).split('-')
                    year = int(year_str)
                    week = int(week_str)

                    # Hitung awal minggu (ISO): Senin minggu ke-X
                    start_date = datetime.strptime(f'{year}-W{week:02}-1', "%G-W%V-%u")
                    end_date = start_date + timedelta(days=6)
                    print("Start:", start_date, "End:", end_date)

                else:
                    # Parsing normal year, month, week
                    year  = int(year)
                    month = int(month)
                    week  = int(week)

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
            
            # ✅ Tambahkan WHERE clause filter mingguan
            filter_sql += " AND tgl_production BETWEEN %s AND %s"
            params = [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]

        elif filter_type =='monthly' and year and month:  # Monthly
            filter_sql += " AND EXTRACT(YEAR FROM tgl_production) = %s AND EXTRACT(MONTH FROM tgl_production) = %s" \
                if db_vendor == 'postgresql' else " AND YEAR(tgl_production) = %s AND MONTH(tgl_production) = %s"
            params = [year, month]

        elif filter_type =='yearly' and year:  # Yearly
            filter_sql += " AND EXTRACT(YEAR FROM tgl_production) = %s" \
                if db_vendor == 'postgresql' else " AND YEAR(tgl_production) = %s"
            params = [year]

        elif filter_type =='all':  # All
            pass  # Tidak ada tambahan filter

        else:
            return JsonResponse({'error': 'Invalid or incomplete filter parameters'}, status=400)

        # Query berdasarkan vendor
        if db_vendor == 'postgresql':
            query = f"""
                SELECT
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'LGL' THEN tonnage ELSE 0 END)::NUMERIC, 2), 0) AS LGLO,
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'MGL' THEN tonnage ELSE 0 END)::NUMERIC, 2), 0) AS MGLO,
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'HGL' THEN tonnage ELSE 0 END)::NUMERIC, 2), 0) AS HGLO,
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'LGS' THEN tonnage ELSE 0 END)::NUMERIC, 2), 0) AS LGSO,
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'MGS' THEN tonnage ELSE 0 END)::NUMERIC, 2), 0) AS MGSO,
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'HGS' THEN tonnage ELSE 0 END)::NUMERIC, 2), 0) AS HGSO
                FROM ore_productions
                {filter_sql}
            """
        elif db_vendor in ['mysql', 'mssql', 'microsoft']:
            query = f"""
                SELECT
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'LGL' THEN tonnage ELSE 0 END), 2), 0) AS LGLO,
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'MGL' THEN tonnage ELSE 0 END), 2), 0) AS MGLO,
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'HGL' THEN tonnage ELSE 0 END), 2), 0) AS HGLO,
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'LGS' THEN tonnage ELSE 0 END), 2), 0) AS LGSO,
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'MGS' THEN tonnage ELSE 0 END), 2), 0) AS MGSO,
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'HGS' THEN tonnage ELSE 0 END), 2), 0) AS HGSO
                FROM ore_productions
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

