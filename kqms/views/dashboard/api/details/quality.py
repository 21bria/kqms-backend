# views.py
import logging
from django.http import JsonResponse
from django.db import connections, DatabaseError
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from django.utils.timezone import now
logger = logging.getLogger(__name__) 
from .....utils.db_utils import get_db_vendor

 # Memanggil fungsi utility
db_vendor = get_db_vendor('kqms_db')


def safe_division(numerator, denominator):
    return round(numerator / denominator * 100, 0) if denominator else 0

def get_start_end_of_week(iso_week_str):
    year, week = map(int, iso_week_str.split('-'))
    start = datetime.strptime(f'{year}-W{week - 1}-1', "%Y-W%W-%w").date()
    end = start + timedelta(days=6)
    return start, end
# For Chart
def get_chart_detail_quality(request):
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

    else:
        return JsonResponse({'error': 'Invalid filter'}, status=400)

def get_daily_chart(filter_date):
    query = """ 
             SELECT
                t1.id,
                t1.left_time,
                COALESCE(SUM(t2.total_tonnage), 0)::numeric(10,2) AS total,
                ROUND(COALESCE(SUM(DISTINCT t2.plan_data), 0)::numeric / 22, 2) AS plan_data
            FROM tanggal_jam t1
            LEFT JOIN (
			    SELECT 
			        t_load,
			        SUM(CASE 
					    WHEN nama_material IN ('LGLO', 'MGLO', 'HGLO', 'MWS', 'LGSO', 'MGSO', 'HGSO') 
					    THEN tonnage 
					    ELSE 0 
					END)::numeric AS total_tonnage,
			        SUM(
			            COALESCE(lglo, 0) + COALESCE(mglo, 0) +
			            COALESCE(hglo, 0) + COALESCE(mws, 0) + COALESCE(lgso, 0) +
			            COALESCE(mgso, 0) + COALESCE(hgso, 0)
			        ) AS plan_data
			    FROM mine_productions
			    LEFT JOIN plan_productions 
			        ON mine_productions.date_production = plan_productions.date_plan
			    WHERE date_production=%s
			    GROUP BY t_load
			) t2 ON t1.left_time = t2.t_load
            GROUP BY t1.id, t1.left_time
            ORDER BY t1.id;
    """

    params = [filter_date]

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params)
        data = cursor.fetchall()

    df = pd.DataFrame(data, columns=['id', 'left_time', 'total', 'plan_data'])
    df['total'] = pd.to_numeric(df['total'], errors='coerce').fillna(0.0).round(2)
    df['plan_data'] = pd.to_numeric(df['plan_data'], errors='coerce').fillna(0.0).round(2)
    df['achievement'] = df.apply(lambda r: round((r['total'] / r['plan_data'] * 100), 2) if r['plan_data'] > 0 else 0.0, axis=1)

    return JsonResponse({
        'x_data': df['left_time'].tolist(),  # ini label jam (misal: "01:00", "02:00", ...)
        'total_actual': df['total'].tolist(),
        'total_plan': df['plan_data'].tolist(),
        'achievement': df['achievement'].tolist(),
    }, safe=False)

