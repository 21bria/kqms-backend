# views.py
import logging
from django.http import JsonResponse
from django.db import connections
import pandas as pd
from datetime import datetime
from collections import defaultdict
logger = logging.getLogger(__name__) 
from kqms.utils.db_utils import get_db_vendor

 # Memanggil fungsi utility
db_vendor = get_db_vendor('kqms_db')
import json

def safe_division(numerator, denominator):
    return round(numerator / denominator * 100, 0) if denominator else 0

def min_to_hhmm(minutes):
    minutes = int(minutes or 0)
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"

def build_filter_clause(date_val):
    where_actual = "1=1"
    where_plan = "1=1"
    params = []

    group_actual = "DATE(date_production)"
    group_plan = "DATE(date_plan)"
    where_actual += " AND DATE(date_production) = %s"
    where_plan += " AND DATE(date_plan) = %s"
    params += [date_val, date_val]

    return where_actual, where_plan, group_actual, group_plan, params

# For Summary plan vc actual
def get_summary_dataframe(where_actual, where_plan, group_actual, group_plan, params):
    query = f"""
        WITH actual AS (
            SELECT
                {group_actual} AS periode,
                SUM(CASE WHEN nama_material = 'Top Soil' THEN tonnage ELSE 0 END)::numeric AS topsoil,
                SUM(CASE WHEN nama_material = 'OB' THEN tonnage ELSE 0 END)::numeric AS ob,
                SUM(CASE WHEN nama_material = 'Waste' THEN tonnage ELSE 0 END)::numeric AS waste,
                SUM(CASE WHEN nama_material = 'Quarry' THEN tonnage ELSE 0 END)::numeric AS quarry,
                SUM(CASE WHEN nama_material = 'Ballast' THEN tonnage ELSE 0 END)::numeric AS ballast,
                SUM(CASE WHEN nama_material = 'Biomass' THEN tonnage ELSE 0 END)::numeric AS biomass,
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
            WHERE {where_actual}
            GROUP BY {group_actual}
        ),
        plan AS (
            SELECT
                {group_plan} AS periode,
                SUM(topsoil)::numeric AS topsoil_plan,
                SUM(ob)::numeric AS ob_plan,
                SUM(waste)::numeric AS waste_plan,
                SUM(quarry)::numeric AS quarry_plan,
                SUM(ballast)::numeric AS ballast_plan,
                SUM(biomass)::numeric AS biomass_plan,
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
            WHERE {where_plan}
            GROUP BY {group_plan}
        )
        SELECT
            COALESCE(a.periode, p.periode) AS periode,
            ROUND(COALESCE(a.topsoil, 0), 2) AS topsoil,
            ROUND(COALESCE(p.topsoil_plan, 0), 2) AS topsoil_plan,
            ROUND(COALESCE(a.ob, 0), 2) AS ob,
            ROUND(COALESCE(p.ob_plan, 0), 2) AS ob_plan,
            ROUND(COALESCE(a.waste, 0), 2) AS waste,
            ROUND(COALESCE(p.waste_plan, 0), 2) AS waste_plan,
            ROUND(COALESCE(a.quarry, 0), 2) AS quarry,
            ROUND(COALESCE(p.quarry_plan, 0), 2) AS quarry_plan,
            ROUND(COALESCE(a.ballast, 0), 2) AS ballast,
            ROUND(COALESCE(p.ballast_plan, 0), 2) AS ballast_plan,
            ROUND(COALESCE(a.biomass, 0), 2) AS biomass,
            ROUND(COALESCE(p.biomass_plan, 0), 2) AS biomass_plan,
            ROUND(COALESCE(a.lglo, 0), 2) AS lglo,
            ROUND(COALESCE(p.lglo_plan, 0), 2) AS lglo_plan,
            ROUND(COALESCE(a.mglo, 0), 2) AS mglo,
            ROUND(COALESCE(p.mglo_plan, 0), 2) AS mglo_plan,
            ROUND(COALESCE(a.hglo, 0), 2) AS hglo,
            ROUND(COALESCE(p.hglo_plan, 0), 2) AS hglo_plan,
            ROUND(COALESCE(a.mws, 0), 2) AS mws,
            ROUND(COALESCE(p.mws_plan, 0), 2) AS mws_plan,
            ROUND(COALESCE(a.lgso, 0), 2) AS lgso,
            ROUND(COALESCE(p.lgso_plan, 0), 2) AS lgso_plan,
            ROUND(COALESCE(a.mgso, 0), 2) AS mgso,
            ROUND(COALESCE(p.mgso_plan, 0), 2) AS mgso_plan,
            ROUND(COALESCE(a.hgso, 0), 2) AS hgso,
            ROUND(COALESCE(p.hgso_plan, 0), 2) AS hgso_plan,
            ROUND(COALESCE(a.lim, 0), 2) AS lim,
            ROUND(COALESCE(p.lim_plan, 0), 2) AS lim_plan,
            ROUND(COALESCE(a.sap, 0), 2) AS sap,
            ROUND(COALESCE(p.sap_plan, 0), 2) AS sap_plan
        FROM actual a
        FULL OUTER JOIN plan p ON a.periode = p.periode
        ORDER BY periode
    """

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params)
        data = cursor.fetchall()

    df = pd.DataFrame(data, columns=[
        'periode', 'topsoil', 'topsoil_plan',
        'ob', 'ob_plan', 'waste', 'waste_plan', 'quarry', 'quarry_plan',
        'ballast', 'ballast_plan', 'biomass', 'biomass_plan',
        'lglo', 'lglo_plan', 'mglo', 'mglo_plan', 'hglo', 'hglo_plan',
        'mws', 'mws_plan', 'lgso', 'lgso_plan', 'mgso', 'mgso_plan', 'hgso', 'hgso_plan',
        'lim', 'lim_plan', 'sap', 'sap_plan'
    ])

    return df

