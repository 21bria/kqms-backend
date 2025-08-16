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
def get_chart_detail_others(request):
    filter_type  = request.GET.get('filter_type')
    filter_year  = int(request.GET.get('filter_year', 0))
    filter_month = int(request.GET.get('filter_month', 0))
    filter_week  = request.GET.get('filter_week')
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
                    LPAD(t_load::text, 2, '0') AS t_load_time,
                    SUM(CASE WHEN nama_material IN ('Ballast','Biomass') THEN tonnage ELSE 0 END)::numeric AS total_tonnage
                FROM mine_productions mp
                WHERE mp.date_production = %s::date
                GROUP BY LPAD(t_load::text, 2, '0')
            ),
            plan_per_hour AS (
                SELECT
                    ROUND(SUM(COALESCE(ballast) + COALESCE(biomass,0))::numeric / 22, 3) AS plan_data
                FROM plan_productions
                WHERE date_plan = %s::date
            )
            SELECT
                hs.hour_label AS id,
                hs.left_time,
                COALESCE(agg.total_tonnage, 0) AS total,
                p.plan_data
            FROM hour_series hs
            LEFT JOIN agg_data agg ON hs.left_time = agg.t_load_time
            CROSS JOIN plan_per_hour p
            ORDER BY hs.sort_order;
    """

    params = [filter_date,filter_date]

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params)
        data = cursor.fetchall()

    df = pd.DataFrame(data, columns=['id', 'left_time', 'total', 'plan_data'])
    df['total']         = pd.to_numeric(df['total'], errors='coerce').fillna(0.0).round(2)
    df['plan_data']     = pd.to_numeric(df['plan_data'], errors='coerce').fillna(0.0)
    df['achievement']   = df.apply(lambda r: round((r['total'] / r['plan_data'] * 100), 2) if r['plan_data'] > 0 else 0.0, axis=1)

    # === Grand Total per tanggal ===
    grand_total = {
        'total' : round(df['total'].sum(), 2),
        'plan'  : round(df['plan_data'].sum(), 2),  # sum dulu, baru round
        'achievement' : round((df['total'].sum() / df['plan_data'].sum() * 100), 2) if df['plan_data'].sum() > 0 else 0.0,
        'avg': round(df['total'].mean(), 2)
    }

    return JsonResponse({
        'x_data'        : df['left_time'].tolist(),
        'total_actual'  : df['total'].tolist(),
        'total_plan'    : df['plan_data'].tolist(),
        'achievement'   : df['achievement'].tolist(),
        'grand_total'   : grand_total
    }, safe=False)

def get_monthly_chart(filter_year, filter_month):
    query = """
    WITH day_series AS (
        SELECT generate_series(
            make_date(%s, %s, 1), 
            (make_date(%s, %s, 1) + interval '1 month - 1 day')::date,
            interval '1 day'
        )::date AS left_date
    ),
    actual AS (
        SELECT 
            DATE(date_production) AS prod_date,
            SUM(
                CASE WHEN nama_material IN ('Ballast','Biomass') 
                THEN tonnage ELSE 0 END
            )::numeric AS total_tonnage
        FROM mine_productions
        WHERE EXTRACT(MONTH FROM date_production) = %s
          AND EXTRACT(YEAR FROM date_production) = %s
        GROUP BY DATE(date_production)
    ),
    plan AS (
        SELECT
            DATE(date_plan) AS plan_date,
            SUM(COALESCE(ballast,0) + COALESCE(biomass,0))::numeric AS total_plan
        FROM plan_productions
        WHERE EXTRACT(MONTH FROM date_plan) = %s
          AND EXTRACT(YEAR FROM date_plan) = %s
        GROUP BY DATE(date_plan)
    )
    SELECT
        EXTRACT(DAY FROM ds.left_date)::int AS day,
        ROUND(COALESCE(a.total_tonnage, 0), 2) AS total_tonnage,
        ROUND(COALESCE(p.total_plan, 0), 2)   AS total_plan
    FROM day_series ds
    LEFT JOIN actual a ON ds.left_date = a.prod_date
    LEFT JOIN plan p   ON ds.left_date = p.plan_date
    ORDER BY ds.left_date;
    """

    params = [
        filter_year, filter_month,   # awal bulan
        filter_year, filter_month,   # akhir bulan
        filter_month, filter_year,   # actual
        filter_month, filter_year    # plan
    ]

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params)
        data = cursor.fetchall()

    df = pd.DataFrame(data, columns=['day', 'total_tonnage', 'total_plan'])

    # pastikan numeric
    for col in ['total_tonnage', 'total_plan']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0).round(2)

    # achievement per hari
    df['achievement'] = df.apply(
        lambda r: round((r['total_tonnage'] / r['total_plan'] * 100), 2) if r['total_plan'] > 0 else 0.0,
        axis=1
    )

    # === Grand Total ===
    total_sum = df['total_tonnage'].sum()
    plan_sum  = df['total_plan'].sum()

    grand_total = {
        'total'       : round(total_sum, 2),
        'plan'        : round(plan_sum, 2),
        'achievement' : round((total_sum / plan_sum * 100), 2) if plan_sum > 0 else 0.0,
        'avg_per_day' : round(df['total_tonnage'].mean(skipna=True), 2) if not df.empty else 0.0
    }

    return JsonResponse({
        'x_data'       : df['day'].astype(int).tolist(),   # [1,2,3,...]
        'total_actual' : df['total_tonnage'].astype(float).tolist(),
        'total_plan'   : df['total_plan'].astype(float).tolist(),
        'achievement'  : df['achievement'].astype(float).tolist(),
        'grand_total'  : grand_total
    }, safe=False)

def get_weekly_chart(filter_week):
    query = """
        WITH actual AS (
            SELECT
                DATE(date_production) AS tanggal,
                TO_CHAR(date_production, 'Dy') AS nama_hari,
                SUM(CASE WHEN nama_material = 'Ballast' THEN tonnage ELSE 0 END)::numeric AS ballast,
                SUM(CASE WHEN nama_material = 'Biomass' THEN tonnage ELSE 0 END)::numeric AS biomass
            FROM mine_productions
            WHERE TO_CHAR(date_production, 'IYYY-IW') = %s
            GROUP BY tanggal
        ),
        plan AS (
            SELECT
                DATE(date_plan) AS tanggal,
                TO_CHAR(date_plan, 'Dy') AS nama_hari,
                SUM(COALESCE(ballast,0))::numeric AS ballast_plan,
                SUM(COALESCE(biomass,0))::numeric AS biomass_plan
            FROM plan_productions
            WHERE TO_CHAR(date_plan, 'IYYY-IW') = %s
            GROUP BY tanggal
        )
        SELECT
            COALESCE(a.tanggal, p.tanggal) AS tanggal,
            COALESCE(a.nama_hari, p.nama_hari) AS hari,
            ROUND(COALESCE(a.ballast, 0), 2) AS ballast,
            ROUND(COALESCE(p.ballast_plan, 0), 2) AS ballast_plan,
            ROUND(CASE WHEN p.ballast_plan > 0 THEN (a.ballast * 100.0 / p.ballast_plan)::numeric ELSE 0 END, 2) AS ballast_ach,
            ROUND(COALESCE(a.biomass, 0), 2) AS biomass,
            ROUND(COALESCE(p.biomass_plan, 0), 2) AS biomass_plan,
            ROUND(CASE WHEN p.biomass_plan > 0 THEN (a.biomass * 100.0 / p.biomass_plan)::numeric ELSE 0 END, 2) AS biomass_ach
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
        'ballast', 'ballast_plan', 'ballast_ach',
        'biomass', 'biomass_plan', 'biomass_ach',
    ]

    df = pd.DataFrame(data, columns=columns)

    # pastikan numeric
    for col in ['ballast', 'ballast_plan', 'ballast_ach',
                'biomass', 'biomass_plan', 'biomass_ach']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

    # total per hari (ballast + biomass)
    df['total_actual'] = df['ballast'] + df['biomass']
    df['total_plan']   = df['ballast_plan'] + df['biomass_plan']

    # achievement total per hari
    df['achievement'] = df.apply(
        lambda r: round((r['total_actual'] / r['total_plan'] * 100), 2) if r['total_plan'] > 0 else 0.0,
        axis=1
    )

    # === Grand Total Mingguan ===
    total_sum = df['total_actual'].sum()
    plan_sum  = df['total_plan'].sum()

    grand_total = {
        'total'       : round(total_sum, 2),
        'plan'        : round(plan_sum, 2),
        'achievement' : round((total_sum / plan_sum * 100), 2) if plan_sum > 0 else 0.0,
        'avg_per_day' : round(df['total_actual'].mean(skipna=True), 2) if not df.empty else 0.0
    }

    return JsonResponse({
        'x_data'       : df['hari'].astype(str).tolist(),
        'total_actual' : df['total_actual'].astype(float).tolist(),
        'total_plan'   : df['total_plan'].astype(float).tolist(),
        'achievement'  : df['achievement'].astype(float).tolist(),
        'grand_total'  : grand_total
    }, safe=False)

