# views.py
import logging
from django.http import JsonResponse
from django.db import connections
import pandas as pd
from datetime import datetime, date, timedelta
from django.db.utils import DatabaseError
import calendar
logger = logging.getLogger(__name__) 
from ....utils.db_utils import get_db_vendor

 # Memanggil fungsi utility
db_vendor = get_db_vendor('kqms_db')

def safe_division(numerator, denominator):
    return round(numerator / denominator * 100, 0) if denominator else 0

# For Chart
def get_chart_fuel(request):
    filter_type  = request.GET.get('filter_type')
    filter_year  = int(request.GET.get('year', 0))
    filter_month = int(request.GET.get('month', 0))
    filter_week  = request.GET.get('week')
    filter_date  = request.GET.get('filter_date')
    date_start   = request.GET.get('date_start')
    date_end     = request.GET.get('date_end')

    if filter_type == 'monthly' and filter_year and filter_month:
        return get_monthly_chart(filter_year, filter_month)
    
    elif filter_type == 'daily' and filter_date:
        return get_daily_chart(filter_date)

    elif filter_type == 'range' and date_start and date_end:
        return get_range_chart(date_start, date_end)

    elif filter_type == 'yearly' and filter_year:
        return get_yearly_chart(filter_year)

    elif filter_type == 'weekly' and filter_week:
        return get_weekly_chart(filter_week)

    elif filter_type == 'all':
        return get_all_chart()

    else:
        return JsonResponse({'error': 'Invalid filter'}, status=400)

