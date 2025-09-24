from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.db import connections
from django.utils.html import escape
import json,re
import pandas as pd
from datetime import datetime, timedelta


# Fungsi untuk sanitasi input
def sanitize_input(value):
    if value is None:
        return None
    return escape(re.sub(r"[;'\"]", "", str(value)))

def niChartCoa(request):
    filter_type = request.GET.get('filter_type')
    year        = request.GET.get('year')
    month       = request.GET.get('month')
    week        = request.GET.get('week')
    date_start  = request.GET.get('date_start')
    date_end    = request.GET.get('date_end')
    filter_date = request.GET.get('filter_date')
    typeFilter  = request.GET.get('materialFilter')

    base_query = """
        SELECT 
            TRIM(t1.code_lot) AS code_lot,
            TRIM(t1.barge_code) AS barge_code,
            CONCAT(TRIM(t1.barge_code), '/', RIGHT(TRIM(t1.code_lot), 3)) AS lot_barge,
            COALESCE(SUM(t1.tonnage), 0) AS tonnage_split,              
            COALESCE(SUM(t1.tonnage * t1.ni) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.ni IS NOT NULL THEN t1.tonnage ELSE 0 END),0), 0) AS ni_split,
            COALESCE(t2.tonnage_official, 0) AS tonnage_official,
            COALESCE(t2.ni, 0) AS ni_official,
            ABS(COALESCE(SUM(t1.tonnage) - t2.tonnage_official, 0)) AS tonnage_diff,
            COALESCE(((SUM(t1.tonnage * t1.ni) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.ni IS NOT NULL THEN t1.tonnage ELSE 0 END), 0)) - t2.ni) / NULLIF(t2.ni, 0) * 100, 0) AS ni_diff
        FROM details_selling_barge_split t1
        LEFT JOIN (
            SELECT 
                product_code,
                COALESCE(SUM(tonnage), 0) AS tonnage_official,
                COALESCE(SUM(ni), 0) AS ni,
                type_selling
            FROM sellings_official_view
            GROUP BY product_code, type_selling
        ) AS t2 ON t1.code_lot = t2.product_code
        WHERE 1=1
    """

    filters = []

    # --- Daily ---
    if filter_type == 'daily' and filter_date:
        filters.append(f"DATE(t1.date_barge_out) = '{filter_date}'")

    # --- Range ---
    elif filter_type == 'range' and date_start and date_end:
        filters.append(f"t1.date_barge_out BETWEEN '{date_start}' AND '{date_end}'")

    # --- Weekly ---
    elif filter_type == 'weekly' and year and month and week:
        year = int(year); month = int(month); week = int(week)
        first_day = datetime(int(year), int(month), 1)
        start_date = first_day + timedelta(days=(week - 1) * 7)
        end_date = start_date + timedelta(days=6)
        if end_date.month != month:  # koreksi akhir bulan
            next_month = datetime(year, month, 28) + timedelta(days=4)
            end_date = datetime(next_month.year, next_month.month, 1) - timedelta(days=1)
        filters.append(f"t1.date_barge_out BETWEEN '{start_date.date()}' AND '{end_date.date()}'")

    # --- Monthly ---
    elif filter_type == 'monthly' and year and month:
        filters.append(f"EXTRACT(YEAR FROM t1.date_barge_out) = {year} "
                       f"AND EXTRACT(MONTH FROM t1.date_barge_out) = {month}")

    # --- Yearly ---
    elif filter_type == 'yearly' and year:
        filters.append(f"EXTRACT(YEAR FROM t1.date_barge_out) = {year}")

    # --- All ---
    elif filter_type == 'all':
        pass  # tidak ada filter tambahan

    else:
        return JsonResponse({'error': 'Invalid or incomplete filter parameters'}, status=400)

    # Filter tambahan (material type)
    if typeFilter:
        filters.append(f"t1.sale_adjust = '{typeFilter}'")

    # Gabungkan filter ke query
    if filters:
        base_query += " AND " + " AND ".join(filters)

    # Grouping akhir
    base_query += """
        GROUP BY t1.code_lot, t1.barge_code,
                 t2.tonnage_official, t2.ni
        ORDER BY t1.code_lot ASC
    """

    # Eksekusi query
    df = pd.read_sql_query(base_query, connections['kqms_db'])
    details = df.to_dict(orient="records")
    
    compare = {
        "x_data": [row["lot_barge"] for row in details],
        "y_split": [round(row["ni_split"] or 0, 2) for row in details],
        "y_official": [round(row["ni_official"] or 0, 2) for row in details],
        "tonnage_split": [round(row["tonnage_split"] or 0, 2) for row in details],
        "tonnage_official": [round(row["tonnage_official"] or 0, 2) for row in details],
        "ni_diff": [round(row["ni_diff"] or 0, 3) for row in details],
        "tonnage_diff": [round(row["tonnage_diff"] or 0, 2) for row in details],
    }

    return JsonResponse({
        "compare": compare,
        "details": details
    }, safe=False)

