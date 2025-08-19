
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ....models.mine_productions import mineProductions
from django.shortcuts import render
from django.db.models import Count, Sum
import pandas as pd
from datetime import datetime
from django.db import connections
from ....utils.db_utils import get_db_vendor
 # Memanggil fungsi utility
db_vendor = get_db_vendor('kqms_db')


def format_angka(jumlah):
    if jumlah >= 1_000_000_000:
        return f"{jumlah / 1_000_000_000:.2f} B"
    elif jumlah >= 1_000_000:
        return f"{jumlah / 1_000_000:.2f} M"
    elif jumlah >= 1_000:
        return f"{jumlah / 1_000:.2f} K"
    else:
        return str(jumlah)

@login_required
def daily_selling_summary_page(request):
    today = datetime.today()
    first_day_of_month = today.replace(day=1) 
    context = {
        'start_date' : first_day_of_month.strftime('%Y-%m-%d'),
        'end_date'   : today.strftime('%Y-%m-%d'),
    }
    return render(request, 'admin-selling/summary/widget.html',context)

@login_required
def total_daily_sublot(request):
    date      = request.GET.get('date')
    code_lot  = request.GET.get('code_lot')
    shift     = request.GET.get('shift')
    db_vendor = connections['kqms_db'].vendor

    try:
        if db_vendor != 'postgresql':
            raise ValueError("Unsupported database vendor.")

        base_query = """
            SELECT 
                shift,
                SUM(CASE WHEN code_sub = 'SL_01' THEN 1 ELSE 0 END)::numeric AS SL_01,
                SUM(CASE WHEN code_sub = 'SL_02' THEN 1 ELSE 0 END)::numeric AS SL_02,
                SUM(CASE WHEN code_sub = 'SL_03' THEN 1 ELSE 0 END)::numeric AS SL_03,
                SUM(CASE WHEN code_sub = 'SL_04' THEN 1 ELSE 0 END)::numeric AS SL_04,
                SUM(CASE WHEN code_sub = 'SL_05' THEN 1 ELSE 0 END)::numeric AS SL_05,
                COUNT(no_urut)::numeric AS total_sublot
            FROM ore_sellings_barging_temp
            WHERE  code_lot = %s
        """
        params = [ code_lot]

        # if shift:
        #     base_query += " AND shift = %s"
        #     params.append(shift)

        base_query += " GROUP BY shift ORDER BY shift"

        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(base_query, params)
            rows = cursor.fetchall()

        by_shift = []
        total_sl01 = total_sl02 = total_sl03 = total_sl04 = total_sl05 = total_qty = 0

        for r in rows:
            shift_name = r[0]
            sl_01 = int(r[1] or 0)
            sl_02 = int(r[2] or 0)
            sl_03 = int(r[3] or 0)
            sl_04 = int(r[4] or 0)
            sl_05 = int(r[5] or 0)
            total_sublot = int(r[6] or 0)

            by_shift.append({
                "Shift": shift_name,
                "SL_01": sl_01,
                "SL_02": sl_02,
                "SL_03": sl_03,
                "SL_04": sl_04,
                "SL_05": sl_05,
                "Total": total_sublot,
            })

            total_sl01 += sl_01
            total_sl02 += sl_02
            total_sl03 += sl_03
            total_sl04 += sl_04
            total_sl05 += sl_05
            total_qty  += total_sublot

        # bentuk struktur "sublots"
        sublots = {
            "SL_01": {"actual": total_sl01},
            "SL_02": {"actual": total_sl02},
            "SL_03": {"actual": total_sl03},
            "SL_04": {"actual": total_sl04},
            "SL_05": {"actual": total_sl05},
            "total": {"actual": total_qty}
        }

        return JsonResponse({
            "sublots" : sublots,
            "by_shift": by_shift
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# For Barginig
@login_required
def total_daily_summary_quick(request):
    date_production = request.GET.get('date_production')
    db_vendor = connections['kqms_db'].vendor  # ambil vendor DB

    try:
        if db_vendor != 'postgresql':
            raise ValueError("Unsupported database vendor.") 

        query = """
            SELECT 
                shift,
                COUNT(*) AS ritase_total,
                COUNT(CASE WHEN material = 'LIM' THEN 1 END) AS ritase_lim,
                COUNT(CASE WHEN material = 'SAP' THEN 1 END) AS ritase_sap,
                ROUND(COALESCE(SUM(CASE WHEN material = 'LIM' THEN tonnage ELSE 0 END), 0)::numeric, 2) AS tonnage_lim,
                ROUND(COALESCE(SUM(CASE WHEN material = 'SAP' THEN tonnage ELSE 0 END), 0)::numeric, 2) AS tonnage_sap,
                ROUND(COALESCE(SUM(tonnage), 0)::numeric, 2) AS total_tonnage
            FROM details_selling_barging_temp
            WHERE date_hauling = %s
            GROUP BY shift
            ORDER BY shift
        """

        params = [date_production]

        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        by_shift = []
        total_ritase_total = 0
        total_ritase_lim = 0
        total_ritase_sap = 0
        total_tonnage_lim = 0
        total_tonnage_sap = 0
        total_tonnage_all = 0

        for row in rows:
            shift, rit_total, rit_lim, rit_sap, ton_lim, ton_sap, total = row
            by_shift.append({
                'Shift': shift,
                'Ritase_Total': int(rit_total or 0),
                'Ritase_LIM': int(rit_lim or 0),
                'Ritase_SAP': int(rit_sap or 0),
                'Limonite': float(ton_lim or 0),
                'Saprolite': float(ton_sap or 0),
                'Total': float(total or 0)
            })
            total_ritase_total += rit_total or 0
            total_ritase_lim += rit_lim or 0
            total_ritase_sap += rit_sap or 0
            total_tonnage_lim += ton_lim or 0
            total_tonnage_sap += ton_sap or 0
            total_tonnage_all += total or 0

        return JsonResponse({
            'total': {
                'Ritase_Total': total_ritase_total,
                'Ritase_LIM': total_ritase_lim,
                'Ritase_SAP': total_ritase_sap,
                'Limonite': total_tonnage_lim,
                'Saprolite': total_tonnage_sap,
                'Total': total_tonnage_all
            },
            'by_shift': by_shift
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def total_time_barging_by_hour(request):
    date  = request.GET.get('date')
    shift = request.GET.get('shift')
    hour  = request.GET.get('hour')  # untuk filter jam t_load
    db_vendor = connections['kqms_db'].vendor

    try:
        if db_vendor != 'postgresql':
            raise ValueError("Unsupported database vendor.")

        query = """
            SELECT 
                material,
                EXTRACT(HOUR FROM time_hauling)::int AS jam,
                SUM(tonnage)::numeric AS actual
            FROM details_selling_barging_temp
            WHERE date_hauling = %s
        """
        params = [date]

        if shift:
            query += " AND shift = %s"
            params.append(shift)
        
        
        if hour:
            query += " AND EXTRACT(HOUR FROM time_hauling) = %s"
            params.append(hour)

        query += " GROUP BY material, jam ORDER BY jam, material"

        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        result = []
        for r in rows:
            result.append({
                "material": r[0],
                "hour"    : int(r[1]),
                "actual"  : float(r[2] or 0)
            })

        return JsonResponse({"data": result})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def total_barging_by_hour(request):
    date  = request.GET.get('date')
    shift_param = request.GET.get('shift', '').strip()
    db_vendor = connections['kqms_db'].vendor

    try:
        if db_vendor != 'postgresql':
            raise ValueError("Unsupported database vendor.")

        # Normalisasi shift
        if shift_param in ['D', 'Day', 'd', 'day']:
            shift_db = 'Day'
        elif shift_param in ['N', 'Night', 'n', 'night']:
            shift_db = 'Night'
        else:
            shift_db = None  # ambil semua shift

        # Tentukan jam sesuai shift (optional, bisa dipakai di frontend)
        if shift_db == 'Day':
            hours = list(range(7, 19))
        elif shift_db == 'Night':
            hours = list(range(19, 24)) + list(range(0, 7))
        else:
            hours = list(range(0, 24))

        # Bangun query dasar
        query = """
        WITH working_hours AS (
            SELECT hour_label,
                   CASE WHEN hour_label >= 7 THEN hour_label ELSE hour_label + 24 END AS sort_order
            FROM generate_series(0,23) AS hour_label
        ),
        hour_series AS (
            SELECT hour_label,
                   sort_order,
                   TO_CHAR(make_time(hour_label,0,0),'HH24') AS label
            FROM working_hours
        ),
        agg_data AS (
            SELECT EXTRACT(HOUR FROM time_hauling)::int AS t_load,
                   SUM(CASE WHEN material='LIM' THEN tonnage ELSE 0 END)::numeric AS lim_actual,
                   SUM(CASE WHEN material='SAP' THEN tonnage ELSE 0 END)::numeric AS sap_actual
            FROM details_selling_barging_temp
            WHERE date_hauling = %s
        """

        params = [date]

        # tambahkan filter shift jika ada
        if shift_db:
            query += " AND shift = %s"
            params.append(shift_db)

        query += """
            GROUP BY t_load
        )
        SELECT hs.hour_label AS id,
               hs.label,
               COALESCE(agg.lim_actual,0) AS lim_actual,
               COALESCE(agg.sap_actual,0) AS sap_actual,
               COALESCE(agg.lim_actual,0) + COALESCE(agg.sap_actual,0) AS total_actual
        FROM hour_series hs
        LEFT JOIN agg_data agg ON hs.hour_label = agg.t_load
        ORDER BY hs.sort_order;
        """

        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        result = []
        for r in rows:
            result.append({
                "hour"  : int(r[0]),
                "label" : r[1],
                "lim"   : float(r[2] or 0),
                "sap"   : float(r[3] or 0),
                "total" : float(r[4] or 0)
            })

        return JsonResponse({"data": result})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
