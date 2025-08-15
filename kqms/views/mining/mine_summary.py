
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ...models.mine_productions import mineProductions
from ...models.mine_productions_view import mineProductionsView
from django.shortcuts import render
from django.db.models import Count, Sum
from datetime import datetime
from django.db import connections, DatabaseError
from ...utils.db_utils import get_db_vendor
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
def mine_summary_page(request):
    today = datetime.today()
    first_day_of_month = today.replace(day=1) 
    context = {
        'start_date' : first_day_of_month.strftime('%Y-%m-%d'),
        'end_date'   : today.strftime('%Y-%m-%d'),
    }
    return render(request, 'admin-mine/summary/widget.html',context)

@login_required
def daily_summary(request):
    date_production = request.GET.get('date_production')

    queryset = mineProductions.objects.all()

    if date_production:
        queryset = queryset.filter(date_production=date_production)

    # Total keseluruhan
    total_result = queryset.aggregate(
        qty=Count('id'),
        bcm=Sum('bcm', default=0),
        tonnage=Sum('tonnage', default=0)
    )

    # Total per shift
    shift_result = queryset.values('shift').annotate(
        qty=Count('id'),
        bcm=Sum('bcm', default=0),
        tonnage=Sum('tonnage', default=0)
    )

    return JsonResponse({
        'total': {
            'Qty': total_result['qty'] or 0,
            'Bcm': round(total_result['bcm'] or 0, 2),
            'Tonnage': round(total_result['tonnage'] or 0, 2)
        },
        'by_shift': [
            {
                'Shift': row['shift'],
                'Qty': row['qty'] or 0,
                'Bcm': round(row['bcm'] or 0, 2),
                'Tonnage': round(row['tonnage'] or 0, 2)
            }
            for row in shift_result
        ]
    })

