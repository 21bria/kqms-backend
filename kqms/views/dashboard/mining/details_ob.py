# views.py
import logging
from django.http import JsonResponse
from django.db import connections, DatabaseError
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from django.utils.timezone import now
logger = logging.getLogger(__name__) 
from ....utils.db_utils import get_db_vendor

 # Memanggil fungsi utility
db_vendor = get_db_vendor('kqms_db')
import json

def safe_division(numerator, denominator):
    return round(numerator / denominator * 100, 0) if denominator else 0

# For Chart
def get_chart_detail_ob(request):
    filter_type  = request.GET.get('filter_type')
    filter_year  = int(request.GET.get('filter_year', 0))
    filter_month = int(request.GET.get('filter_month', 0))
    filter_week  = request.GET.get('filter_week')
    filter_date  = request.GET.get('filter_date')
    date_start   = request.GET.get('date_start')
    date_end     = request.GET.get('date_end')

    if filter_type == 'monthly' and filter_year and filter_month:
        return get_monthly_detail_chart(filter_year, filter_month)
    
    elif filter_type == 'daily' and filter_date:
        return get_daily_detail_chart(filter_date)

    elif filter_type == 'range' and date_start and date_end:
        return get_range_detail_chart(date_start, date_end)

    elif filter_type == 'yearly' and filter_year:
        return get_yearly_chart(filter_year)

    elif filter_type == 'weekly' and filter_week:
        return get_weekly_detail_chart(filter_week)

    else:
        return JsonResponse({'error': 'Invalid filter'}, status=400)

def get_daily_detail_chart(filter_date):
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
					    WHEN nama_material IN ('OB') 
					    THEN tonnage 
					    ELSE 0 
					END)::numeric AS total_tonnage,
			        SUM(
			            COALESCE(ob, 0)
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
    df['achievement'] = df.apply( lambda row: round(float(row['total']) / float(row['plan_data']) * 100, 2) if float(row['plan_data']) > 0 else 0,axis=1)

    return JsonResponse({
        'x_data': df['left_time'].tolist(),  # ini label jam (misal: "01:00", "02:00", ...)
        'total_actual': df['total'].tolist(),
        'total_plan': df['plan_data'].tolist(),
        'achievement': df['achievement'].tolist(),
    }, safe=False)

def get_monthly_detail_chart(filter_year, filter_month):
     # Ambil jumlah hari terakhir dalam bulan
    last_day = calendar.monthrange(int(filter_year), int(filter_month))[1]

    query = """
        SELECT 
                t1.left_date,
                ROUND(SUM(t2.tonnage)::numeric, 2) AS total_tonnage,
                ROUND(COALESCE(tp.plan_data, 0)::numeric, 2) AS total_plan
            FROM tanggal t1
            LEFT JOIN (
                SELECT 
                    left_date,
                    SUM(CASE WHEN nama_material = 'OB' THEN tonnage ELSE 0 END)::numeric AS tonnage
                FROM mine_productions
                WHERE EXTRACT(MONTH FROM date_production) = %s
                AND EXTRACT(YEAR FROM date_production) = %s
                GROUP BY left_date
            ) AS t2 ON t1.left_date = t2.left_date
            LEFT JOIN (
                SELECT 
                    EXTRACT(DAY FROM date_plan)::int AS day_plan,
                    SUM(COALESCE(ob, 0))AS plan_data
                FROM plan_productions
                WHERE EXTRACT(MONTH FROM date_plan) = %s
                AND EXTRACT(YEAR FROM date_plan) = %s
                GROUP BY day_plan
            ) AS tp ON t1.left_date = tp.day_plan
        WHERE t1.left_date <= %s
        GROUP BY t1.left_date, tp.plan_data
        ORDER BY t1.left_date ASC;
        """

    params = [filter_month, filter_year, filter_month, filter_year, last_day]

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params)
        data = cursor.fetchall()

    df = pd.DataFrame(data, columns=['left_date', 'total_tonnage', 'total_plan'])
    
    # Konversi ke float, pastikan tidak dalam string
    df['total_tonnage'] = pd.to_numeric(df['total_tonnage'], errors='coerce').fillna(0.0).round(2)
    df['total_plan']    = pd.to_numeric(df['total_plan'], errors='coerce').fillna(0.0).round(2)

    # Optional: hitung achievement jika dibutuhkan
    df['achievement'] = df.apply( lambda row: round(float(row['total_tonnage']) / float(row['total_plan']) * 100, 2) if float(row['total_plan']) > 0 else 0,axis=1)

    return JsonResponse({
        'x_data': df['left_date'].tolist(),
        'total_tonnage': df['total_tonnage'].astype(float).tolist(),
        'total_plan': df['total_plan'].astype(float).tolist(),
        # 'achievement': df['achievement'].astype(float).tolist()
    }, safe=False)