def get_daily_chart(filter_date):
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
                hour_series AS (
                    SELECT 
                        make_time(hour_label, 0, 0) AS raw_time,
                        TO_CHAR(make_time(hour_label, 0, 0), 'HH24') AS left_time,
                        hour_label,
                        sort_order
                    FROM working_hours
                ),
                agg_data AS (
                    SELECT 
                        LPAD(charging_time::text, 2, '0') AS charging_time,
                        SUM(volume) AS total_volume
                    FROM mine_units_fuel_consumption mp
                    WHERE mp.date = %s::date
                    GROUP BY LPAD(t_load::text, 2, '0')
                )
                SELECT
                    hs.hour_label AS id,
                    hs.left_time,
                    COALESCE(a.total_volume, 0)::numeric(10,2) AS total
                FROM hour_series hs
                LEFT JOIN agg_data a ON hs.left_time = a.t_load_time
                ORDER BY hs.sort_order;
            """
        else:
            raise ValueError("Unsupported vendor")

        params = [filter_date,filter_date]

        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            data = cursor.fetchall()

        df = pd.DataFrame(data, columns=['time', 'left_time', 'total'])
        df['total'] = pd.to_numeric(df['total'], errors='coerce').fillna(0.0).round(2)
        # grand total
        grand_total = round(df['total'].sum(), 2)

        return JsonResponse({
            'x_data'     : df['left_time'].tolist(),  # ini label jam (misal: "01:00", "02:00", ...)
            'y_data'     : df['total'].tolist(),
            'grand_total': float(grand_total)
        }, safe=False)

def get_monthly_chart(filter_year, filter_month):
    # Ambil jumlah hari terakhir dalam bulan
    year  = int(filter_year)
    month = int(filter_month)
    # Ambil jumlah hari terakhir dalam bulan
    last_day = calendar.monthrange(year, month)[1]
    # Bangun tanggal awal dan akhir bulan
    tgl_pertama  = datetime(year, month, 1).date()
    tgl_terakhir = datetime(year, month, last_day).date()
    # Siapkan parameter untuk query
    params = [
            tgl_pertama, tgl_terakhir,  # generate_series
            tgl_pertama, tgl_terakhir,  # actual
        ]

    query = """
            WITH tanggal AS (
                    SELECT generate_series(%s::date, %s::date, interval '1 day') AS date
                ),
                actual AS (
                    SELECT
                        date::date AS date,
                        SUM(volume) AS volume
                    FROM mine_units_fuel_consumption
                    WHERE date BETWEEN %s AND %s
                    GROUP BY date
                )
            SELECT
                TO_CHAR(tanggal.date, 'DD') AS left_date,
                ROUND(COALESCE(a.volume, 0)::numeric, 2) AS total_volume
            FROM tanggal
            LEFT JOIN actual a ON tanggal.date = a.date
            ORDER BY tanggal.date
        """

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params)
        data = cursor.fetchall()

    df = pd.DataFrame(data, columns=['left_date', 'total_volume'])
    
    # Konversi ke float, pastikan tidak dalam string
    df['total_volume'] = pd.to_numeric(df['total_volume'], errors='coerce').fillna(0.0).round(2)

    # grand total
    grand_total = round(df['total_volume'].sum(), 2)

    return JsonResponse({
        'x_data'      : df['left_date'].tolist(),
        'y_data'      : df['total_volume'].astype(float).tolist(),
        'grand_total' : float(grand_total)
    }, safe=False)

def get_weekly_chart(filter_week):

    iso_year, iso_week = map(int, filter_week.split('-'))

    # Ambil hari pertama dan terakhir dari minggu ISO tersebut
    start_date = date.fromisocalendar(iso_year, iso_week, 1)  # Senin
    end_date   = date.fromisocalendar(iso_year, iso_week, 7)    # Minggu

    params     = [start_date, end_date, filter_week]

    query = """
        WITH hari AS (
            SELECT generate_series(%s::date, %s::date, interval '1 day') AS tanggal
        ),
        actual AS (
            SELECT
                DATE(date) AS tanggal,
                TO_CHAR(date, 'FMDy') AS nama_hari,
                SUM(volume) AS volume
            FROM mine_units_fuel_consumption
            WHERE TO_CHAR(date, 'IYYY-IW') = %s
            GROUP BY DATE(date), TO_CHAR(date, 'FMDy')
        )
        SELECT
            TO_CHAR(hari.tanggal, 'YYYY-MM-DD') AS tanggal,
            TO_CHAR(hari.tanggal, 'FMDy') AS hari,
            ROUND(COALESCE(a.volume, 0)::numeric, 2) AS total_volume
        FROM hari
        LEFT JOIN actual a ON hari.tanggal = a.tanggal
        ORDER BY hari.tanggal
    """

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params)
        data = cursor.fetchall()

    df = pd.DataFrame(data, columns=['tanggal', 'hari','total_volume'])
    
    # Konversi ke float, pastikan tidak dalam string
    df['total_volume'] = pd.to_numeric(df['total_volume'], errors='coerce').fillna(0.0).round(2)

    # grand total
    grand_total = round(df['total_volume'].sum(), 2)

    return JsonResponse({
        'x_data'     : df['hari'].tolist(),
        'y_data'     : df['total_volume'].astype(float).tolist(),
        'grand_total': float(grand_total)
    }, safe=False)

def get_range_chart(date_start, date_end):
    query = """
        WITH tanggal AS (
            SELECT generate_series(%s::date, %s::date, interval '1 day') AS date
        ),
        actual AS (
            SELECT
                DATE(date) AS tanggal,
                SUM(volume) AS volume
            FROM mine_units_fuel_consumption
            WHERE date BETWEEN %s AND %s
            GROUP BY DATE(date)
        )
        SELECT
            TO_CHAR(tanggal.date, 'YYYY-MM-DD') AS tanggal,
            ROUND(COALESCE(a.volume, 0)::numeric, 2) AS total_volume
        FROM tanggal
        LEFT JOIN actual a ON tanggal.date = a.tanggal
        ORDER BY tanggal.date
    """
    params = [date_start, date_end, 
              date_start, date_end,
              ]

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params)
        data = cursor.fetchall()

    df = pd.DataFrame(data, columns=['tanggal','total_volume'])
    
    # Konversi ke float, pastikan tidak dalam string
    df['total_volume'] = pd.to_numeric(df['total_volume'], errors='coerce').fillna(0.0).round(2)

    # grand total
    grand_total = round(df['total_volume'].sum(), 2)

    return JsonResponse({
        'x_data'     : df['tanggal'].tolist(),
        'y_data'     : df['total_volume'].astype(float).tolist(),
        'grand_total': float(grand_total)
    }, safe=False)

def get_yearly_chart(yearly):
    query = """
         WITH bulan AS (
            SELECT TO_CHAR(DATE_TRUNC('month', (DATE %s + (n || ' month')::interval)), 'YYYY-MM') AS bulan
            FROM generate_series(0, 11) AS n
        ),
        actual AS (
            SELECT
                TO_CHAR(date, 'YYYY-MM') AS bulan,
                SUM(volume) AS volume
            FROM mine_units_fuel_consumption
            WHERE EXTRACT(YEAR FROM date) = %s
            GROUP BY TO_CHAR(date, 'YYYY-MM')
        )
        SELECT
            b.bulan,
            ROUND(COALESCE(a.volume, 0)::numeric, 2) AS total_volume
        FROM bulan b
        LEFT JOIN actual a ON a.bulan = b.bulan
        ORDER BY b.bulan
    """

    params = [f"{yearly}-01-01", yearly]

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params)
        data = cursor.fetchall()

    df = pd.DataFrame(data, columns=['bulan','total_volume'])
    
    # Konversi ke float, pastikan tidak dalam string
    df['total_volume'] = pd.to_numeric(df['total_volume'], errors='coerce').fillna(0.0).round(2)

    # grand total
    grand_total = round(df['total_volume'].sum(), 2)

    # Define month names
    x_data = df['bulan'].apply(lambda x: datetime.strptime(x, '%Y-%m').strftime('%b %y')).tolist()

    return JsonResponse({
        'x_data'     : x_data,
        'y_data'     : df['total_volume'].astype(float).tolist(),
        'grand_total': float(grand_total)
    }, safe=False)

def get_all_chart():
    query = """ 
          WITH actual_per_year AS (
                SELECT 
                    TO_CHAR(date, 'YYYY') AS tahun,
                    SUM(volume) AS total_volume
                FROM mine_units_fuel_consumption
                GROUP BY TO_CHAR(date, 'YYYY')
            ),
            SELECT 
                COALESCE(a.tahun, p.tahun) AS tahun,
                COALESCE(a.volume, 0) AS total_volume
            FROM actual_per_year a
            ORDER BY tahun
    """
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query)
        data = cursor.fetchall()

    df = pd.DataFrame(data, columns=['tahun','total_volume'])
    df['total'] = pd.to_numeric(df['total_tonnage'], errors='coerce').fillna(0.0).round(2)

    # grand total
    grand_total = round(df['total_volume'].sum(), 2)


    return JsonResponse({
        'x_data'     : df['tahun'].tolist(), 
        'y_date'     : df['total'].tolist(),
        'grand_total': float(grand_total)
    }, safe=False)

# grouped by fuel_category
def get_chart_fuel_category(request):
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
        if filter_type =='daily' and filter_date:
            filter_sql += " AND date = %s"
            params = [filter_date]

        elif filter_type =='range' and date_start and date_end:  # Range
            filter_sql += " AND date BETWEEN %s AND %s"
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
            
            # Tambahkan WHERE clause filter mingguan
            filter_sql += " AND date BETWEEN %s AND %s"
            params = [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]

        elif filter_type =='monthly' and year and month:  # Monthly
            filter_sql += " AND EXTRACT(YEAR FROM date) = %s AND EXTRACT(MONTH FROM date) = %s" \
                if db_vendor == 'postgresql' else " AND YEAR(date) = %s AND MONTH(date) = %s"
            params = [year, month]

        elif filter_type =='yearly' and year:  # Yearly
            filter_sql += " AND EXTRACT(YEAR FROM date) = %s" \
                if db_vendor == 'postgresql' else " AND YEAR(date) = %s"
            params = [year]

        elif filter_type =='all':  # All
            pass  # Tidak ada tambahan filter

        else:
            return JsonResponse({'error': 'Invalid or incomplete filter parameters'}, status=400)

        # Query berdasarkan vendor
        if db_vendor == 'postgresql':
            query = f"""
                SELECT
                    COALESCE(TRIM(BOTH FROM category), 'Unknown'::text) AS category,
                    COALESCE(ROUND(SUM(volume)::NUMERIC, 2), 0) AS total_voume               
                FROM daily_fuel_consumption
                {filter_sql}
                GROUP BY category
                ORDER BY category
            """
        else:
            raise ValueError(f"Unsupported database vendor: {db_vendor}")

        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        # Konversi hasil menjadi list
        labels = [row[0] for row in rows]
        y_data = [float(row[1]) for row in rows]

        return JsonResponse({
            'labels': labels,
            'y_data': y_data,
        })


    except Exception as e:
        logger.exception("Unexpected error occurred.")
        return JsonResponse({'error': str(e)}, status=500)
    
# by vendors
def get_chart_fuel_vendors(request):
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
        if filter_type =='daily' and filter_date:
            filter_sql += " AND date = %s"
            params = [filter_date]

        elif filter_type =='range' and date_start and date_end:  # Range
            filter_sql += " AND date BETWEEN %s AND %s"
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
            
            # Tambahkan WHERE clause filter mingguan
            filter_sql += " AND date BETWEEN %s AND %s"
            params = [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]

        elif filter_type =='monthly' and year and month:  # Monthly
            filter_sql += " AND EXTRACT(YEAR FROM date) = %s AND EXTRACT(MONTH FROM date) = %s" \
                if db_vendor == 'postgresql' else " AND YEAR(date) = %s AND MONTH(date) = %s"
            params = [year, month]

        elif filter_type =='yearly' and year:  # Yearly
            filter_sql += " AND EXTRACT(YEAR FROM date) = %s" \
                if db_vendor == 'postgresql' else " AND YEAR(date) = %s"
            params = [year]

        elif filter_type =='all':  # All
            pass  # Tidak ada tambahan filter

        else:
            return JsonResponse({'error': 'Invalid or incomplete filter parameters'}, status=400)

        # Query berdasarkan vendor
        if db_vendor == 'postgresql':
            query = f"""
                SELECT
                    COALESCE(TRIM(BOTH FROM code), 'Unknown'::text) AS vendors,
                    COALESCE(ROUND(SUM(volume)::NUMERIC, 2), 0) AS total_voume               
                FROM daily_fuel_consumption
                {filter_sql}
                GROUP BY code
                ORDER BY code
            """
        else:
            raise ValueError(f"Unsupported database vendor: {db_vendor}")

        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        # Konversi hasil menjadi list
        labels = [row[0] for row in rows]
        y_data = [float(row[1]) for row in rows]

        return JsonResponse({
            'x_data': labels,
            'y_data': y_data,
        })


    except Exception as e:
        logger.exception("Unexpected error occurred.")
        return JsonResponse({'error': str(e)}, status=500)