def feChartCoa(request):
    filter_type = request.GET.get('filter_type')
    year        = request.GET.get('year')
    month       = request.GET.get('month')
    week        = request.GET.get('week')
    date_start  = request.GET.get('date_start')
    date_end    = request.GET.get('date_end')
    filter_date = request.GET.get('filter_date')
    typeFilter  = request.GET.get('materialFilter')

    base_query = """
        SELECT 
            TRIM(t1.code_lot) AS code_lot,
            TRIM(t1.barge_code) AS barge_code,
            CONCAT(TRIM(t1.barge_code), '/', RIGHT(TRIM(t1.code_lot), 3)) AS lot_barge,
            COALESCE(SUM(t1.tonnage), 0) AS tonnage_split,              
            COALESCE(SUM(t1.tonnage * t1.fe) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.fe IS NOT NULL THEN t1.tonnage ELSE 0 END),0), 0) AS fe_split,
            COALESCE(t2.tonnage_official, 0) AS tonnage_official,
            COALESCE(t2.fe, 0) AS fe_official,
            ABS(COALESCE(SUM(t1.tonnage) - t2.tonnage_official, 0)) AS tonnage_diff,
            COALESCE(((SUM(t1.tonnage * t1.fe) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.fe IS NOT NULL THEN t1.tonnage ELSE 0 END), 0)) - t2.fe) / NULLIF(t2.fe, 0) * 100, 0) AS fe_diff
        FROM details_selling_barge_split t1
        LEFT JOIN (
            SELECT 
                product_code,
                COALESCE(SUM(tonnage), 0) AS tonnage_official,
                COALESCE(SUM(fe), 0) AS fe,
                type_selling
            FROM sellings_official_view
            GROUP BY product_code, type_selling
        ) AS t2 ON t1.code_lot = t2.product_code
        WHERE 1=1
    """

    filters = []

    # --- Daily ---
    if filter_type == 'daily' and filter_date:
        filters.append(f"DATE(t1.date_barge_out) = '{filter_date}'")

    # --- Range ---
    elif filter_type == 'range' and date_start and date_end:
        filters.append(f"t1.date_barge_out BETWEEN '{date_start}' AND '{date_end}'")

    # --- Weekly ---
    elif filter_type == 'weekly' and year and month and week:
        year = int(year); month = int(month); week = int(week)
        first_day = datetime(int(year), int(month), 1)
        start_date = first_day + timedelta(days=(week - 1) * 7)
        end_date = start_date + timedelta(days=6)
        if end_date.month != month:  # koreksi akhir bulan
            next_month = datetime(year, month, 28) + timedelta(days=4)
            end_date = datetime(next_month.year, next_month.month, 1) - timedelta(days=1)
        filters.append(f"t1.date_barge_out BETWEEN '{start_date.date()}' AND '{end_date.date()}'")

    # --- Monthly ---
    elif filter_type == 'monthly' and year and month:
        filters.append(f"EXTRACT(YEAR FROM t1.date_barge_out) = {year} "
                       f"AND EXTRACT(MONTH FROM t1.date_barge_out) = {month}")

    # --- Yearly ---
    elif filter_type == 'yearly' and year:
        filters.append(f"EXTRACT(YEAR FROM t1.date_barge_out) = {year}")

    # --- All ---
    elif filter_type == 'all':
        pass  # tidak ada filter tambahan

    else:
        return JsonResponse({'error': 'Invalid or incomplete filter parameters'}, status=400)

    # Filter tambahan (material type)
    if typeFilter:
        filters.append(f"t1.sale_adjust = '{typeFilter}'")

    # Gabungkan filter ke query
    if filters:
        base_query += " AND " + " AND ".join(filters)

    # Grouping akhir
    base_query += """
        GROUP BY t1.code_lot, t1.barge_code,
                 t2.tonnage_official, t2.fe
        ORDER BY t1.code_lot ASC
    """

    # Eksekusi query
    df = pd.read_sql_query(base_query, connections['kqms_db'])
    details = df.to_dict(orient="records")
    
    compare = {
        "x_data": [row["lot_barge"] for row in details],
        "y_split": [round(row["fe_split"] or 0, 2) for row in details],
        "y_official": [round(row["fe_official"] or 0, 2) for row in details],
        "tonnage_split": [round(row["tonnage_split"] or 0, 2) for row in details],
        "tonnage_official": [round(row["tonnage_official"] or 0, 2) for row in details],
        "fe_diff": [round(row["fe_diff"] or 0, 3) for row in details],
        "tonnage_diff": [round(row["tonnage_diff"] or 0, 2) for row in details],
    }

    return JsonResponse({
        "compare": compare,
        "details": details
    }, safe=False)