def get_range_chart(date_start, date_end):
    query = """
        WITH actual AS (
            SELECT
                DATE(date_production) AS tanggal,
                SUM(CASE WHEN nama_material = 'Ballast' THEN tonnage ELSE 0 END)::numeric AS ballast,
                SUM(CASE WHEN nama_material = 'Biomass' THEN tonnage ELSE 0 END)::numeric AS biomass
            FROM mine_productions
            WHERE date_production BETWEEN %s AND %s
            GROUP BY tanggal
        ),
        plan AS (
            SELECT
                DATE(date_plan) AS tanggal,
                SUM(ballast)::numeric AS ballast_plan,
                SUM(biomass)::numeric AS biomass_plan
            FROM plan_productions
            WHERE date_plan BETWEEN %s AND %s
            GROUP BY tanggal
        )
        SELECT
            COALESCE(a.tanggal, p.tanggal) AS tanggal,
            ROUND(COALESCE(a.ballast, 0), 2) AS ballast,
            ROUND(COALESCE(p.ballast_plan, 0), 2) AS ballast_plan,
            ROUND(CASE WHEN p.ballast_plan > 0 THEN (a.ballast * 100.0 / p.ballast_plan)::numeric ELSE 0 END, 2) AS ballast_ach,
            ROUND(COALESCE(a.biomass, 0), 2) AS biomass,
            ROUND(COALESCE(p.biomass_plan, 0), 2) AS biomass_plan,
            ROUND(CASE WHEN p.biomass_plan > 0 THEN (a.biomass * 100.0 / p.biomass_plan)::numeric ELSE 0 END, 2) AS biomass_ach
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
        'ballast', 'ballast_plan', 'ballast_ach',
        'biomass', 'biomass_plan', 'biomass_ach',
    ]

    df = pd.DataFrame(data, columns=columns)

    # Pastikan kolom angka = float
    num_cols = ['ballast', 'ballast_plan', 'biomass', 'biomass_plan']
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(float)

    # Hitung total harian
    df['total_actual'] = df['ballast'] + df['biomass']
    df['total_plan']   = df['ballast_plan'] + df['biomass_plan']

    # Achievement harian
    df['achievement']  = df.apply(
        lambda r: round((r['total_actual'] / r['total_plan'] * 100), 2) if r['total_plan'] > 0 else 0.0,
        axis=1
    )

    # === Grand Total periode ===
    total_sum = df['total_actual'].sum()
    plan_sum  = df['total_plan'].sum()

    grand_total = {
        'total'       : round(total_sum, 2),
        'plan'        : round(plan_sum, 2),
        'achievement' : round((total_sum / plan_sum * 100), 2) if plan_sum > 0 else 0.0,
        'avg_per_day' : round(df['total_actual'].mean(skipna=True), 2) if not df.empty else 0.0
    }

    return JsonResponse({
        'x_data'       : df['tanggal'].astype(str).tolist(),
        'total_actual' : df['total_actual'].tolist(),
        'total_plan'   : df['total_plan'].tolist(),
        'achievement'  : df['achievement'].tolist(),
        'grand_total'  : grand_total
    }, safe=False)

def get_yearly_chart(yearly):
    query = """
        WITH actual AS (
            SELECT
                TO_CHAR(date_production, 'YYYY-MM') AS bulan,
                SUM(CASE WHEN nama_material = 'Ballast' THEN tonnage ELSE 0 END)::numeric AS ballast,
                SUM(CASE WHEN nama_material = 'Biomass' THEN tonnage ELSE 0 END)::numeric AS biomass
            FROM mine_productions
            WHERE EXTRACT(YEAR FROM date_production) = %s
            GROUP BY bulan
        ),
        plan AS (
            SELECT
                TO_CHAR(date_plan, 'YYYY-MM') AS bulan,
                SUM(ballast)::numeric AS ballast_plan,
                SUM(biomass)::numeric AS biomass_plan
            FROM plan_productions
            WHERE EXTRACT(YEAR FROM date_plan) = %s
            GROUP BY bulan
        )
        SELECT
            COALESCE(a.bulan, p.bulan) AS bulan,
            ROUND(COALESCE(a.ballast, 0), 2) AS ballast,
            ROUND(COALESCE(p.ballast_plan, 0), 2) AS ballast_plan,
            ROUND(CASE WHEN p.ballast_plan > 0 THEN (a.ballast * 100.0 / p.ballast_plan)::numeric ELSE 0 END, 2) AS ballast_ach,
            ROUND(COALESCE(a.biomass, 0), 2) AS biomass,
            ROUND(COALESCE(p.biomass_plan, 0), 2) AS biomass_plan,
            ROUND(CASE WHEN p.biomass_plan > 0 THEN (a.biomass * 100.0 / p.biomass_plan)::numeric ELSE 0 END, 2) AS biomass_ach
        FROM actual a
        FULL OUTER JOIN plan p ON a.bulan = p.bulan
        ORDER BY bulan;
    """

    params = [yearly, yearly]

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params)
        data = cursor.fetchall()

    columns = [
        'bulan',
        'ballast', 'ballast_plan', 'ballast_ach',
        'biomass', 'biomass_plan', 'biomass_ach',
    ]

    df = pd.DataFrame(data, columns=columns)

    # Pastikan semua angka jadi float
    num_cols = ['ballast', 'ballast_plan', 'biomass', 'biomass_plan']
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(float)

    # Hitung total bulanan
    df['total_actual'] = df['ballast'] + df['biomass']
    df['total_plan']   = df['ballast_plan'] + df['biomass_plan']

    # Achievement per bulan
    df['achievement'] = df.apply(
        lambda r: round((r['total_actual'] / r['total_plan'] * 100), 2) if r['total_plan'] > 0 else 0.0,
        axis=1
    )

    # Label bulan singkat (contoh: Jan 25)
    x_data = df['bulan'].apply(lambda x: datetime.strptime(x, '%Y-%m').strftime('%b %y')).tolist()

    # === Grand Total tahun ===
    total_sum = df['total_actual'].sum()
    plan_sum  = df['total_plan'].sum()
    grand_total = {
        'total'       : round(total_sum, 2),
        'plan'        : round(plan_sum, 2),
        'achievement' : round((total_sum / plan_sum * 100), 2) if plan_sum > 0 else 0.0,
        'avg_per_month': round(df['total_actual'].mean(skipna=True), 2) if not df.empty else 0.0
    }

    return JsonResponse({
        'x_data'       : x_data,  # ['Jan 25', 'Feb 25', ...]
        'total_actual' : df['total_actual'].tolist(),
        'total_plan'   : df['total_plan'].tolist(),
        'achievement'  : df['achievement'].tolist(),
        'grand_total'  : grand_total
    }, safe=False)




