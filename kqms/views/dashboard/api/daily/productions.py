# views.py
import logging
from django.http import JsonResponse
from django.db import connections
import pandas as pd
logger = logging.getLogger(__name__) 
from kqms.utils.db_utils import get_db_vendor

 # Memanggil fungsi utility
db_vendor = get_db_vendor('kqms_db')
import json

def safe_division(numerator, denominator):
    return round(numerator / denominator * 100, 0) if denominator else 0

# For Chart
# def get_daily_detail_productions(request):
#     filter_date  = request.GET.get('filter_date')
#     return get_daily_detail_ore(filter_date)

def get_daily_detail_productions(request):
    filter_date = request.GET.get('filter_date')

    handlers = {
        "ore"      : get_daily_detail_ore,
        "ob"       : get_daily_detail_ob,
        "waste"    : get_daily_detail_waste,
        "quarry"   : get_daily_detail_quarry,
        "top_soil" : get_daily_detail_top_soil,
        "others"   : get_daily_detail_others,
    }

    data = {
        key: func(filter_date)
        for key, func in handlers.items()
    }

    return JsonResponse(data, safe=True)

def get_daily_detail_ore(filter_date):
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

    return {
        'x_data'       : df['left_time'].tolist(),
        'lim_actual'   : df['lim'].tolist(),
        'sap_actual'   : df['sap'].tolist(),
        'total_actual' : df['total'].tolist(),
        'total_plan'   : df['plan_data'].tolist(),
        'achievement'  : df['achievement'].tolist(),
        'grand_total'  : grand_total,
    }