def mgoChartCoa(request):
    filter_type = request.GET.get('filter_type')
    year        = request.GET.get('year')
    month       = request.GET.get('month')
    week        = request.GET.get('week')
    date_start  = request.GET.get('date_start')
    date_end    = request.GET.get('date_end')
    filter_date = request.GET.get('filter_date')
    typeFilter  = request.GET.get('materialFilter')

    base_query = """
        SELECT 
            TRIM(t1.code_lot) AS code_lot,
            TRIM(t1.barge_code) AS barge_code,
            CONCAT(TRIM(t1.barge_code), '/', RIGHT(TRIM(t1.code_lot), 3)) AS lot_barge,
            COALESCE(SUM(t1.tonnage), 0) AS tonnage_split,              
            COALESCE(SUM(t1.tonnage * t1.mgo) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.mgo IS NOT NULL THEN t1.tonnage ELSE 0 END),0), 0) AS mgo_split,
            COALESCE(t2.tonnage_official, 0) AS tonnage_official,
            COALESCE(t2.mgo, 0) AS mgo_official,
            ABS(COALESCE(SUM(t1.tonnage) - t2.tonnage_official, 0)) AS tonnage_diff,
            COALESCE(((SUM(t1.tonnage * t1.mgo) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.mgo IS NOT NULL THEN t1.tonnage ELSE 0 END), 0)) - t2.mgo) / NULLIF(t2.mgo, 0) * 100, 0) AS mgo_diff
        FROM details_selling_barge_split t1
        LEFT JOIN (
            SELECT 
                product_code,
                COALESCE(SUM(tonnage), 0) AS tonnage_official,
                COALESCE(SUM(mgo), 0) AS mgo,
                type_selling
            FROM sellings_official_view
            GROUP BY product_code, type_selling
        ) AS t2 ON t1.code_lot = t2.product_code
        WHERE 1=1
    """

    filters = []

    # --- Daily ---
    if filter_type == 'daily' and filter_date:
        filters.append(f"DATE(t1.date_barge_out) = '{filter_date}'")

    # --- Range ---
    elif filter_type == 'range' and date_start and date_end:
        filters.append(f"t1.date_barge_out BETWEEN '{date_start}' AND '{date_end}'")

    # --- Weekly ---
    elif filter_type == 'weekly' and year and month and week:
        year = int(year); month = int(month); week = int(week)
        first_day = datetime(int(year), int(month), 1)
        start_date = first_day + timedelta(days=(week - 1) * 7)
        end_date = start_date + timedelta(days=6)
        if end_date.month != month:  # koreksi akhir bulan
            next_month = datetime(year, month, 28) + timedelta(days=4)
            end_date = datetime(next_month.year, next_month.month, 1) - timedelta(days=1)
        filters.append(f"t1.date_barge_out BETWEEN '{start_date.date()}' AND '{end_date.date()}'")

    # --- Monthly ---
    elif filter_type == 'monthly' and year and month:
        filters.append(f"EXTRACT(YEAR FROM t1.date_barge_out) = {year} "
                       f"AND EXTRACT(MONTH FROM t1.date_barge_out) = {month}")

    # --- Yearly ---
    elif filter_type == 'yearly' and year:
        filters.append(f"EXTRACT(YEAR FROM t1.date_barge_out) = {year}")

    # --- All ---
    elif filter_type == 'all':
        pass  # tidak ada filter tambahan

    else:
        return JsonResponse({'error': 'Invalid or incomplete filter parameters'}, status=400)

    # Filter tambahan (material type)
    if typeFilter:
        filters.append(f"t1.sale_adjust = '{typeFilter}'")

    # Gabungkan filter ke query
    if filters:
        base_query += " AND " + " AND ".join(filters)

    # Grouping akhir
    base_query += """
        GROUP BY t1.code_lot, t1.barge_code,
                 t2.tonnage_official, t2.mgo
        ORDER BY t1.code_lot ASC
    """

    # Eksekusi query
    df = pd.read_sql_query(base_query, connections['kqms_db'])
    details = df.to_dict(orient="records")
    
    compare = {
        "x_data": [row["lot_barge"] for row in details],
        "y_split": [round(row["mgo_split"] or 0, 2) for row in details],
        "y_official": [round(row["mgo_official"] or 0, 2) for row in details],
        "tonnage_split": [round(row["tonnage_split"] or 0, 2) for row in details],
        "tonnage_official": [round(row["tonnage_official"] or 0, 2) for row in details],
        "mgo_diff": [round(row["mgo_diff"] or 0, 3) for row in details],
        "tonnage_diff": [round(row["tonnage_diff"] or 0, 2) for row in details],
    }

    return JsonResponse({
        "compare": compare,
        "details": details
    }, safe=False)

