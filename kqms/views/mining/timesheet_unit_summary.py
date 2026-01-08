from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.db import connections
import json 
from datetime import datetime
from ...utils.db_utils import get_db_vendor
 # Memanggil fungsi utility
db_vendor = get_db_vendor('kqms_db')


@login_required
def timesheet__summary_page(request):
    today = datetime.today()
    context = {
        'day_date' : today.strftime('%Y-%m-%d'),
    }
    return render(request, 'admin-mine/list-timesheet-summary.html', context)

# @login_required
def summary_hm_unit_kpi(request):
    date_start     = request.GET.get('date_start')
    date_end       = request.GET.get('date_end')
    categories_raw = request.GET.get('categories', '[]')

    try:
        categories = json.loads(categories_raw)
    except:
        categories = []


    # Optional validasi
    try:
        datetime.strptime(date_start, "%Y-%m-%d")
        datetime.strptime(date_end, "%Y-%m-%d")
    except ValueError:
        return JsonResponse({"error": "Invalid date format"}, status=400)

    try:
        if db_vendor != 'postgresql':
            raise ValueError("Unsupported database vendor.")

        query = """
            SELECT
                u.unit_code,
                TRIM(c.category) as category,
                -- FUEL
                COALESCE(SUM(f.volume), 0) AS fuel,
                -- DURATIONS
                COALESCE(SUM(CASE WHEN s.code = 'OPR' THEN d.duration_min END), 0) AS op,
                COALESCE(SUM(CASE WHEN s.code IN ('STB','SUPPORT','WX','SLP') THEN d.duration_min END), 0) AS st,
                COALESCE(SUM(CASE WHEN s.code = 'PM' THEN d.duration_min END), 0) AS mt,
                COALESCE(SUM(CASE WHEN s.code = 'BD' THEN d.duration_min END), 0) AS bd,
                COUNT(DISTINCT h.date) * 1440 AS total_time,
                -- MA = OP / (OP + MT + BD)
                ROUND(
                    COALESCE(
                        SUM(CASE WHEN s.code = 'OPR' THEN d.duration_min END)::numeric
                        /
                        NULLIF(SUM(CASE WHEN s.code IN ('OPR','PM','BD') THEN d.duration_min END), 0),
                    0) * 100, 2
                ) AS ma,
                -- PA = (OP + ST) / TOTAL
                ROUND(
                    COALESCE(
                        SUM(CASE WHEN s.code IN ('OPR','STB','SUPPORT','WX','SLP') THEN d.duration_min END)::numeric
                        / (COUNT(DISTINCT h.date) * 1440)
                    ) * 100,
                    2
                ) AS pa,
                -- UA = OP / (OP + ST)
                ROUND(
                    COALESCE(
                        SUM(CASE WHEN s.code = 'OPR' THEN d.duration_min END)::numeric
                        /
                        NULLIF(SUM(CASE WHEN s.code IN ('OPR','STB','SUPPORT','WX','SLP') THEN d.duration_min END), 0),
                    0
                ) * 100,
                2
                ) AS ua,
                -- EU = OP / TOTAL
                ROUND(
                    COALESCE(
                        SUM(CASE WHEN s.code = 'OPR' THEN d.duration_min END)::numeric
                        / (COUNT(DISTINCT h.date) * 1440), 0
                    ) * 100,
                    2
                ) AS eu
            FROM mine_hm_unit h
            LEFT JOIN mine_units u ON u.id = h.unit_id
            LEFT JOIN mine_hm_unit_detail d ON d.hm_unit_id = h.id
            LEFT JOIN units_categories c ON c.id = u.id_category
            LEFT JOIN mine_units_categories_status s ON s.id = d.status_id
            LEFT JOIN mine_units_fuel_consumption f 
                ON f.unit = u.unit_code
            AND f.date = h.date   -- PENTING: sinkron tanggal
            WHERE h.date BETWEEN %s AND %s
        """
        params  = [date_start,date_end]
        
        # filter kategori
        if categories:
            placeholders = ','.join(['%s'] * len(categories))
            query += f" AND LOWER(TRIM(c.category)) IN ({placeholders})"
            params.extend([c.lower().strip() for c in categories])

        # filter unit
        # if unit_code:
        #     query += f" AND u.unit_code IN ({','.join(['%s'] * len(unit_code))})"
        #     params.extend(unit_code)

        query += "GROUP BY h.id, u.unit_code,c.category ORDER BY u.unit_code"

        print("RAW:", categories_raw)
        print("PARSED:", categories)

        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        result = []
        for r in rows:
            result.append({
                "unit" : r[0],
                "category" : r[1],
                "fuel" : float(r[2] or 0),
                "op"   : float(r[3] or 0),
                "st"   : float(r[4] or 0),
                "mt"   : float(r[5] or 0),
                "bd"   : float(r[6] or 0),
                "time" : int(r[7] or 0),
                "ma"   : float(r[9] or 0),
                "pa"   : float(r[9] or 0),
                "ua"   : float(r[10] or 0),
                "eu"   : float(r[11] or 0),
            })

        return JsonResponse({
            "success" : True,
            "data"    : result
        })


    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
