# views.py
import logging
from django.http import JsonResponse
from django.db import connections
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
def get_chart_detail_ore(request):
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
                SUM(CASE WHEN mp.nama_material = 'LIM' THEN mp.tonnage ELSE 0 END)::numeric AS lim,
                SUM(CASE WHEN mp.nama_material = 'SAP' THEN mp.tonnage ELSE 0 END)::numeric AS sap
            FROM mine_productions mp
            WHERE mp.date_production = %s::date
            GROUP BY LPAD(t_load::text, 2, '0')
        ),
        plan_per_hour AS (
            SELECT
                SUM(COALESCE(lim,0) + COALESCE(sap,0))::numeric / 22 AS plan_data
            FROM plan_productions
            WHERE date_plan = %s::date
        )
        SELECT
            hs.hour_label AS id,
            hs.left_time,
            COALESCE(agg.lim, 0) AS lim,
            COALESCE(agg.sap, 0) AS sap,
            COALESCE(agg.lim, 0) + COALESCE(agg.sap, 0) AS total,
            p.plan_data
        FROM hour_series hs
        LEFT JOIN agg_data agg ON hs.left_time = agg.t_load_time
        CROSS JOIN plan_per_hour p
        ORDER BY hs.sort_order;
    """

    params = [filter_date, filter_date]

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params)
        data = cursor.fetchall()

    df = pd.DataFrame(data, columns=['id', 'left_time', 'lim', 'sap', 'total', 'plan_data'])

    for col in ['lim', 'sap', 'total', 'plan_data']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

    df['achievement'] = df.apply(
        lambda r: round((r['total'] / r['plan_data'] * 100), 2) if r['plan_data'] > 0 else 0.0,
        axis=1
    )

    # === Grand Total per tanggal ===
    grand_total = {
        'lim'   : round(df['lim'].sum(), 2),
        'sap'   : round(df['sap'].sum(), 2),
        'total' : round(df['total'].sum(), 2),
        'plan'  : round(df['plan_data'].sum(), 2),  # sum dulu, baru round
        'achievement': round((df['total'].sum() / df['plan_data'].sum() * 100), 2) if df['plan_data'].sum() > 0 else 0.0,
        'avg': round(df['total'].mean(), 2)
    }

    return JsonResponse({
        'x_data'       : df['left_time'].tolist(),
        'lim_actual'   : df['lim'].tolist(),
        'sap_actual'   : df['sap'].tolist(),
        'total_actual' : df['total'].tolist(),
        'total_plan'   : df['plan_data'].tolist(),
        'achievement'  : df['achievement'].tolist(),
        'grand_total'  : grand_total,
    }, safe=False)

def get_monthly_detail_chart(filter_year, filter_month):
    query = """
        WITH day_series AS (
            SELECT generate_series(
                make_date(%s, %s, 1), 
                (make_date(%s, %s, 1) + interval '1 month - 1 day')::date,
                interval '1 day'
            )::date AS left_date
        ),
        agg_data AS (
            SELECT 
                DATE(date_production) AS prod_date,
                SUM(CASE WHEN nama_material = 'LIM' THEN tonnage ELSE 0 END)::numeric AS lim,
                SUM(CASE WHEN nama_material = 'SAP' THEN tonnage ELSE 0 END)::numeric AS sap,
                SUM(CASE WHEN nama_material IN ('LGLO','MGLO','HGLO','MWS','LGSO','MGSO','HGSO') 
                        THEN tonnage ELSE 0 END)::numeric AS ore,
                SUM(tonnage)::numeric AS total
            FROM mine_productions
            WHERE EXTRACT(MONTH FROM date_production) = %s
            AND EXTRACT(YEAR  FROM date_production) = %s
            GROUP BY DATE(date_production)
        ),
        plan_data AS (
            SELECT
                DATE(date_plan) AS plan_date,
                SUM(COALESCE(lim,0))::numeric AS plan_lim,
                SUM(COALESCE(sap,0))::numeric AS plan_sap,
                SUM(
                    COALESCE(lglo,0)+COALESCE(mglo,0)+COALESCE(hglo,0)+COALESCE(mws,0)+
                    COALESCE(lgso,0)+COALESCE(mgso,0)+COALESCE(hgso,0)+
                    COALESCE(lim,0)+COALESCE(sap,0)+
                    COALESCE(quarry,0)+COALESCE(ballast,0)+COALESCE(biomass,0)
                )::numeric AS plan_total
            FROM plan_productions
            WHERE EXTRACT(MONTH FROM date_plan) = %s
            AND EXTRACT(YEAR  FROM date_plan) = %s
            GROUP BY DATE(date_plan)
        )
        SELECT
            EXTRACT(DAY FROM ds.left_date)::int AS id,  -- hanya ambil hari
            COALESCE(agg.lim,0)   AS lim,
            COALESCE(agg.sap,0)   AS sap,
            COALESCE(agg.total,0) AS total,
            COALESCE(pl.plan_total,0) AS plan_data
        FROM day_series ds
        LEFT JOIN agg_data agg ON ds.left_date = agg.prod_date
        LEFT JOIN plan_data pl ON ds.left_date = pl.plan_date
        WHERE ds.left_date <= (make_date(%s, %s, 1) + interval '1 month - 1 day')::date
        ORDER BY ds.left_date;

 """

    params = [
        filter_year, filter_month,   # make_date awal
        filter_year, filter_month,   # make_date akhir
        filter_month, filter_year,   # agg_data
        filter_month, filter_year,   # plan_data
        filter_year, filter_month    # batas akhir
    ]

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params)
        data = cursor.fetchall()

    df = pd.DataFrame(data, columns=['id','lim','sap','total','plan_data'])

    # pastikan numeric
    for col in ['lim', 'sap', 'total', 'plan_data']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

    # achievement harian
    df['achievement'] = df.apply(
        lambda r: round((r['total'] / r['plan_data'] * 100), 2) if r['plan_data'] > 0 else 0.0,
        axis=1
    )

    # === Grand Total ===
    total_sum = df['total'].sum()
    plan_sum  = df['plan_data'].sum()

    # === Grand Total untuk bulan ===
    grand_total = {
        'lim'           : round(df['lim'].sum(), 2),
        'sap'           : round(df['sap'].sum(), 2),
        'total'         : round(df['total'].sum(), 2),
        'plan'          : round(df['plan_data'].sum(), 2),
        'achievement'   : round((total_sum / plan_sum * 100), 2) if plan_sum > 0 else 0.0,
        'avg'           : round(df['total'].mean(skipna=True), 2) if not df.empty else 0.0
    }

    return JsonResponse({
        'x_data'       : df['id'].tolist(),          # hari saja
        'lim_actual'   : df['lim'].tolist(),
        'sap_actual'   : df['sap'].tolist(),
        'total_tonnage' : df['total'].tolist(),
        'total_plan'   : df['plan_data'].tolist(),
        'achievement'  : df['achievement'].tolist(),
        'grand_total'  : grand_total,
    }, safe=False)

def get_weekly_detail_chart(filter_week):
    # iso_week_str = f"{iso_year}-{str(iso_week).zfill(2)}"  # pastikan format IYYY-IW: "2025-04"
    query = """
        WITH actual AS (
            SELECT
                DATE(date_production) AS tanggal,
                TO_CHAR(date_production, 'FMDy') AS nama_hari,
                SUM(CASE WHEN nama_material = 'LGLO' THEN tonnage ELSE 0 END)::numeric AS lglo,
                SUM(CASE WHEN nama_material = 'MGLO' THEN tonnage ELSE 0 END)::numeric AS mglo,
                SUM(CASE WHEN nama_material = 'HGLO' THEN tonnage ELSE 0 END)::numeric AS hglo,
                SUM(CASE WHEN nama_material = 'MWS' THEN tonnage ELSE 0 END)::numeric AS mws,
                SUM(CASE WHEN nama_material = 'LGSO' THEN tonnage ELSE 0 END)::numeric AS lgso,
                SUM(CASE WHEN nama_material = 'MGSO' THEN tonnage ELSE 0 END)::numeric AS mgso,
                SUM(CASE WHEN nama_material = 'HGSO' THEN tonnage ELSE 0 END)::numeric AS hgso,
                SUM(CASE WHEN nama_material = 'LIM' THEN tonnage ELSE 0 END)::numeric AS lim,
                SUM(CASE WHEN nama_material = 'SAP' THEN tonnage ELSE 0 END)::numeric AS sap
            FROM mine_productions
            WHERE TO_CHAR(date_production, 'IYYY-IW') = %s
            GROUP BY tanggal
        ),
        plan AS (
            SELECT
                DATE(date_plan) AS tanggal,
                TO_CHAR(date_plan, 'FMDy') AS nama_hari,
                SUM(lglo)::numeric AS lglo_plan,
                SUM(mglo)::numeric AS mglo_plan,
                SUM(hglo)::numeric AS hglo_plan,
                SUM(mws)::numeric AS mws_plan,
                SUM(lgso)::numeric AS lgso_plan,
                SUM(mgso)::numeric AS mgso_plan,
                SUM(hgso)::numeric AS hgso_plan,
                SUM(lim)::numeric AS lim_plan,
                SUM(sap)::numeric AS sap_plan
            FROM plan_productions
            WHERE TO_CHAR(date_plan, 'IYYY-IW') = %s
            GROUP BY tanggal
        )
        SELECT
            COALESCE(a.tanggal, p.tanggal) AS tanggal,
            COALESCE(a.nama_hari, p.nama_hari) AS hari,
            ROUND(COALESCE(a.lglo, 0), 2) AS lglo,
            ROUND(COALESCE(p.lglo_plan, 0), 2) AS lglo_plan,
            ROUND(CASE WHEN p.lglo_plan > 0 THEN (a.lglo * 100.0 / p.lglo_plan)::numeric ELSE 0 END, 2) AS lglo_ach,
            ROUND(COALESCE(a.mglo, 0), 2) AS mglo,
            ROUND(COALESCE(p.mglo_plan, 0), 2) AS mglo_plan,
            ROUND(CASE WHEN p.mglo_plan > 0 THEN (a.mglo * 100.0 / p.mglo_plan)::numeric ELSE 0 END, 2) AS mglo_ach,
            ROUND(COALESCE(a.hglo, 0), 2) AS hglo,
            ROUND(COALESCE(p.hglo_plan, 0), 2) AS hglo_plan,
            ROUND(CASE WHEN p.hglo_plan > 0 THEN (a.hglo * 100.0 / p.hglo_plan)::numeric ELSE 0 END, 2) AS hglo_ach,
            ROUND(COALESCE(a.mws, 0), 2) AS mws,
            ROUND(COALESCE(p.mws_plan, 0), 2) AS mws_plan,
            ROUND(CASE WHEN p.mws_plan > 0 THEN (a.mws * 100.0 / p.mws_plan)::numeric ELSE 0 END, 2) AS mws_ach,
            ROUND(COALESCE(a.lgso, 0), 2) AS lgso,
            ROUND(COALESCE(p.lgso_plan, 0), 2) AS lgso_plan,
            ROUND(CASE WHEN p.lgso_plan > 0 THEN (a.lgso * 100.0 / p.lgso_plan)::numeric ELSE 0 END, 2) AS lgso_ach,
            ROUND(COALESCE(a.mgso, 0), 2) AS mgso,
            ROUND(COALESCE(p.mgso_plan, 0), 2) AS mgso_plan,
            ROUND(CASE WHEN p.mgso_plan > 0 THEN (a.mgso * 100.0 / p.mgso_plan)::numeric ELSE 0 END, 2) AS mgso_ach,
            ROUND(COALESCE(a.hgso, 0), 2) AS hgso,
            ROUND(COALESCE(p.hgso_plan, 0), 2) AS hgso_plan,
            ROUND(CASE WHEN p.hgso_plan > 0 THEN (a.hgso * 100.0 / p.hgso_plan)::numeric ELSE 0 END, 2) AS hgso_ach,
            ROUND(COALESCE(a.lim, 0), 2) AS lim,
            ROUND(COALESCE(p.lim_plan, 0), 2) AS lim_plan,
            ROUND(CASE WHEN p.lim_plan > 0 THEN (a.lim * 100.0 / p.lim_plan)::numeric ELSE 0 END, 2) AS lim_ach,
            ROUND(COALESCE(a.sap, 0), 2) AS sap,
            ROUND(COALESCE(p.sap_plan, 0), 2) AS sap_plan,
            ROUND(CASE WHEN p.sap_plan > 0 THEN (a.sap * 100.0 / p.sap_plan)::numeric ELSE 0 END, 2) AS sap_ach
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
        'lglo', 'lglo_plan', 'lglo_ach',
        'mglo', 'mglo_plan', 'mglo_ach',
        'hglo', 'hglo_plan', 'hglo_ach',
        'mws',  'mws_plan',  'mws_ach',
        'lgso', 'lgso_plan', 'lgso_ach',
        'mgso', 'mgso_plan', 'mgso_ach',
        'hgso', 'hgso_plan', 'hgso_ach',
        'lim', 'lim_plan', 'lim_ach',
        'sap', 'sap_plan', 'sap_ach'
    ]

    df = pd.DataFrame(data, columns=columns)

    lim_cols = ['lglo', 'mglo', 'hglo','lim']
    sap_cols = ['lgso', 'mgso', 'hgso','sap']
    lim_plan_cols = [f + '_plan' for f in lim_cols]
    sap_plan_cols = [f + '_plan' for f in sap_cols]

    # Konversi kolom ke numerik (handle string atau null)
    for col in lim_cols + sap_cols + lim_plan_cols + sap_plan_cols :
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(float)

    df['limonite']       = df[lim_cols].sum(axis=1)
    df['limonite_plan']  = df[lim_plan_cols].sum(axis=1)
    df['saprolite']      = df[sap_cols].sum(axis=1)
    df['saprolite_plan'] = df[sap_plan_cols].sum(axis=1)

    df['total_actual'] = df['limonite'] + df['saprolite']
    df['total_plan']   = df['limonite_plan'] + df['saprolite_plan']
    df['achievement']  = df.apply(lambda row: round((row['total_actual'] / row['total_plan'] * 100), 2) if row['total_plan'] > 0 else 0, axis=1)

    df['limonite_ach']  = df.apply(lambda r: round((r['limonite'] / r['limonite_plan'] * 100), 2) if r['limonite_plan'] > 0 else 0, axis=1)
    df['saprolite_ach'] = df.apply(lambda r: round((r['saprolite'] / r['saprolite_plan'] * 100), 2) if r['saprolite_plan'] > 0 else 0, axis=1)

    # === Grand Total Mingguan ===
    total_sum       = df['total_actual'].sum()
    total_plan_sum  = df['total_plan'].sum()
    limonite_sum    = df['limonite'].sum()
    limonite_plan   = df['limonite_plan'].sum()
    saprolite_sum   = df['saprolite'].sum()
    saprolite_plan  = df['saprolite_plan'].sum()

    grand_total = {
        'lim'            : round(limonite_sum, 2),
        'limonite_plan'  : round(limonite_plan, 2),
        'limonite_ach'   : round((limonite_sum / limonite_plan * 100), 2) if limonite_plan > 0 else 0.0,
        'saprolite'      : round(saprolite_sum, 2),
        'sap'            : round(saprolite_plan, 2),
        'saprolite_ach'  : round((saprolite_sum / saprolite_plan * 100), 2) if saprolite_plan > 0 else 0.0,
        'total'          : round(total_sum, 2),
        'plan'           : round(total_plan_sum, 2),
        'achievement'    : round((total_sum / total_plan_sum * 100), 2) if total_plan_sum > 0 else 0.0,
        'avg'            : round(df['total_actual'].mean(skipna=True), 2) if not df.empty else 0.0
    }


    return JsonResponse({
        'x_data'       : df['hari'].astype(str).tolist(),
        'total_actual' : df['total_actual'].astype(float).tolist(),
        'total_plan'   : df['total_plan'].astype(float).tolist(),
        'achievement'  : df['achievement'].astype(float).tolist(),
        'grand_total'  : grand_total
    }, safe=False)