def sio2ChartCoa(request):
    filter_type = request.GET.get('filter_type')
    year        = request.GET.get('year')
    month       = request.GET.get('month')
    week        = request.GET.get('week')
    date_start  = request.GET.get('date_start')
    date_end    = request.GET.get('date_end')
    filter_date = request.GET.get('filter_date')
    typeFilter  = request.GET.get('materialFilter')

    base_query = """
        SELECT 
            TRIM(t1.code_lot) AS code_lot,
            TRIM(t1.barge_code) AS barge_code,
            CONCAT(TRIM(t1.barge_code), '/', RIGHT(TRIM(t1.code_lot), 3)) AS lot_barge,
            COALESCE(SUM(t1.tonnage), 0) AS tonnage_split,              
            COALESCE(SUM(t1.tonnage * t1.sio2) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.sio2 IS NOT NULL THEN t1.tonnage ELSE 0 END),0), 0) AS sio2_split,
            COALESCE(t2.tonnage_official, 0) AS tonnage_official,
            COALESCE(t2.sio2, 0) AS sio2_official,
            ABS(COALESCE(SUM(t1.tonnage) - t2.tonnage_official, 0)) AS tonnage_diff,
            COALESCE(((SUM(t1.tonnage * t1.sio2) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.sio2 IS NOT NULL THEN t1.tonnage ELSE 0 END), 0)) - t2.sio2) / NULLIF(t2.sio2, 0) * 100, 0) AS sio2_diff
        FROM details_selling_barge_split t1
        LEFT JOIN (
            SELECT 
                product_code,
                COALESCE(SUM(tonnage), 0) AS tonnage_official,
                COALESCE(SUM(sio2), 0) AS sio2,
                type_selling
            FROM sellings_official_view
            GROUP BY product_code, type_selling
        ) AS t2 ON t1.code_lot = t2.product_code
        WHERE 1=1
    """

    filters = []

    # --- Daily ---
    if filter_type == 'daily' and filter_date:
        filters.append(f"DATE(t1.date_barge_out) = '{filter_date}'")

    # --- Range ---
    elif filter_type == 'range' and date_start and date_end:
        filters.append(f"t1.date_barge_out BETWEEN '{date_start}' AND '{date_end}'")

    # --- Weekly ---
    elif filter_type == 'weekly' and year and month and week:
        year = int(year); month = int(month); week = int(week)
        first_day = datetime(int(year), int(month), 1)
        start_date = first_day + timedelta(days=(week - 1) * 7)
        end_date = start_date + timedelta(days=6)
        if end_date.month != month:  # koreksi akhir bulan
            next_month = datetime(year, month, 28) + timedelta(days=4)
            end_date = datetime(next_month.year, next_month.month, 1) - timedelta(days=1)
        filters.append(f"t1.date_barge_out BETWEEN '{start_date.date()}' AND '{end_date.date()}'")

    # --- Monthly ---
    elif filter_type == 'monthly' and year and month:
        filters.append(f"EXTRACT(YEAR FROM t1.date_barge_out) = {year} "
                       f"AND EXTRACT(MONTH FROM t1.date_barge_out) = {month}")

    # --- Yearly ---
    elif filter_type == 'yearly' and year:
        filters.append(f"EXTRACT(YEAR FROM t1.date_barge_out) = {year}")

    # --- All ---
    elif filter_type == 'all':
        pass  # tidak ada filter tambahan

    else:
        return JsonResponse({'error': 'Invalid or incomplete filter parameters'}, status=400)

    # Filter tambahan (material type)
    if typeFilter:
        filters.append(f"t1.sale_adjust = '{typeFilter}'")

    # Gabungkan filter ke query
    if filters:
        base_query += " AND " + " AND ".join(filters)

    # Grouping akhir
    base_query += """
        GROUP BY t1.code_lot, t1.barge_code,
                 t2.tonnage_official, t2.sio2
        ORDER BY t1.code_lot ASC
    """

    # Eksekusi query
    df = pd.read_sql_query(base_query, connections['kqms_db'])
    details = df.to_dict(orient="records")
    
    compare = {
        "x_data": [row["lot_barge"] for row in details],
        "y_split": [round(row["sio2_split"] or 0, 2) for row in details],
        "y_official": [round(row["sio2_official"] or 0, 2) for row in details],
        "tonnage_split": [round(row["tonnage_split"] or 0, 2) for row in details],
        "tonnage_official": [round(row["tonnage_official"] or 0, 2) for row in details],
        "sio2_diff": [round(row["sio2_diff"] or 0, 3) for row in details],
        "tonnage_diff": [round(row["tonnage_diff"] or 0, 2) for row in details],
    }

    return JsonResponse({
        "compare": compare,
        "details": details
    }, safe=False)