def get_weekly_detail_chart(filter_week):
    # iso_week_str = f"{iso_year}-{str(iso_week).zfill(2)}"  # pastikan format IYYY-IW: "2025-04"
    query = """
        WITH actual AS (
            SELECT
                DATE(date_production) AS tanggal,
                TO_CHAR(date_production, 'FMDy') AS nama_hari,
                SUM(CASE WHEN nama_material = 'OB' THEN tonnage ELSE 0 END)::numeric AS ob
            FROM mine_productions
            WHERE TO_CHAR(date_production, 'IYYY-IW') = %s
            GROUP BY tanggal
        ),
        plan AS (
            SELECT
                DATE(date_plan) AS tanggal,
                TO_CHAR(date_plan, 'FMDy') AS nama_hari,
                SUM(ob)::numeric AS ob_plan
            FROM plan_productions
            WHERE TO_CHAR(date_plan, 'IYYY-IW') = %s
            GROUP BY tanggal
        )
        SELECT
            COALESCE(a.tanggal, p.tanggal) AS tanggal,
            COALESCE(a.nama_hari, p.nama_hari) AS hari,
            ROUND(COALESCE(a.ob, 0), 2) AS ob,
            ROUND(COALESCE(p.ob_plan, 0), 2) AS ob_plan,
            ROUND(CASE WHEN p.ob_plan > 0 THEN (a.ob * 100.0 / p.ob_plan)::numeric ELSE 0 END, 2) AS ob_ach
        FROM actual a
        FULL OUTER JOIN plan p ON a.tanggal = p.tanggal
        ORDER BY tanggal;
    """

    params = [filter_week, filter_week]

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params)
        data = cursor.fetchall()

    columns = [
        'tanggal', 'hari',
        'ob', 'ob_plan', 'ob_ach'
    ]

    df = pd.DataFrame(data, columns=columns)

    ob_cols = ['ob']
    ob_plan_cols = [f + '_plan' for f in ob_cols]

    # Konversi kolom ke numerik (handle string atau null)
    for col in ob_cols  :
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(float)

    df['ob']       = df[ob_cols].sum(axis=1)
    df['ob_plan']  = df[ob_plan_cols].sum(axis=1)

    df['total_actual'] = df['ob']
    df['total_plan']   = df['ob_plan']
    df['achievement'] = df.apply( lambda row: round(float(row['total_actual']) / float(row['total_plan']) * 100, 2) if float(row['total_plan']) > 0 else 0,axis=1)

    return JsonResponse({
        'x_data'       : df['hari'].astype(str).tolist(),
        'total_actual' : df['total_actual'].astype(float).tolist(),
        'total_plan'   : df['total_plan'].astype(float).tolist(),
        'achievement'  : df['achievement'].astype(float).tolist(),
    }, safe=False)