@login_required
def total_daily_summary(request):
    date_production = request.GET.get('date_production')
    db_vendor = connections['kqms_db'].vendor  # ambil vendor DB

    try:
        if db_vendor == 'postgresql':
            query = """
                SELECT 
                    shift,
                    COUNT(ritase) AS ritase,
                    SUM(tonnage) AS actual_data,
                    SUM(
                        COALESCE(topsoil, 0) + COALESCE(ob, 0) + COALESCE(lglo, 0) + COALESCE(mglo, 0) +
                        COALESCE(hglo, 0) + COALESCE(waste, 0) + COALESCE(mws, 0) + COALESCE(lgso, 0) +
                        COALESCE(mgso, 0) + COALESCE(hgso, 0) + COALESCE(lim, 0) + COALESCE(sap, 0) +  
                        COALESCE(quarry, 0) + COALESCE(ballast, 0) + COALESCE(biomass, 0)
                    ) AS plan_data
                FROM mine_productions
                LEFT JOIN plan_productions 
                    ON mine_productions.date_production = plan_productions.date_plan
                WHERE date_production = %s
                GROUP BY shift
            """
        else:
            raise ValueError("Unsupported database vendor.") 

        params = [date_production]

        # Eksekusi query
        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        # Olah hasil query
        by_shift = []
        total_qty = 0
        total_actual = 0
        total_plan = 0

        for shift, ritase, actual_data, plan_data in rows:
            by_shift.append({
                'Shift': shift,
                'Qty': int(ritase or 0),
                'Actual': round(float(actual_data or 0), 2),
                'Plan': round(float(plan_data or 0), 2)
            })
            total_qty += ritase or 0
            total_actual += actual_data or 0
            total_plan += plan_data or 0

        return JsonResponse({
            'total': {
                'Qty': int(total_qty),
                'Actual': round(float(total_actual), 2),
                'Plan': round(float(total_plan), 2)
            },
            'by_shift': by_shift
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@login_required
def total_daily_material(request):
    date  = request.GET.get('date')
    shift = request.GET.get('shift')
    db_vendor = connections['kqms_db'].vendor

    try:
        if db_vendor != 'postgresql':
            raise ValueError("Unsupported database vendor.")

        query = """
            SELECT 
                mp.shift,
                COUNT(mp.ritase) AS ritase,
                SUM(CASE WHEN mp.nama_material = 'LIM' THEN mp.tonnage ELSE 0 END)::numeric AS actual_lim,
                SUM(CASE WHEN mp.nama_material = 'SAP' THEN mp.tonnage ELSE 0 END)::numeric AS actual_sap,
                SUM(CASE WHEN mp.nama_material = 'Top Soil' THEN mp.tonnage ELSE 0 END)::numeric AS actual_topsoil,
                SUM(CASE WHEN mp.nama_material = 'OB' THEN mp.tonnage ELSE 0 END)::numeric AS actual_ob,
                SUM(CASE WHEN mp.nama_material = 'Waste' THEN mp.tonnage ELSE 0 END)::numeric AS actual_waste,
                SUM(CASE WHEN mp.nama_material IN ('Quarry', 'Ballast', 'Biomass') THEN mp.tonnage ELSE 0 END)::numeric AS actual_other,
                SUM(mp.tonnage)::numeric AS actual_total,

                SUM(COALESCE(pp.lim, 0))::numeric AS plan_lim,
                SUM(COALESCE(pp.sap, 0))::numeric AS plan_sap,
                SUM(COALESCE(pp.topsoil, 0))::numeric AS plan_topsoil,
                SUM(COALESCE(pp.ob, 0))::numeric AS plan_ob,
                SUM(COALESCE(pp.waste, 0))::numeric AS plan_waste,
                SUM(COALESCE(pp.quarry, 0) + COALESCE(pp.ballast, 0) + COALESCE(pp.biomass, 0))::numeric AS plan_other,
                SUM(
                    COALESCE(pp.lim, 0) + COALESCE(pp.sap, 0) + COALESCE(pp.topsoil, 0) + 
                    COALESCE(pp.ob, 0) + COALESCE(pp.waste, 0) +
                    COALESCE(pp.quarry, 0) + COALESCE(pp.ballast, 0) + COALESCE(pp.biomass, 0)
                )::numeric AS plan_total
            FROM mine_productions mp
            LEFT JOIN plan_productions pp
                ON mp.date_production = pp.date_plan
            WHERE mp.date_production = %s
        """

        params = [date]
        if shift:
            query += " AND mp.shift = %s"
            params.append(shift)

        query += " GROUP BY mp.shift ORDER BY mp.shift"

        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        # Agregasi total semua shift
        total_data = {
            "ore": {"actual": 0, "plan": 0},
            "topsoil": {"actual": 0, "plan": 0},
            "ob": {"actual": 0, "plan": 0},
            "waste": {"actual": 0, "plan": 0},
            "quarry": {"actual": 0, "plan": 0},
            "others": {"actual": 0, "plan": 0},
        }

        total_qty = total_actual = total_plan = 0
        by_shift = []

        for r in rows:
            shift_name = r[0]
            ritase = r[1]

            actual_ore = r[2] + r[3]  # LIM + SAP = Ore
            plan_ore   = r[9] + r[10]

            actual_topsoil = r[4]
            plan_topsoil = r[11]

            actual_ob = r[5]
            plan_ob = r[12]

            actual_waste = r[6]
            plan_waste = r[13]

            actual_quarry = r[7]
            plan_quarry = r[14]

            # Others bisa disamakan dengan quarry jika beda definisi, tapi di sini 0
            actual_others = 0
            plan_others = 0

            actual_total = r[8]
            plan_total = r[15]

            by_shift.append({
                "Shift": shift_name,
                "Qty": int(ritase or 0),
                "Actual": round(float(actual_total or 0), 2),
                "Plan": round(float(plan_total or 0), 2)
            })

            total_qty += ritase or 0
            total_actual += actual_total or 0
            total_plan += plan_total or 0

            # Tambah ke total per material
            total_data["ore"]["actual"] += actual_ore or 0
            total_data["ore"]["plan"] += plan_ore or 0
            total_data["topsoil"]["actual"] += actual_topsoil or 0
            total_data["topsoil"]["plan"] += plan_topsoil or 0
            total_data["ob"]["actual"] += actual_ob or 0
            total_data["ob"]["plan"] += plan_ob or 0
            total_data["waste"]["actual"] += actual_waste or 0
            total_data["waste"]["plan"] += plan_waste or 0
            total_data["quarry"]["actual"] += actual_quarry or 0
            total_data["quarry"]["plan"] += plan_quarry or 0
            total_data["others"]["actual"] += actual_others or 0
            total_data["others"]["plan"] += plan_others or 0

        # Hitung persentase
        for k, v in total_data.items():
            v["ach"] = round((v["actual"] / v["plan"] * 100), 2) if v["plan"] else 0

        return JsonResponse({
            "total": {
                "Qty"   : int(total_qty),
                "Actual": round(float(total_actual), 2),
                "Plan"  : round(float(total_plan), 2)
            },
            "materials" : total_data,
            "by_shift"  : by_shift
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
def total_time_material_by_hour(request):
    date  = request.GET.get('date')
    shift = request.GET.get('shift')
    hour  = request.GET.get('hour')  # untuk filter jam t_load
    db_vendor = connections['kqms_db'].vendor

    try:
        if db_vendor != 'postgresql':
            raise ValueError("Unsupported database vendor.")

        query = """
            SELECT 
                mp.nama_material,
                mp.t_load AS jam,
                -- Actual hanya dari material yang sama
                SUM(
                    CASE 
                        WHEN mp.nama_material = 'LIM' THEN mp.tonnage
                        WHEN mp.nama_material = 'SAP' THEN mp.tonnage
                        WHEN mp.nama_material = 'Top Soil' THEN mp.tonnage
                        WHEN mp.nama_material = 'OB' THEN mp.tonnage
                        WHEN mp.nama_material = 'Waste' THEN mp.tonnage
                        WHEN mp.nama_material IN ('Quarry', 'Ballast', 'Biomass') THEN mp.tonnage
                        ELSE 0
                    END
                )::numeric AS actual,
                -- Plan dibagi per 22 jam
                (SUM(
                    CASE 
                        WHEN mp.nama_material = 'LIM' THEN COALESCE(pp.lim, 0)
                        WHEN mp.nama_material = 'SAP' THEN COALESCE(pp.sap, 0)
                        WHEN mp.nama_material = 'Top Soil' THEN COALESCE(pp.topsoil, 0)
                        WHEN mp.nama_material = 'OB' THEN COALESCE(pp.ob, 0)
                        WHEN mp.nama_material = 'Waste' THEN COALESCE(pp.waste, 0)
                        WHEN mp.nama_material IN ('Quarry', 'Ballast', 'Biomass') THEN 
                            COALESCE(pp.quarry, 0) + COALESCE(pp.ballast, 0) + COALESCE(pp.biomass, 0)
                        ELSE 0
                    END
                ) / 22)::numeric AS plan_per_hour
            FROM mine_productions mp
            LEFT JOIN plan_productions pp 
                ON mp.date_production = pp.date_plan
            WHERE mp.date_production = %s
        """

        params = [date]

        if shift:
            query += " AND mp.shift = %s"
            params.append(shift)

        if hour:
            query += " AND mp.t_load = %s"
            params.append(hour)

        query += " GROUP BY mp.nama_material, jam ORDER BY jam"

        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        result = []
        for r in rows:
            actual = float(r[2] or 0)
            plan   = float(r[3] or 0)
            ach    = round((actual / plan * 100), 2) if plan > 0 else 0

            result.append({
                "material"      : r[0],
                "hour"          : int(r[1]),
                "actual"        : actual,
                "plan_per_hour" : plan,
                "ach"           : ach
            })

        return JsonResponse({"data": result})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
def total_material_by_hour(request):
    date  = request.GET.get('date')
    shift = request.GET.get('shift')
    db_vendor = connections['kqms_db'].vendor

    try:
        if db_vendor != 'postgresql':
            raise ValueError("Unsupported database vendor.")

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
                TO_CHAR(make_time(t_load::int, 0, 0), 'HH24') AS t_load_time,
                SUM(mp.tonnage)::numeric AS total_actual,
                (SUM(
                    COALESCE(pp.lim,0) + COALESCE(pp.sap,0) + COALESCE(pp.topsoil,0) +
                    COALESCE(pp.ob,0) + COALESCE(pp.waste,0) +
                    COALESCE(pp.quarry,0) + COALESCE(pp.ballast,0) + COALESCE(pp.biomass,0)
                ) / 22)::numeric AS total_plan_per_hour
            FROM mine_productions mp
            LEFT JOIN plan_productions pp
                ON mp.date_production = pp.date_plan
            WHERE mp.date_production = %s
            {}
            GROUP BY t_load
        )
        SELECT
            hs.hour_label AS id,
            hs.left_time,
            COALESCE(agg.total_actual, 0) AS total_actual,
            COALESCE(agg.total_plan_per_hour, 0) AS total_plan_per_hour,
            ROUND(
                CASE WHEN agg.total_plan_per_hour > 0
                     THEN (agg.total_actual / agg.total_plan_per_hour * 100)
                     ELSE 0
                END, 2
            ) AS ach
        FROM hour_series hs
        LEFT JOIN agg_data agg ON hs.left_time = agg.t_load_time
        ORDER BY hs.sort_order;
        """

        # jika shift ada, tambahkan kondisi AND
        shift_filter = ""
        params = [date]
        if shift:
            shift_filter = " AND mp.shift = %s"
            params.append(shift)

        query = query.format(shift_filter)

        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        result = []
        for r in rows:
            result.append({
                "hour"          : int(r[0]),
                "label"         : r[1],  # string HH24
                "actual"        : float(r[2] or 0),
                "plan_per_hour" : float(r[3] or 0),
                "ach"           : float(r[4] or 0)
            })

        return JsonResponse({"data": result})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# For Barginig
@login_required
def total_daily_summary_barging(request):
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