def smChartCoa(request):
    filter_type = request.GET.get('filter_type')
    year        = request.GET.get('year')
    month       = request.GET.get('month')
    week        = request.GET.get('week')
    date_start  = request.GET.get('date_start')
    date_end    = request.GET.get('date_end')
    filter_date = request.GET.get('filter_date')
    typeFilter  = request.GET.get('materialFilter')

    base_query = """
        SELECT 
            TRIM(t1.code_lot) AS code_lot,
            TRIM(t1.barge_code) AS barge_code,
            CONCAT(TRIM(t1.barge_code), '/', RIGHT(TRIM(t1.code_lot), 3)) AS lot_barge,
            COALESCE(SUM(t1.tonnage), 0) AS tonnage_split,              
            COALESCE(SUM(t1.tonnage * t1.sm) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.sm IS NOT NULL THEN t1.tonnage ELSE 0 END),0), 0) AS sm_split,
            COALESCE(t2.tonnage_official, 0) AS tonnage_official,
            COALESCE(t2.sm, 0) AS sm_official,
            ABS(COALESCE(SUM(t1.tonnage) - t2.tonnage_official, 0)) AS tonnage_diff,
            COALESCE(((SUM(t1.tonnage * t1.sm) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.sm IS NOT NULL THEN t1.tonnage ELSE 0 END), 0)) - t2.sm) / NULLIF(t2.sm, 0) * 100, 0) AS sm_diff
        FROM details_selling_barge_split t1
        LEFT JOIN (
            SELECT 
                product_code,
                COALESCE(SUM(tonnage), 0) AS tonnage_official,
                COALESCE(SUM(sm), 0) AS sm,
                type_selling
            FROM sellings_official_view
            GROUP BY product_code, type_selling
        ) AS t2 ON t1.code_lot = t2.product_code
        WHERE 1=1
    """

    filters = []

    # --- Daily ---
    if filter_type == 'daily' and filter_date:
        filters.append(f"DATE(t1.date_barge_out) = '{filter_date}'")

    # --- Range ---
    elif filter_type == 'range' and date_start and date_end:
        filters.append(f"t1.date_barge_out BETWEEN '{date_start}' AND '{date_end}'")

    # --- Weekly ---
    elif filter_type == 'weekly' and year and month and week:
        year = int(year); month = int(month); week = int(week)
        first_day = datetime(int(year), int(month), 1)
        start_date = first_day + timedelta(days=(week - 1) * 7)
        end_date = start_date + timedelta(days=6)
        if end_date.month != month:  # koreksi akhir bulan
            next_month = datetime(year, month, 28) + timedelta(days=4)
            end_date = datetime(next_month.year, next_month.month, 1) - timedelta(days=1)
        filters.append(f"t1.date_barge_out BETWEEN '{start_date.date()}' AND '{end_date.date()}'")

    # --- Monthly ---
    elif filter_type == 'monthly' and year and month:
        filters.append(f"EXTRACT(YEAR FROM t1.date_barge_out) = {year} "
                       f"AND EXTRACT(MONTH FROM t1.date_barge_out) = {month}")

    # --- Yearly ---
    elif filter_type == 'yearly' and year:
        filters.append(f"EXTRACT(YEAR FROM t1.date_barge_out) = {year}")

    # --- All ---
    elif filter_type == 'all':
        pass  # tidak ada filter tambahan

    else:
        return JsonResponse({'error': 'Invalid or incomplete filter parameters'}, status=400)

    # Filter tambahan (material type)
    if typeFilter:
        filters.append(f"t1.sale_adjust = '{typeFilter}'")

    # Gabungkan filter ke query
    if filters:
        base_query += " AND " + " AND ".join(filters)

    # Grouping akhir
    base_query += """
        GROUP BY t1.code_lot, t1.barge_code,
                 t2.tonnage_official, t2.sm
        ORDER BY t1.code_lot ASC
    """

    # Eksekusi query
    df = pd.read_sql_query(base_query, connections['kqms_db'])
    details = df.to_dict(orient="records")
    
    compare = {
        "x_data": [row["lot_barge"] for row in details],
        "y_split": [round(row["sm_split"] or 0, 2) for row in details],
        "y_official": [round(row["sm_official"] or 0, 2) for row in details],
        "tonnage_split": [round(row["tonnage_split"] or 0, 2) for row in details],
        "tonnage_official": [round(row["tonnage_official"] or 0, 2) for row in details],
        "sm_diff": [round(row["sm_diff"] or 0, 3) for row in details],
        "tonnage_diff": [round(row["tonnage_diff"] or 0, 2) for row in details],
    }

    return JsonResponse({
        "compare": compare,
        "details": details
    }, safe=False)