def get_monthly_chart(filter_year, filter_month):
    # Ambil jumlah hari terakhir dalam bulan
    # last_day = calendar.monthrange(int(filter_year), int(filter_month))[1]

    year  = int(filter_year)
    month = int(filter_month)
    # Ambil jumlah hari terakhir dalam bulan
    last_day = calendar.monthrange(year, month)[1]
    # Bangun tanggal awal dan akhir bulan
    tgl_pertama  = datetime(year, month, 1).date()
    tgl_terakhir = datetime(year, month, last_day).date()
    # Siapkan parameter untuk query

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
                COALESCE(i.sap, 0) AS lim
            FROM tanggal
            LEFT JOIN incoming i ON tanggal.date = i.date
            ORDER BY tanggal.date
        """

    params = [tgl_pertama, tgl_terakhir,tgl_pertama, tgl_terakhir]

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params)
        data = cursor.fetchall()

    df = pd.DataFrame(data, columns=['label', 'lim','sap'])
    
    # Konversi ke float, pastikan tidak dalam string
    df['total_lim'] = pd.to_numeric(df['lim'], errors='coerce').fillna(0.0).round(2)
    df['total_sap'] = pd.to_numeric(df['sap'], errors='coerce').fillna(0.0).round(2)


    return JsonResponse({
        'x_data': df['label'].tolist(),
        'y_lim': df['total_lim'].astype(float).tolist(),
        'y_sap': df['total_sap'].astype(float).tolist(),
    }, safe=False)

def get_weekly_chart(filter_week):

    start_date, end_date = get_start_end_of_week(filter_week)

    if db_vendor == 'postgresql':
        query = """
            WITH tanggal AS (
                SELECT generate_series(%s::date, %s::date, interval '1 day') AS date
            ),
            incoming AS (
                SELECT
                    tgl_production::date AS date,
                    TO_CHAR(tgl_production, 'FMDy') AS hari,
                    SUM(CASE WHEN nama_material = 'LIM' THEN tonnage ELSE 0 END) AS lim,
                    SUM(CASE WHEN nama_material = 'SAP' THEN tonnage ELSE 0 END) AS sap
                FROM ore_production
                WHERE TO_CHAR(tgl_production, 'IYYY-IW') = %s
                GROUP BY tgl_production
            )
            SELECT
                TO_CHAR(tanggal.date, 'FMDy') AS hari,
                tanggal.date,
                COALESCE(i.lim, 0) AS lim,
                COALESCE(i.sap, 0) AS sap
            FROM tanggal
            LEFT JOIN incoming i ON tanggal.date = i.date
            ORDER BY tanggal.date;
        """
    else:
        raise ValueError("Unsupported database vendor.")

    params = [start_date, end_date, filter_week]

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params)
        data = cursor.fetchall()

    df = pd.DataFrame(data, columns=['label', 'date', 'lim', 'sap'])

    df['total_lim'] = pd.to_numeric(df['lim'], errors='coerce').fillna(0.0).round(2)
    df['total_sap'] = pd.to_numeric(df['sap'], errors='coerce').fillna(0.0).round(2)

    return JsonResponse({
        'x_data': df['label'].tolist(),
        'y_lim': df['total_lim'].tolist(),
        'y_sap': df['total_sap'].tolist(),
    }, safe=False)

def get_range_chart(date_start, date_end):
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
    else:
        raise ValueError("Unsupported database vendor.")

    params = [date_start, date_end, date_start, date_end]

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params)
        data = cursor.fetchall()

    df = pd.DataFrame(data, columns=['label', 'lim','sap'])
    
    # Konversi ke float, pastikan tidak dalam string
    df['total_lim'] = pd.to_numeric(df['lim'], errors='coerce').fillna(0.0).round(2)
    df['total_sap'] = pd.to_numeric(df['sap'], errors='coerce').fillna(0.0).round(2)

    return JsonResponse({

        'x_data': df['label'].tolist(),
        'y_lim' : df['total_lim'].astype(float).tolist(),
        'y_sap' : df['total_sap'].astype(float).tolist(),
    }, safe=False)

def get_yearly_chart(filter_year):
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
    else:
        raise ValueError("Unsupported database vendor.")
    params = [filter_year]

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params)
        data = cursor.fetchall()

    df = pd.DataFrame(data, columns=['label', 'lim','sap'])
    
    # Konversi ke float, pastikan tidak dalam string
    df['total_lim'] = pd.to_numeric(df['lim'], errors='coerce').fillna(0.0).round(2)
    df['total_sap'] = pd.to_numeric(df['sap'], errors='coerce').fillna(0.0).round(2)

    return JsonResponse({
        'x_data': df['label'].tolist(),
        'y_lim' : df['total_lim'].astype(float).tolist(),
        'y_sap' : df['total_sap'].astype(float).tolist(),
    }, safe=False)

# Class Ore
def get_chart_ore_class_lim(request):
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
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'HGL' THEN tonnage ELSE 0 END)::NUMERIC, 2), 0) AS HGLO
                FROM ore_productions
                {filter_sql}
            """
        elif db_vendor in ['mysql', 'mssql', 'microsoft']:
            query = f"""
                SELECT
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'LGL' THEN tonnage ELSE 0 END), 2), 0) AS LGLO,
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'MGL' THEN tonnage ELSE 0 END), 2), 0) AS MGLO,
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'HGL' THEN tonnage ELSE 0 END), 2), 0) AS HGLO
                FROM ore_productions
                {filter_sql}
            """
        else:
            raise ValueError(f"Unsupported database vendor: {db_vendor}")

        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchone()  # karena hasil SUM hanya satu baris

        # Konversi hasil menjadi list
        y_data = [float(val) for val in chart_data] if chart_data else [0, 0, 0]


        return JsonResponse({
            'labels': ['LGLO', 'MGLO', 'HGLO'],
            'y_data': y_data,
        })

    except DatabaseError:
        logger.exception("Database query failed.")
        return JsonResponse({'error': 'Internal server error'}, status=500)

    except Exception as e:
        logger.exception("Unexpected error occurred.")
        return JsonResponse({'error': str(e)}, status=500)
    
def get_chart_ore_class_sap(request):
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
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'LGS' THEN tonnage ELSE 0 END)::NUMERIC, 2), 0) AS LGSO,
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'MGS' THEN tonnage ELSE 0 END)::NUMERIC, 2), 0) AS MGSO,
                    COALESCE(ROUND(SUM(CASE WHEN ore_class = 'HGS' THEN tonnage ELSE 0 END)::NUMERIC, 2), 0) AS HGSO
                FROM ore_productions
                {filter_sql}
            """
        elif db_vendor in ['mysql', 'mssql', 'microsoft']:
            query = f"""
                SELECT
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
        y_data = [float(val) for val in chart_data] if chart_data else [0, 0, 0]


        return JsonResponse({
            'labels': ['LGSO', 'MGSO', 'HGSO'],
            'y_data': y_data,
        })

    except DatabaseError:
        logger.exception("Database query failed.")
        return JsonResponse({'error': 'Internal server error'}, status=500)

    except Exception as e:
        logger.exception("Unexpected error occurred.")
        return JsonResponse({'error': str(e)}, status=500)