def get_range_detail_chart(date_start, date_end):
    query = """
        WITH actual AS (
            SELECT
                DATE(date_production) AS tanggal,
                SUM(CASE WHEN nama_material = 'OB' THEN tonnage ELSE 0 END)::numeric AS ob
            FROM mine_productions
            WHERE date_production BETWEEN %s AND %s
            GROUP BY tanggal
        ),
        plan AS (
            SELECT
                DATE(date_plan) AS tanggal,
                SUM(ob)::numeric AS ob_plan
            FROM plan_productions
            WHERE date_plan BETWEEN %s AND %s
            GROUP BY tanggal
        )
        SELECT
            COALESCE(a.tanggal, p.tanggal) AS tanggal,
            ROUND(COALESCE(a.ob, 0), 2) AS ob,
            ROUND(COALESCE(p.ob_plan, 0), 2) AS ob_plan,
            ROUND(CASE WHEN p.ob_plan > 0 THEN (a.ob * 100.0 / p.ob_plan)::numeric ELSE 0 END, 2) AS ob_ach
        FROM actual a
        FULL OUTER JOIN plan p ON a.tanggal = p.tanggal
        ORDER BY tanggal;
    """

    params = [date_start, date_end, date_start, date_end]

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params)
        data = cursor.fetchall()

    columns = [
        'tanggal',
        'ob', 'ob_plan', 'ob_ach'
    ]

    df = pd.DataFrame(data, columns=columns)

    ob_cols = ['ob']
    ob_plan_cols = [f + '_plan' for f in ob_cols]


    # Konversi kolom ke numerik (handle string atau null)
    for col in ob_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(float)

    df['ob']       = df[ob_cols].sum(axis=1)
    df['ob_plan']  = df[ob_plan_cols].sum(axis=1)


    df['total_actual'] = df['ob'] 
    df['total_plan']   = df['ob_plan']
    df['achievement']  = df.apply( lambda row: round(float(row['total_actual']) / float(row['total_plan']) * 100, 2) if float(row['total_plan']) > 0 else 0,axis=1)

    return JsonResponse({
        'x_data'        : df['tanggal'].astype(str).tolist(),
        'total_actual' : df['total_actual'].astype(float).tolist(),
        'total_plan'   : df['total_plan'].astype(float).tolist(),
        'achievement'  : df['achievement'].astype(float).tolist(),
    }, safe=False)

def get_yearly_chart(yearly):
    query = """
        WITH actual AS (
            SELECT
                TO_CHAR(date_production, 'YYYY-MM') AS bulan,
                SUM(CASE WHEN nama_material = 'OB' THEN tonnage ELSE 0 END)::numeric AS ob
            FROM mine_productions
            WHERE EXTRACT(YEAR FROM date_production) = %s
            GROUP BY bulan
        ),
        plan AS (
            SELECT
                TO_CHAR(date_plan, 'YYYY-MM') AS bulan,
                SUM(ob)::numeric AS ob_plan
            FROM plan_productions
            WHERE EXTRACT(YEAR FROM date_plan) = %s
            GROUP BY bulan
        )
        SELECT
            COALESCE(a.bulan, p.bulan) AS bulan,
            ROUND(COALESCE(a.ob, 0), 2) AS ob,
            ROUND(COALESCE(p.ob_plan, 0), 2) AS ob_plan,
            ROUND(CASE WHEN p.ob_plan > 0 THEN (a.ob * 100.0 / p.ob_plan)::numeric ELSE 0 END, 2) AS ob_ach
        FROM actual a
        FULL OUTER JOIN plan p ON a.bulan = p.bulan
        ORDER BY bulan;
    """

    params = [yearly,yearly]

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params)
        data = cursor.fetchall()

    columns = [
        'bulan',
        'ob', 'ob_plan', 'ob_ach'
    ]

    df = pd.DataFrame(data, columns=columns)

    ob_cols = ['ob']
    ob_plan_cols = [f + '_plan' for f in ob_cols]

    # Konversi kolom ke numerik (handle string atau null)
    for col in ob_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(float)

    df['ob']       = df[ob_cols].sum(axis=1)
    df['ob_plan']  = df[ob_plan_cols].sum(axis=1)

    df['total_actual'] = df['ob'] 
    df['total_plan']   = df['ob_plan']
    df['achievement'] = df.apply( lambda row: round(float(row['total_actual']) / float(row['total_plan']) * 100, 2) if float(row['total_plan']) > 0 else 0,axis=1)

    # Define month names
    x_data = df['bulan'].apply(lambda x: datetime.strptime(x, '%Y-%m').strftime('%b %y')).tolist()

    return JsonResponse({
        'x_data'       : x_data,  # Contoh: ['Jan 25', 'Feb 25', ...]
        'total_actual' : df['total_actual'].astype(float).tolist(),
        'total_plan'   : df['total_plan'].astype(float).tolist(),
        'achievement'  : df['achievement'].astype(float).tolist(),
    }, safe=False)