def allChartCoa(request):
    filter_type = request.GET.get('filter_type')
    year        = request.GET.get('year')
    month       = request.GET.get('month')
    typeFilter  = request.GET.get('materialFilter')

    base_query = """
        SELECT 
            TRIM(t1.code_lot) AS code_lot,
            TRIM(t1.barge_code) AS barge_code,
            CONCAT(TRIM(t1.barge_code), '/', RIGHT(TRIM(t1.code_lot), 3)) AS lot_barge,
            COALESCE(SUM(t1.tonnage), 0) AS tonnage_split,              
            COALESCE(SUM(t1.tonnage * t1.ni) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.ni IS NOT NULL THEN t1.tonnage ELSE 0 END),0), 0) AS ni_split,
            COALESCE(SUM(t1.tonnage * t1.fe) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.fe IS NOT NULL THEN t1.tonnage ELSE 0 END),0), 0) AS fe_split,
            COALESCE(SUM(t1.tonnage * t1.mgo) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.mgo IS NOT NULL THEN t1.tonnage ELSE 0 END),0), 0) AS mgo_split,
            COALESCE(SUM(t1.tonnage * t1.sio2) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.sio2 IS NOT NULL THEN t1.tonnage ELSE 0 END),0), 0) AS sio2_split,
            COALESCE(SUM(t1.tonnage * t1.sm) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.sm IS NOT NULL THEN t1.tonnage ELSE 0 END),0), 0) AS sm_split,
            COALESCE(t2.tonnage_official, 0) AS tonnage_official,
            COALESCE(t2.ni, 0) AS ni_official,
            COALESCE(t2.fe, 0) AS fe_official,
            COALESCE(t2.mgo, 0) AS mgo_official,
            COALESCE(t2.sio2, 0) AS sio2_official,
            COALESCE(t2.sm, 0) AS sm_official,
            ABS(COALESCE(SUM(t1.tonnage) - t2.tonnage_official, 0)) AS tonnage_diff,
            COALESCE(((SUM(t1.tonnage * t1.ni) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.ni IS NOT NULL THEN t1.tonnage ELSE 0 END), 0)) - t2.ni) / NULLIF(t2.ni, 0) * 100, 0) AS ni_diff,
            COALESCE(((SUM(t1.tonnage * t1.fe) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.fe IS NOT NULL THEN t1.tonnage ELSE 0 END), 0)) - t2.fe) / NULLIF(t2.fe, 0) * 100, 0) AS fe_diff,
            COALESCE(((SUM(t1.tonnage * t1.mgo) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.mgo IS NOT NULL THEN t1.tonnage ELSE 0 END), 0)) - t2.mgo) / NULLIF(t2.mgo, 0) * 100, 0) AS mgo_diff,
            COALESCE(((SUM(t1.tonnage * t1.sio2) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.sio2 IS NOT NULL THEN t1.tonnage ELSE 0 END), 0)) - t2.sio2) / NULLIF(t2.sio2, 0) * 100, 0) AS sio2_diff,
            COALESCE(((SUM(t1.tonnage * t1.sm) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.sm IS NOT NULL THEN t1.tonnage ELSE 0 END), 0)) - t2.sm) / NULLIF(t2.sm, 0) * 100, 0) AS sm_diff
        FROM details_selling_barge_split t1
        LEFT JOIN (
            SELECT 
                product_code,
                COALESCE(SUM(tonnage), 0) AS tonnage_official,
                COALESCE(SUM(ni), 0) AS ni,
                COALESCE(SUM(fe), 0) AS fe,
                COALESCE(SUM(mgo), 0) AS mgo,
                COALESCE(SUM(sio2), 0) AS sio2,
                COALESCE(SUM(sm), 0) AS sm,
                type_selling
            FROM sellings_official_view
            GROUP BY product_code, type_selling
        ) AS t2 ON t1.code_lot = t2.product_code
        WHERE 1=1
    """

    filters = []


    # --- Monthly ---
    if filter_type == 'monthly' and year and month:
        filters.append(f"EXTRACT(YEAR FROM t1.date_barge_out) = {year} "
                       f"AND EXTRACT(MONTH FROM t1.date_barge_out) = {month}")

    # --- Yearly ---
    elif filter_type == 'yearly' and year:
        filters.append(f"EXTRACT(YEAR FROM t1.date_barge_out) = {year}")

    # --- All ---
    elif filter_type == 'all':
        pass  # tidak ada filter tambahan

    else:
        return JsonResponse({'error': 'Invalid or incomplete filter parameters'}, status=400)

    # Filter tambahan (material type)
    if typeFilter:
        filters.append(f"t1.sale_adjust = '{typeFilter}'")

    # Gabungkan filter ke query
    if filters:
        base_query += " AND " + " AND ".join(filters)

    # Grouping akhir
    base_query += """
        GROUP BY t1.code_lot, t1.barge_code,
                 t2.tonnage_official, 
                 t2.ni,t2.fe,t2.mgo,t2.sio2,t2.sm
        ORDER BY t1.code_lot ASC
    """

    # Eksekusi query
    df = pd.read_sql_query(base_query, connections['kqms_db'])
    details = df.to_dict(orient="records")
    
    compare = {
        "x_data"            : [row["lot_barge"] for row in details],
        "y_data"            : [row["barge_code"] for row in details],
        "y_split_ni"        : [round(row["ni_split"] or 0, 2) for row in details],
        "y_official_ni"     : [round(row["ni_official"] or 0, 2) for row in details],
        "y_split_fe"        : [round(row["fe_split"] or 0, 2) for row in details],
        "y_official_fe"     : [round(row["fe_official"] or 0, 2) for row in details],
        "y_split_mgo"       : [round(row["mgo_split"] or 0, 2) for row in details],
        "y_official_mgo"    : [round(row["mgo_official"] or 0, 2) for row in details],
        "y_split_sio2"      : [round(row["sio2_split"] or 0, 2) for row in details],
        "y_official_sio2"   : [round(row["sio2_official"] or 0, 2) for row in details],
        "y_split_sm"        : [round(row["sm_split"] or 0, 2) for row in details],
        "y_official_sm"     : [round(row["sm_official"] or 0, 2) for row in details],
        "tonnage_split"     : [round(row["tonnage_split"] or 0, 2) for row in details],
        "tonnage_official"  : [round(row["tonnage_official"] or 0, 2) for row in details],
        "tonnage_diff"      : [round(row["tonnage_diff"] or 0, 2) for row in details],
        "ni_diff"           : [round(row["ni_diff"] or 0, 3) for row in details],
        "fe_diff"           : [round(row["fe_diff"] or 0, 3) for row in details],
        "mgo_diff"          : [round(row["mgo_diff"] or 0, 3) for row in details],
        "sio2_diff"         : [round(row["sio2_diff"] or 0, 3) for row in details],
        "sm_diff"           : [round(row["sm_diff"] or 0, 3) for row in details]
    }

    return JsonResponse({
        "compare": compare,
        "details": details
    }, safe=False)