def generate_summary(df, label):
    ore_cols = ['lglo', 'mglo', 'hglo', 'lgso', 'mgso', 'hgso', 'mws','lim','sap']
    lim_cols = ['lglo', 'mglo', 'hglo','lim']
    sap_cols = ['lgso', 'mgso', 'hgso', 'mws','sap']
    non_ore_cols = ['topsoil', 'ob', 'waste', 'quarry', 'ballast', 'biomass']

    ore_plan_cols = [f + '_plan' for f in ore_cols]
    lim_plan_cols = [f + '_plan' for f in lim_cols]
    sap_plan_cols = [f + '_plan' for f in sap_cols]
    non_ore_plan_cols = [f + '_plan' for f in non_ore_cols]

    df['total_ore'] = df[ore_cols].sum(axis=1)
    df['total_ore_plan'] = df[ore_plan_cols].sum(axis=1)
    df['total_limonite'] = df[lim_cols].sum(axis=1)
    df['total_limonite_plan'] = df[lim_plan_cols].sum(axis=1)
    df['total_saprolite'] = df[sap_cols].sum(axis=1)
    df['total_saprolite_plan'] = df[sap_plan_cols].sum(axis=1)
    df['total_non_ore'] = df[non_ore_cols].sum(axis=1)
    df['total_non_ore_plan'] = df[non_ore_plan_cols].sum(axis=1)

    df['total_actual'] = df['total_ore'] + df['total_non_ore']
    df['total_plan'] = df['total_ore_plan'] + df['total_non_ore_plan']

    def safe_div(a, b):
        return round((a / b * 100), 0) if b > 0 else 0

    return {
        'label': label,
        'total_ore': float(round(df['total_ore'].sum(), 2)),
        'total_ore_plan': float(round(df['total_ore_plan'].sum(), 2)),
        'total_limonite': float(round(df['total_limonite'].sum(), 2)),
        'total_limonite_plan': float(round(df['total_limonite_plan'].sum(), 2)),
        'total_saprolite': float(round(df['total_saprolite'].sum(), 2)),
        'total_saprolite_plan': float(round(df['total_saprolite_plan'].sum(), 2)),
        'total_non_ore': float(round(df['total_non_ore'].sum(), 2)),
        'total_non_ore_plan': float(round(df['total_non_ore_plan'].sum(), 2)),
        'total_actual': float(round(df['total_actual'].sum(), 2)),
        'total_plan': float(round(df['total_plan'].sum(), 2)),
        'achievement': float(safe_div(df['total_actual'].sum(), df['total_plan'].sum())),
        'achievement_ore': float(safe_div(df['total_ore'].sum(), df['total_ore_plan'].sum())),
        'achievement_limonite': float(safe_div(df['total_limonite'].sum(), df['total_limonite_plan'].sum())),
        'achievement_saprolite': float(safe_div(df['total_saprolite'].sum(), df['total_saprolite_plan'].sum())),
        'achievement_non_ore': float(safe_div(df['total_non_ore'].sum(), df['total_non_ore_plan'].sum())),
    }