def get_daily_detail_ob(filter_date):
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
                    SUM(CASE WHEN nama_material IN ('OB') THEN tonnage ELSE 0 END)::numeric AS total_tonnage
                FROM mine_productions mp
                WHERE mp.date_production = %s::date
                GROUP BY LPAD(t_load::text, 2, '0')
            ),
            plan_per_hour AS (
                SELECT
                    ROUND(SUM(COALESCE(ob,0))::numeric / 22, 3) AS plan_data
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
    df['achievement']   = df.apply( lambda row: round(float(row['total']) / float(row['plan_data']) * 100, 2) if float(row['plan_data']) > 0 else 0,axis=1)

    # === Grand Total per tanggal ===
    grand_total = {
        'total' : round(df['total'].sum(), 2),
        'plan'  : round(df['plan_data'].sum(), 2),  # sum dulu, baru round
        'achievement': round((df['total'].sum() / df['plan_data'].sum() * 100), 2) if df['plan_data'].sum() > 0 else 0.0,
        'avg': round(df['total'].mean(), 2)
    }


    return {
        'x_data'       : df['left_time'].tolist(),  # ini label jam (misal: "01:00", "02:00", ...)
        'total_actual' : df['total'].tolist(),
        'total_plan'   : df['plan_data'].tolist(),
        'achievement'  : df['achievement'].tolist(),
        'grand_total'  : grand_total
    }

def get_daily_detail_quarry(filter_date):
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
                        SUM(CASE WHEN nama_material IN ('Quarry') THEN tonnage ELSE 0 END)::numeric AS total_tonnage
                    FROM mine_productions mp
                    WHERE mp.date_production = %s::date
                    GROUP BY LPAD(t_load::text, 2, '0')
                ),
                plan_per_hour AS (
                    SELECT
                        ROUND(SUM(COALESCE(quarry,0))::numeric / 22, 3) AS plan_data
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
    df['total']       = pd.to_numeric(df['total'], errors='coerce').fillna(0.0).round(2)
    df['plan_data']   = pd.to_numeric(df['plan_data'], errors='coerce').fillna(0.0)
    df['achievement'] = df.apply( lambda row: round(float(row['total']) / float(row['plan_data']) * 100, 2) if float(row['plan_data']) > 0 else 0,axis=1)

    # === Grand Total per tanggal ===
    grand_total = {
        'total' : round(df['total'].sum(), 2),
        'plan'  : round(df['plan_data'].sum(), 2),  # sum dulu, baru round
        'achievement': round((df['total'].sum() / df['plan_data'].sum() * 100), 2) if df['plan_data'].sum() > 0 else 0.0,
        'avg': round(df['total'].mean(), 2)
    }


    return {
        'x_data'        : df['left_time'].tolist(),  # ini label jam (misal: "01:00", "02:00", ...)
        'total_actual'  : df['total'].tolist(),
        'total_plan'    : df['plan_data'].tolist(),
        'achievement'   : df['achievement'].tolist(),
        'grand_total'   : grand_total
    }

def get_daily_detail_top_soil(filter_date):
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
                    SUM(CASE WHEN nama_material IN ('Top Soil') THEN tonnage ELSE 0 END)::numeric AS total_tonnage
                FROM mine_productions mp
                WHERE mp.date_production = %s::date
                GROUP BY LPAD(t_load::text, 2, '0')
            ),
            plan_per_hour AS (
                SELECT
                    ROUND(SUM(COALESCE(topsoil,0))::numeric / 22, 3) AS plan_data
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
    df['total'] = pd.to_numeric(df['total'], errors='coerce').fillna(0.0).round(2)
    df['plan_data'] = pd.to_numeric(df['plan_data'], errors='coerce').fillna(0.0)
    df['achievement'] = df.apply( lambda row: round(float(row['total']) / float(row['plan_data']) * 100, 2) if float(row['plan_data']) > 0 else 0,axis=1)

    # === Grand Total per tanggal ===
    grand_total = {
        'total' : round(df['total'].sum(), 2),
        'plan'  : round(df['plan_data'].sum(), 2),  # sum dulu, baru round
        'achievement' : round((df['total'].sum() / df['plan_data'].sum() * 100), 2) if df['plan_data'].sum() > 0 else 0.0,
        'avg': round(df['total'].mean(), 2)
    }

    return {
        'x_data'        : df['left_time'].tolist(),  # ini label jam (misal: "01:00", "02:00", ...)
        'total_actual'  : df['total'].tolist(),
        'total_plan'    : df['plan_data'].tolist(),
        'achievement'   : df['achievement'].tolist(),
        'grand_total'   : grand_total,
    }

def get_daily_detail_waste(filter_date):
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
                    SUM(CASE WHEN nama_material IN ('Waste') THEN tonnage ELSE 0 END)::numeric AS total_tonnage
                FROM mine_productions mp
                WHERE mp.date_production = %s::date
                GROUP BY LPAD(t_load::text, 2, '0')
            ),
            plan_per_hour AS (
                SELECT
                    ROUND(SUM(COALESCE(waste,0))::numeric / 22, 3) AS plan_data
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
    df['total'] = pd.to_numeric(df['total'], errors='coerce').fillna(0.0).round(2)
    df['plan_data'] = pd.to_numeric(df['plan_data'], errors='coerce').fillna(0.0)
    df['achievement'] = df.apply( lambda row: round(float(row['total']) / float(row['plan_data']) * 100, 2) if float(row['plan_data']) > 0 else 0,axis=1)

    # === Grand Total per tanggal ===
    grand_total = {
        'total' : round(df['total'].sum(), 2),
        'plan'  : round(df['plan_data'].sum(), 2),  # sum dulu, baru round
        'achievement': round((df['total'].sum() / df['plan_data'].sum() * 100), 2) if df['plan_data'].sum() > 0 else 0.0,
        'avg': round(df['total'].mean(), 2)
    }

    return {
        'x_data'      : df['left_time'].tolist(),
        'total_actual': df['total'].tolist(),
        'total_plan'  : df['plan_data'].tolist(),
        'achievement' : df['achievement'].tolist(),
        'grand_total'  : grand_total,
    }

def get_daily_detail_others(filter_date):
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

    return {
        'x_data'        : df['left_time'].tolist(),
        'total_actual'  : df['total'].tolist(),
        'total_plan'    : df['plan_data'].tolist(),
        'achievement'   : df['achievement'].tolist(),
        'grand_total'   : grand_total
    }