def get_range_detail_chart(date_start, date_end):
    query = """
        WITH actual AS (
            SELECT
                DATE(date_production) AS tanggal,
                SUM(CASE WHEN nama_material = 'LGLO' THEN tonnage ELSE 0 END)::numeric AS lglo,
                SUM(CASE WHEN nama_material = 'MGLO' THEN tonnage ELSE 0 END)::numeric AS mglo,
                SUM(CASE WHEN nama_material = 'HGLO' THEN tonnage ELSE 0 END)::numeric AS hglo,
                SUM(CASE WHEN nama_material = 'MWS' THEN tonnage ELSE 0 END)::numeric AS mws,
                SUM(CASE WHEN nama_material = 'LGSO' THEN tonnage ELSE 0 END)::numeric AS lgso,
                SUM(CASE WHEN nama_material = 'MGSO' THEN tonnage ELSE 0 END)::numeric AS mgso,
                SUM(CASE WHEN nama_material = 'HGSO' THEN tonnage ELSE 0 END)::numeric AS hgso,
                SUM(CASE WHEN nama_material = 'LIM' THEN tonnage ELSE 0 END)::numeric AS lim,
                SUM(CASE WHEN nama_material = 'SAP' THEN tonnage ELSE 0 END)::numeric AS sap
            FROM mine_productions
            WHERE date_production BETWEEN %s AND %s
            GROUP BY tanggal
        ),
        plan AS (
            SELECT
                DATE(date_plan) AS tanggal,
                SUM(lglo)::numeric AS lglo_plan,
                SUM(mglo)::numeric AS mglo_plan,
                SUM(hglo)::numeric AS hglo_plan,
                SUM(mws)::numeric AS mws_plan,
                SUM(lgso)::numeric AS lgso_plan,
                SUM(mgso)::numeric AS mgso_plan,
                SUM(hgso)::numeric AS hgso_plan,
                SUM(lim)::numeric AS lim_plan,
                SUM(sap)::numeric AS sap_plan
            FROM plan_productions
            WHERE date_plan BETWEEN %s AND %s
            GROUP BY tanggal
        )
        SELECT
            COALESCE(a.tanggal, p.tanggal) AS tanggal,
            ROUND(COALESCE(a.lglo, 0), 2) AS lglo,
            ROUND(COALESCE(p.lglo_plan, 0), 2) AS lglo_plan,
            ROUND(CASE WHEN p.lglo_plan > 0 THEN (a.lglo * 100.0 / p.lglo_plan)::numeric ELSE 0 END, 2) AS lglo_ach,
            ROUND(COALESCE(a.mglo, 0), 2) AS mglo,
            ROUND(COALESCE(p.mglo_plan, 0), 2) AS mglo_plan,
            ROUND(CASE WHEN p.mglo_plan > 0 THEN (a.mglo * 100.0 / p.mglo_plan)::numeric ELSE 0 END, 2) AS mglo_ach,
            ROUND(COALESCE(a.hglo, 0), 2) AS hglo,
            ROUND(COALESCE(p.hglo_plan, 0), 2) AS hglo_plan,
            ROUND(CASE WHEN p.hglo_plan > 0 THEN (a.hglo * 100.0 / p.hglo_plan)::numeric ELSE 0 END, 2) AS hglo_ach,
            ROUND(COALESCE(a.mws, 0), 2) AS mws,
            ROUND(COALESCE(p.mws_plan, 0), 2) AS mws_plan,
            ROUND(CASE WHEN p.mws_plan > 0 THEN (a.mws * 100.0 / p.mws_plan)::numeric ELSE 0 END, 2) AS mws_ach,
            ROUND(COALESCE(a.lgso, 0), 2) AS lgso,
            ROUND(COALESCE(p.lgso_plan, 0), 2) AS lgso_plan,
            ROUND(CASE WHEN p.lgso_plan > 0 THEN (a.lgso * 100.0 / p.lgso_plan)::numeric ELSE 0 END, 2) AS lgso_ach,
            ROUND(COALESCE(a.mgso, 0), 2) AS mgso,
            ROUND(COALESCE(p.mgso_plan, 0), 2) AS mgso_plan,
            ROUND(CASE WHEN p.mgso_plan > 0 THEN (a.mgso * 100.0 / p.mgso_plan)::numeric ELSE 0 END, 2) AS mgso_ach,
            ROUND(COALESCE(a.hgso, 0), 2) AS hgso,
            ROUND(COALESCE(p.hgso_plan, 0), 2) AS hgso_plan,
            ROUND(CASE WHEN p.hgso_plan > 0 THEN (a.hgso * 100.0 / p.hgso_plan)::numeric ELSE 0 END, 2) AS hgso_ach,
            ROUND(COALESCE(a.lim, 0), 2) AS lim,
            ROUND(COALESCE(p.lim_plan, 0), 2) AS lim_plan,
            ROUND(CASE WHEN p.lim_plan > 0 THEN (a.lim * 100.0 / p.lim_plan)::numeric ELSE 0 END, 2) AS lim_ach,
            ROUND(COALESCE(a.sap, 0), 2) AS sap,
            ROUND(COALESCE(p.sap_plan, 0), 2) AS sap_plan,
            ROUND(CASE WHEN p.sap_plan > 0 THEN (a.sap * 100.0 / p.sap_plan)::numeric ELSE 0 END, 2) AS sap_ach
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
        'lglo', 'lglo_plan', 'lglo_ach',
        'mglo', 'mglo_plan', 'mglo_ach',
        'hglo', 'hglo_plan', 'hglo_ach',
        'mws',  'mws_plan',  'mws_ach',
        'lgso', 'lgso_plan', 'lgso_ach',
        'mgso', 'mgso_plan', 'mgso_ach',
        'hgso', 'hgso_plan', 'hgso_ach',
        'lim', 'lim_plan', 'lim_ach',
        'sap', 'sap_plan', 'sap_ach'
    ]

    df = pd.DataFrame(data, columns=columns)

    lim_cols = ['lglo', 'mglo', 'hglo','lim']
    sap_cols = ['lgso', 'mgso', 'hgso','sap']
    lim_plan_cols = [f + '_plan' for f in lim_cols]
    sap_plan_cols = [f + '_plan' for f in sap_cols]


    # Konversi kolom ke numerik (handle string atau null)
    for col in lim_cols + sap_cols + lim_plan_cols + sap_plan_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(float)

    df['limonite']       = df[lim_cols].sum(axis=1)
    df['limonite_plan']  = df[lim_plan_cols].sum(axis=1)
    df['saprolite']      = df[sap_cols].sum(axis=1)
    df['saprolite_plan'] = df[sap_plan_cols].sum(axis=1)

    df['total_actual'] = df['limonite'] + df['saprolite']
    df['total_plan']   = df['limonite_plan'] + df['saprolite_plan']
    df['achievement']  = df.apply(lambda row: round((row['total_actual'] / row['total_plan'] * 100), 2) if row['total_plan'] > 0 else 0, axis=1)

    df['limonite_ach']  = df.apply(lambda r: round((r['limonite'] / r['limonite_plan'] * 100), 2) if r['limonite_plan'] > 0 else 0, axis=1)
    df['saprolite_ach'] = df.apply(lambda r: round((r['saprolite'] / r['saprolite_plan'] * 100), 2) if r['saprolite_plan'] > 0 else 0, axis=1)

     # === Grand Total Mingguan ===
    total_sum       = df['total_actual'].sum()
    total_plan_sum  = df['total_plan'].sum()
    limonite_sum    = df['limonite'].sum()
    limonite_plan   = df['limonite_plan'].sum()
    saprolite_sum   = df['saprolite'].sum()
    saprolite_plan  = df['saprolite_plan'].sum()

    grand_total = {
        'lim'            : round(limonite_sum, 2),
        'limonite_plan'  : round(limonite_plan, 2),
        'limonite_ach'   : round((limonite_sum / limonite_plan * 100), 2) if limonite_plan > 0 else 0.0,
        'saprolite'      : round(saprolite_sum, 2),
        'sap'            : round(saprolite_plan, 2),
        'saprolite_ach'  : round((saprolite_sum / saprolite_plan * 100), 2) if saprolite_plan > 0 else 0.0,
        'total'          : round(total_sum, 2),
        'plan'           : round(total_plan_sum, 2),
        'achievement'    : round((total_sum / total_plan_sum * 100), 2) if total_plan_sum > 0 else 0.0,
        'avg'            : round(df['total_actual'].mean(skipna=True), 2) if not df.empty else 0.0
    }

    return JsonResponse({
        'x_data'        : df['tanggal'].astype(str).tolist(),
        'total_actual' : df['total_actual'].astype(float).tolist(),
        'total_plan'   : df['total_plan'].astype(float).tolist(),
        'achievement'  : df['achievement'].astype(float).tolist(),
        'grand_total'  : grand_total
    }, safe=False)

def get_yearly_chart(yearly):
    query = """
        WITH actual AS (
            SELECT
                TO_CHAR(date_production, 'YYYY-MM') AS bulan,
                SUM(CASE WHEN nama_material = 'LGLO' THEN tonnage ELSE 0 END)::numeric AS lglo,
                SUM(CASE WHEN nama_material = 'MGLO' THEN tonnage ELSE 0 END)::numeric AS mglo,
                SUM(CASE WHEN nama_material = 'HGLO' THEN tonnage ELSE 0 END)::numeric AS hglo,
                SUM(CASE WHEN nama_material = 'MWS' THEN tonnage ELSE 0 END)::numeric AS mws,
                SUM(CASE WHEN nama_material = 'LGSO' THEN tonnage ELSE 0 END)::numeric AS lgso,
                SUM(CASE WHEN nama_material = 'MGSO' THEN tonnage ELSE 0 END)::numeric AS mgso,
                SUM(CASE WHEN nama_material = 'HGSO' THEN tonnage ELSE 0 END)::numeric AS hgso,
                SUM(CASE WHEN nama_material = 'LIM' THEN tonnage ELSE 0 END)::numeric AS lim,
                SUM(CASE WHEN nama_material = 'SAP' THEN tonnage ELSE 0 END)::numeric AS sap
            FROM mine_productions
            WHERE EXTRACT(YEAR FROM date_production) = %s
            GROUP BY bulan
        ),
        plan AS (
            SELECT
                TO_CHAR(date_plan, 'YYYY-MM') AS bulan,
                SUM(lglo)::numeric AS lglo_plan,
                SUM(mglo)::numeric AS mglo_plan,
                SUM(hglo)::numeric AS hglo_plan,
                SUM(mws)::numeric AS mws_plan,
                SUM(lgso)::numeric AS lgso_plan,
                SUM(mgso)::numeric AS mgso_plan,
                SUM(hgso)::numeric AS hgso_plan,
                SUM(lim)::numeric AS lim_plan,
                SUM(sap)::numeric AS sap_plan
            FROM plan_productions
            WHERE EXTRACT(YEAR FROM date_plan) = %s
            GROUP BY bulan
        )
        SELECT
            COALESCE(a.bulan, p.bulan) AS bulan,
            ROUND(COALESCE(a.lglo, 0), 2) AS lglo,
            ROUND(COALESCE(p.lglo_plan, 0), 2) AS lglo_plan,
            ROUND(CASE WHEN p.lglo_plan > 0 THEN (a.lglo * 100.0 / p.lglo_plan)::numeric ELSE 0 END, 2) AS lglo_ach,
            ROUND(COALESCE(a.mglo, 0), 2) AS mglo,
            ROUND(COALESCE(p.mglo_plan, 0), 2) AS mglo_plan,
            ROUND(CASE WHEN p.mglo_plan > 0 THEN (a.mglo * 100.0 / p.mglo_plan)::numeric ELSE 0 END, 2) AS mglo_ach,
            ROUND(COALESCE(a.hglo, 0), 2) AS hglo,
            ROUND(COALESCE(p.hglo_plan, 0), 2) AS hglo_plan,
            ROUND(CASE WHEN p.hglo_plan > 0 THEN (a.hglo * 100.0 / p.hglo_plan)::numeric ELSE 0 END, 2) AS hglo_ach,
            ROUND(COALESCE(a.mws, 0), 2) AS mws,
            ROUND(COALESCE(p.mws_plan, 0), 2) AS mws_plan,
            ROUND(CASE WHEN p.mws_plan > 0 THEN (a.mws * 100.0 / p.mws_plan)::numeric ELSE 0 END, 2) AS mws_ach,
            ROUND(COALESCE(a.lgso, 0), 2) AS lgso,
            ROUND(COALESCE(p.lgso_plan, 0), 2) AS lgso_plan,
            ROUND(CASE WHEN p.lgso_plan > 0 THEN (a.lgso * 100.0 / p.lgso_plan)::numeric ELSE 0 END, 2) AS lgso_ach,
            ROUND(COALESCE(a.mgso, 0), 2) AS mgso,
            ROUND(COALESCE(p.mgso_plan, 0), 2) AS mgso_plan,
            ROUND(CASE WHEN p.mgso_plan > 0 THEN (a.mgso * 100.0 / p.mgso_plan)::numeric ELSE 0 END, 2) AS mgso_ach,
            ROUND(COALESCE(a.hgso, 0), 2) AS hgso,
            ROUND(COALESCE(p.hgso_plan, 0), 2) AS hgso_plan,
            ROUND(CASE WHEN p.hgso_plan > 0 THEN (a.hgso * 100.0 / p.hgso_plan)::numeric ELSE 0 END, 2) AS hgso_ach,
            ROUND(COALESCE(a.lim, 0), 2) AS lim,
            ROUND(COALESCE(p.lim_plan, 0), 2) AS lim_plan,
            ROUND(CASE WHEN p.lim_plan > 0 THEN (a.lim * 100.0 / p.lim_plan)::numeric ELSE 0 END, 2) AS lim_ach,
            ROUND(COALESCE(a.sap, 0), 2) AS sap,
            ROUND(COALESCE(p.sap_plan, 0), 2) AS sap_plan,
            ROUND(CASE WHEN p.sap_plan > 0 THEN (a.sap * 100.0 / p.sap_plan)::numeric ELSE 0 END, 2) AS sap_ach
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
        'lglo', 'lglo_plan', 'lglo_ach',
        'mglo', 'mglo_plan', 'mglo_ach',
        'hglo', 'hglo_plan', 'hglo_ach',
        'mws',  'mws_plan',  'mws_ach',
        'lgso', 'lgso_plan', 'lgso_ach',
        'mgso', 'mgso_plan', 'mgso_ach',
        'hgso', 'hgso_plan', 'hgso_ach',
        'lim', 'lim_plan', 'lim_ach',
        'sap', 'sap_plan', 'sap_ach'
    ]

    df = pd.DataFrame(data, columns=columns)

    lim_cols = ['lglo', 'mglo', 'hglo','lim']
    sap_cols = ['lgso', 'mgso', 'hgso','sap']
    lim_plan_cols = [f + '_plan' for f in lim_cols]
    sap_plan_cols = [f + '_plan' for f in sap_cols]

    # Konversi kolom ke numerik (handle string atau null)
    for col in lim_cols + sap_cols + lim_plan_cols + sap_plan_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(float)

    df['limonite']       = df[lim_cols].sum(axis=1)
    df['limonite_plan']  = df[lim_plan_cols].sum(axis=1)
    df['saprolite']      = df[sap_cols].sum(axis=1)
    df['saprolite_plan'] = df[sap_plan_cols].sum(axis=1)
    
    df['total_actual'] = df['limonite'] + df['saprolite']
    df['total_plan']   = df['limonite_plan'] + df['saprolite_plan']
    df['achievement']  = df.apply(lambda row: round((row['total_actual'] / row['total_plan'] * 100), 2) if row['total_plan'] > 0 else 0, axis=1)

    df['limonite_ach']  = df.apply(lambda r: round((r['limonite'] / r['limonite_plan'] * 100), 2) if r['limonite_plan'] > 0 else 0, axis=1)
    df['saprolite_ach'] = df.apply(lambda r: round((r['saprolite'] / r['saprolite_plan'] * 100), 2) if r['saprolite_plan'] > 0 else 0, axis=1)

    # === Grand Total Mingguan ===
    total_sum       = df['total_actual'].sum()
    total_plan_sum  = df['total_plan'].sum()
    limonite_sum    = df['limonite'].sum()
    limonite_plan   = df['limonite_plan'].sum()
    saprolite_sum   = df['saprolite'].sum()
    saprolite_plan  = df['saprolite_plan'].sum()

    grand_total = {
        'lim'            : round(limonite_sum, 2),
        'limonite_plan'  : round(limonite_plan, 2),
        'limonite_ach'   : round((limonite_sum / limonite_plan * 100), 2) if limonite_plan > 0 else 0.0,
        'saprolite'      : round(saprolite_sum, 2),
        'sap'            : round(saprolite_plan, 2),
        'saprolite_ach'  : round((saprolite_sum / saprolite_plan * 100), 2) if saprolite_plan > 0 else 0.0,
        'total'          : round(total_sum, 2),
        'plan'           : round(total_plan_sum, 2),
        'achievement'    : round((total_sum / total_plan_sum * 100), 2) if total_plan_sum > 0 else 0.0,
        'avg'            : round(df['total_actual'].mean(skipna=True), 2) if not df.empty else 0.0
    }

    # Define month names
    x_data = df['bulan'].apply(lambda x: datetime.strptime(x, '%Y-%m').strftime('%b %y')).tolist()


    return JsonResponse({
        'x_data'       : x_data,  # Contoh: ['Jan 25', 'Feb 25', ...]
        'total_actual' : df['total_actual'].astype(float).tolist(),
        'total_plan'   : df['total_plan'].astype(float).tolist(),
        'achievement'  : df['achievement'].astype(float).tolist(),
        'grand_total'  : grand_total
    }, safe=False)