def get_summary_daily_mining(request):
    filter_date  = request.GET.get('filter_date')

    if db_vendor != 'postgresql':
        return JsonResponse({'error': 'Unsupported DB'}, status=400)

    result = {}

    # === Daily ===
    wa, wp, ga, gp, params = build_filter_clause(filter_date)
    df_daily = get_summary_dataframe(wa, wp, ga, gp, params)
    result['daily'] = generate_summary(df_daily, 'Daily')

    return JsonResponse(result, safe=False)

# For Chart
def get_chart_daily_mining(request):
    filter_date  = request.GET.get('filter_date')
    return get_daily_chart(filter_date)

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
                        LPAD(t_load::text, 2, '0') AS t_load_time,
                        -- total produksi aktual tanpa MWS
                    SUM(tonnage) AS total_tonnage
                    FROM mine_productions mp
                    WHERE mp.date_production = %s::date
                    GROUP BY LPAD(t_load::text, 2, '0')
                ),
                plan_per_hour AS (
                    SELECT
                        ROUND((
                            SUM(
                                COALESCE(topsoil, 0) + COALESCE(ob, 0) + COALESCE(lglo, 0) + COALESCE(mglo, 0) +
                                COALESCE(hglo, 0) + COALESCE(waste, 0) + COALESCE(mws, 0) + COALESCE(lgso, 0) +
                                COALESCE(mgso, 0) + COALESCE(hgso, 0) + COALESCE(lim, 0) + COALESCE(sap, 0) +  
                                COALESCE(quarry, 0) + COALESCE(ballast, 0) + COALESCE(biomass, 0)
                            ) / 22
                        )::numeric, 2) AS plan_data
                    FROM plan_productions
                    WHERE date_plan = %s::date
                )
                SELECT
                    hs.hour_label AS id,
                    hs.left_time,
                    COALESCE(a.total_tonnage, 0)::numeric(10,2) AS total,
                    p.plan_data
                FROM hour_series hs
                LEFT JOIN agg_data a ON hs.left_time = a.t_load_time
                CROSS JOIN plan_per_hour p
                ORDER BY hs.sort_order;
            """
        else:
            raise ValueError("Unsupported vendor")

        params = [filter_date,filter_date]

        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            data = cursor.fetchall()

        df = pd.DataFrame(data, columns=['time', 'left_time', 'total', 'plan_data'])
        df['total'] = pd.to_numeric(df['total'], errors='coerce').fillna(0.0).round(2)
        df['plan_data'] = pd.to_numeric(df['plan_data'], errors='coerce').fillna(0.0).round(2)
        df['achievement'] = df.apply(lambda r: round((r['total'] / r['plan_data'] * 100), 2) if r['plan_data'] > 0 else 0.0, axis=1)

        return JsonResponse({
            'x_data'    : df['left_time'].tolist(),  # ini label jam (misal: "01:00", "02:00", ...)
            'total_actual': df['total'].tolist(),
            'total_plan': df['plan_data'].tolist(),
            'achievement': df['achievement'].tolist(),
        }, safe=False)

def get_summary_materials(request):
    filter_date  = request.GET.get('filter_date')
    return summary_materials(filter_date)

def summary_materials(filter_date):
        if db_vendor == 'postgresql':
            query = """ 
                    SELECT 
                        nama_material,
                        SUM(COALESCE(tonnage, 0)) AS total_tonnage
                    FROM mine_productions
                    WHERE date_production = %s
                    GROUP BY nama_material;
            """
        else:
            raise ValueError("Unsupported vendor")

        params = [filter_date]

        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            data = cursor.fetchall()

        # Konversi hasil menjadi list
        labels = [row[0] for row in data]
        y_data = [round(float(row[1] or 0), 1) for row in data]

        return JsonResponse({
            'labels': labels,
            'y_data': y_data
        })

def get_summary_materials_grouped(request):
    filter_date  = request.GET.get('filter_date')
    return summary_materials_grouped(filter_date)
    
def summary_materials_grouped(filter_date):
    if db_vendor != 'postgresql':
        raise ValueError("Unsupported vendor")

    query = """
        SELECT 
            shift,
            nama_material,
            SUM(COALESCE(ritase, 0)) AS total_ritase,
            SUM(COALESCE(tonnage, 0)) AS total_tonnage
        FROM mine_productions
        WHERE date_production = %s
        GROUP BY shift, nama_material
        ORDER BY shift, nama_material;
    """

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, [filter_date])
        rows = cursor.fetchall()

    # Olah data
    summary_by_shift = defaultdict(lambda: {
        "total_ritase": 0,
        "total_tonnage": 0,
        "percentage": 0
    })

    detail = defaultdict(list)

    # Loop 1: total per shift + detail
    for shift, material, ritase, tonnage in rows:
        ritase = ritase or 0
        tonnage = float(tonnage or 0)

        summary_by_shift[shift]["total_ritase"] += ritase
        summary_by_shift[shift]["total_tonnage"] += tonnage

        detail[shift].append({
            "material"  : material,
            "ritase"    : ritase,
            "tonnage"   : round(tonnage, 2)
        })

    # Grand total tonnage
    grand_total_tonnage = sum(
        v["total_tonnage"] for v in summary_by_shift.values()
    )

    # Hitung percentage
    if grand_total_tonnage > 0:
        for shift in summary_by_shift:
            summary_by_shift[shift]["percentage"] = round((summary_by_shift[shift]["total_tonnage"] / grand_total_tonnage) * 100,2)

    return JsonResponse({
        "summary_by_shift": summary_by_shift,
        "grand_total_tonnage": round(grand_total_tonnage, 2),
        "detail": detail
    })

def get_weather_grouped(request):
    filter_date  = request.GET.get('filter_date')
    data = summary_weather_grouped(filter_date)
    return JsonResponse(data, safe=False)

def summary_weather_grouped(filter_date):
    if db_vendor != 'postgresql':
        raise ValueError("Unsupported vendor")

    query = """
        SELECT 
            shift,
            category,
            SUM(COALESCE(duration, 0)) AS duration_min
        FROM mine_weather
        WHERE date = %s
        GROUP BY shift, category
        ORDER BY shift, category;
    """

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, [filter_date])
        rows = cursor.fetchall()

    result = []
    for shift, category, duration_min in rows:
        duration_hour = round(duration_min / 60, 2)  # jam dengan koma

        result.append({
            "shift": shift,
            "category": category,
            # "duration_min": duration_min,
             "duration_min": float(duration_min), 
            "duration_hour": duration_hour
        })

    return result

# Fuel Daily Report
def get_fuel_daily_report(request):
    filter_date  = request.GET.get('filter_date')
    data = fuel_daily_report(filter_date)
    return JsonResponse(data, safe=False)

def fuel_daily_report(filter_date):
    if db_vendor != 'postgresql':
        raise ValueError("Unsupported vendor")

    query = """
        SELECT 
            shift,
            SUM(COALESCE(volume, 0)) AS total_fuel
        FROM mine_units_fuel_consumption
        WHERE date = %s
        GROUP BY shift
        ORDER BY shift;
    """

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, [filter_date])
        rows = cursor.fetchall()

    by_shift = []
    grand_total = 0

    for shift, total_fuel in rows:
        fuel = float(total_fuel or 0)
        grand_total += fuel

        by_shift.append({
            "shift": shift,
            "total_fuel": fuel
        })

    return {
        "by_shift": by_shift,
        "grand_total": grand_total
    }

def get_daily_fuel_ratio(request):
    filter_date  = request.GET.get('filter_date')
    return summary_daily_fuel_ratio(filter_date)

def summary_daily_fuel_ratio(filter_date):
    if db_vendor == 'postgresql':
        query = """
        WITH loader AS (
            SELECT
                date_production,
                SUM(total_loader) AS total_tonnage_loader,
                SUM(total_bcm) AS total_bcm_loader,
                SUM(total_fuel_loader) AS total_fuel_loader
            FROM view_fuel_loader_all
            WHERE date_production = %s
            GROUP BY date_production
        ),
        hauler AS (
            SELECT
                date_production,
                SUM(total_tonnage) AS total_tonnage_hauler,
                SUM(total_bcm) AS total_bcm_hauler,
                SUM(total_fuel_hauler) AS total_fuel_hauler
            FROM view_fuel_hauler_all
            WHERE date_production = %s
            GROUP BY date_production
        )
        SELECT
            COALESCE(h.date_production, l.date_production) AS date_production,
            -- Tonase total
            COALESCE(h.total_tonnage_hauler,0) + COALESCE(l.total_tonnage_loader,0) AS total_tonnage,
            COALESCE(h.total_bcm_hauler,0) + COALESCE(l.total_bcm_loader,0) AS total_bcm,
            -- Fuel total
            COALESCE(h.total_fuel_hauler,0) + COALESCE(l.total_fuel_loader,0) AS total_fuel,
            -- Fuel ratio keseluruhan
            ROUND(
                (COALESCE(h.total_fuel_hauler,0) + COALESCE(l.total_fuel_loader,0))::numeric
                / NULLIF((COALESCE(h.total_tonnage_hauler,0) + COALESCE(l.total_tonnage_loader,0))::numeric,0),
                3
            ) AS fuel_ratio_per_ton
        FROM hauler h
        FULL OUTER JOIN loader l
            ON h.date_production = l.date_production
        ORDER BY date_production;
        """
        
        params = [filter_date, filter_date]

        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            data = cursor.fetchall()

        # Ubah ke DataFrame
        df = pd.DataFrame(data, columns=['date_production','total_tonnage','total_bcm','total_fuel','fuel_ratio_per_ton'])
        df[['total_tonnage','total_bcm','total_fuel','fuel_ratio_per_ton']] = df[['total_tonnage','total_bcm','total_fuel','fuel_ratio_per_ton']].apply(pd.to_numeric, errors='coerce').fillna(0.0)
        
        # Bisa return langsung JSON
        return JsonResponse({
            'date_production': df['date_production'].tolist(),
            'total_tonnage': df['total_tonnage'].tolist(),
            'total_bcm': df['total_bcm'].tolist(),
            'total_fuel': df['total_fuel'].tolist(),
            'fuel_ratio_per_ton': df['fuel_ratio_per_ton'].tolist(),
        }, safe=False)

    else:
        raise ValueError("Unsupported vendor")
    
def get_daily_fuel_ratio_ore(request):
    filter_date  = request.GET.get('filter_date')
    return summary_daily_fuel_ratio_ore(filter_date)

def summary_daily_fuel_ratio_ore(filter_date):
    if db_vendor == 'postgresql':
        query = """
        WITH loader AS (
            SELECT
                date_production,
                SUM(total_loader) AS total_tonnage_loader,
                SUM(total_bcm) AS total_bcm_loader,
                SUM(total_fuel_loader) AS total_fuel_loader
            FROM view_fuel_loader_ore
            WHERE date_production = %s
            GROUP BY date_production
        ),
        hauler AS (
            SELECT
                date_production,
                SUM(total_tonnage) AS total_tonnage_hauler,
                SUM(total_bcm) AS total_bcm_hauler,
                SUM(total_fuel_hauler) AS total_fuel_hauler
            FROM view_fuel_hauler_ore
            WHERE date_production = %s
            GROUP BY date_production
        )
        SELECT
            COALESCE(h.date_production, l.date_production) AS date_production,
            -- Tonase total
            COALESCE(h.total_tonnage_hauler,0) + COALESCE(l.total_tonnage_loader,0) AS total_tonnage,
            COALESCE(h.total_bcm_hauler,0) + COALESCE(l.total_bcm_loader,0) AS total_bcm,
            -- Fuel total
            COALESCE(h.total_fuel_hauler,0) + COALESCE(l.total_fuel_loader,0) AS total_fuel,
            -- Fuel ratio keseluruhan
            ROUND(
                (COALESCE(h.total_fuel_hauler,0) + COALESCE(l.total_fuel_loader,0))::numeric
                / NULLIF((COALESCE(h.total_tonnage_hauler,0) + COALESCE(l.total_tonnage_loader,0))::numeric,0),
                3
            ) AS fuel_ratio_per_ton
        FROM hauler h
        FULL OUTER JOIN loader l
            ON h.date_production = l.date_production
        ORDER BY date_production;
        """

        params = [filter_date, filter_date]

        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            data = cursor.fetchall()

        # Ubah ke DataFrame
        df = pd.DataFrame(data, columns=['date_production','total_tonnage','total_bcm','total_fuel','fuel_ratio_per_ton'])
        df[['total_tonnage','total_bcm','total_fuel','fuel_ratio_per_ton']] = df[['total_tonnage','total_bcm','total_fuel','fuel_ratio_per_ton']].apply(pd.to_numeric, errors='coerce').fillna(0.0)
        
        # Bisa return langsung JSON
        return JsonResponse({
            'date_production'   : df['date_production'].tolist(),
            'total_tonnage'     : df['total_tonnage'].tolist(),
            'total_bcm'         : df['total_bcm'].tolist(),
            'total_fuel'        : df['total_fuel'].tolist(),
            'fuel_ratio_per_ton': df['fuel_ratio_per_ton'].tolist(),
        }, safe=False)

    else:
        raise ValueError("Unsupported vendor")


# Kpi Daily Mining
def min_to_hour(m):
    return round((m or 0) / 60, 2)

# @login_required
def get_kpi_daily_hauler(request):
    filter_date     = request.GET.get('filter_date')

    # Optional validasi
    try:
        datetime.strptime(filter_date, "%Y-%m-%d")
    except ValueError:
        return JsonResponse({"error": "Invalid date format"}, status=400)

    try:
        if db_vendor != 'postgresql':
            raise ValueError("Unsupported database vendor.")

        query = """
            WITH prod_units AS (
                SELECT DISTINCT
                    date_production AS date,
                    TRIM(hauler) AS unit_code
                FROM productions_mines
                WHERE date_production = %s
            )
            SELECT
                u.unit_code,
                TRIM(c.category) AS category,
                -- FUEL
                COALESCE(SUM(f.volume), 0) AS fuel,
                -- DURATIONS
                SUM(CASE WHEN s.code = 'EWH'
                    THEN COALESCE(d.duration_min,0) ELSE 0 END) AS op,
                SUM(CASE WHEN s.code IN ('STB','SUPPORT','WX','SLP')
                    THEN COALESCE(d.duration_min,0) ELSE 0 END) AS st,
                SUM(CASE WHEN s.code IN ('PM','BD')
                    THEN COALESCE(d.duration_min,0) ELSE 0 END) AS mt,
                SUM(CASE WHEN s.code = 'BD'
                    THEN COALESCE(d.duration_min,0) ELSE 0 END) AS bd,
                COUNT(DISTINCT h.date) * 1440 AS total_time,
                -- MA
                ROUND(
                    SUM(CASE WHEN s.code = 'EWH'
                        THEN COALESCE(d.duration_min,0) ELSE 0 END)::numeric
                    /
                    NULLIF(
                        SUM(CASE WHEN s.code IN ('EWH','PM','BD')
                            THEN COALESCE(d.duration_min,0) ELSE 0 END),
                        0
                    ) * 100,
                    2
                ) AS ma,
                -- PA
                ROUND(
                    SUM(CASE WHEN s.code IN ('EWH','STB','SUPPORT','WX','SLP')
                        THEN COALESCE(d.duration_min,0) ELSE 0 END)::numeric
                    /
                    (COUNT(DISTINCT h.date) * 1440) * 100,
                    2
                ) AS pa,
                -- UA
                ROUND(
                        SUM(CASE WHEN s.code = 'EWH'
                            THEN COALESCE(d.duration_min,0) ELSE 0 END)::numeric
                        /
                        NULLIF(
                            SUM(CASE WHEN s.code IN ('EWH','STB','SUPPORT','WX','SLP')
                                THEN COALESCE(d.duration_min,0) ELSE 0 END),
                            0
                        ) * 100,
                        2
                    ) AS ua,
                -- EU
                ROUND(
                    SUM(CASE WHEN s.code = 'EWH'
                        THEN COALESCE(d.duration_min,0) ELSE 0 END)::numeric
                    /
                    (COUNT(DISTINCT h.date) * 1440) * 100,
                    2
                ) AS eu
            FROM mine_hm_unit h
            LEFT JOIN mine_units u ON u.id = h.unit_id
            -- FILTER UTAMA: hanya unit yang ada di produksi
            JOIN prod_units pu ON pu.unit_code = TRIM(u.unit_code) AND pu.date = h.date
            LEFT JOIN mine_hm_unit_detail d ON d.hm_unit_id = h.id
            LEFT JOIN units_categories c ON c.id = u.id_category
            LEFT JOIN mine_units_categories_status s ON s.id = d.status_id
            LEFT JOIN mine_units_fuel_consumption f ON f.unit = u.unit_code AND f.date = h.date
        """
        params  = [filter_date]

        query += "GROUP BY u.unit_code, c.category ORDER BY c.category, u.unit_code;"

        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        result = []
        for r in rows:
            result.append({
                "unit"     : r[0],
                "category" : r[1],
                "fuel"     : float(r[2] or 0),
                # ⬇️ TIME → JAM DESIMAL
                "op"       : min_to_hour(r[3]),
                "st"       : min_to_hour(r[4]),
                "mt"       : min_to_hour(r[5]),
                "bd"       : min_to_hour(r[6]),
                # ⬇️ TOTAL TIME (opsional)
                "time"     : min_to_hour(r[7]),
                # "time"     : int(r[7] or 0),
                "ma"       : float(r[8] or 0),
                "pa"       : float(r[9] or 0),
                "ua"       : float(r[10] or 0),
                "eu"       : float(r[11] or 0),
            })

        return JsonResponse({
            "success" : True,
            "data"    : result
        })


    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
def get_kpi_daily_digger(request):
    filter_date     = request.GET.get('filter_date')

    # Optional validasi
    try:
        datetime.strptime(filter_date, "%Y-%m-%d")
    except ValueError:
        return JsonResponse({"error": "Invalid date format"}, status=400)

    try:
        if db_vendor != 'postgresql':
            raise ValueError("Unsupported database vendor.")

        query = """
            WITH prod_units AS (
                SELECT DISTINCT
                    date_production AS date,
                    TRIM(loader) AS unit_code
                FROM productions_mines
                WHERE date_production = %s
            )
            SELECT
                u.unit_code,
                TRIM(c.category) AS category,
                -- FUEL
                COALESCE(SUM(f.volume), 0) AS fuel,
                -- DURATIONS
                SUM(CASE WHEN s.code = 'EWH'
                    THEN COALESCE(d.duration_min,0) ELSE 0 END) AS op,
                SUM(CASE WHEN s.code IN ('STB','SUPPORT','WX','SLP')
                    THEN COALESCE(d.duration_min,0) ELSE 0 END) AS st,
                SUM(CASE WHEN s.code IN ('PM','BD')
                    THEN COALESCE(d.duration_min,0) ELSE 0 END) AS mt,
                SUM(CASE WHEN s.code = 'BD'
                    THEN COALESCE(d.duration_min,0) ELSE 0 END) AS bd,
                COUNT(DISTINCT h.date) * 1440 AS total_time,
                -- MA
                ROUND(
                    SUM(CASE WHEN s.code = 'EWH'
                        THEN COALESCE(d.duration_min,0) ELSE 0 END)::numeric
                    /
                    NULLIF(
                        SUM(CASE WHEN s.code IN ('EWH','PM','BD')
                            THEN COALESCE(d.duration_min,0) ELSE 0 END),
                        0
                    ) * 100,
                    2
                ) AS ma,
                -- PA
                ROUND(
                    SUM(CASE WHEN s.code IN ('EWH','STB','SUPPORT','WX','SLP')
                        THEN COALESCE(d.duration_min,0) ELSE 0 END)::numeric
                    /
                    (COUNT(DISTINCT h.date) * 1440) * 100,
                    2
                ) AS pa,
                -- UA
                ROUND(
                        SUM(CASE WHEN s.code = 'EWH'
                            THEN COALESCE(d.duration_min,0) ELSE 0 END)::numeric
                        /
                        NULLIF(
                            SUM(CASE WHEN s.code IN ('EWH','STB','SUPPORT','WX','SLP')
                                THEN COALESCE(d.duration_min,0) ELSE 0 END),
                            0
                        ) * 100,
                        2
                    ) AS ua,
                -- EU
                ROUND(
                    SUM(CASE WHEN s.code = 'EWH'
                        THEN COALESCE(d.duration_min,0) ELSE 0 END)::numeric
                    /
                    (COUNT(DISTINCT h.date) * 1440) * 100,
                    2
                ) AS eu
            FROM mine_hm_unit h
            LEFT JOIN mine_units u ON u.id = h.unit_id
            -- FILTER UTAMA: hanya unit yang ada di produksi
            JOIN prod_units pu ON pu.unit_code = TRIM(u.unit_code) AND pu.date = h.date
            LEFT JOIN mine_hm_unit_detail d ON d.hm_unit_id = h.id
            LEFT JOIN units_categories c ON c.id = u.id_category
            LEFT JOIN mine_units_categories_status s ON s.id = d.status_id
            LEFT JOIN mine_units_fuel_consumption f ON f.unit = u.unit_code AND f.date = h.date
        """
        params  = [filter_date]

        query += "GROUP BY u.unit_code, c.category ORDER BY c.category, u.unit_code;"

        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        result = []
        for r in rows:
            result.append({
                "unit"     : r[0],
                "category" : r[1],
                "fuel"     : float(r[2] or 0),
                # ⬇️ TIME → JAM DESIMAL
                "op"       : min_to_hour(r[3]),
                "st"       : min_to_hour(r[4]),
                "mt"       : min_to_hour(r[5]),
                "bd"       : min_to_hour(r[6]),
                # ⬇️ TOTAL TIME (opsional)
                "time"     : min_to_hour(r[7]),
                # "time"     : int(r[7] or 0),
                "ma"       : float(r[8] or 0),
                "pa"       : float(r[9] or 0),
                "ua"       : float(r[10] or 0),
                "eu"       : float(r[11] or 0),
            })

        return JsonResponse({
            "success" : True,
            "data"    : result
        })


    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
   