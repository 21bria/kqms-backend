from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import connections
import json 
from ....utils.db_utils import get_db_vendor
from django.shortcuts import render

# Memanggil fungsi utility
db_vendor = get_db_vendor('kqms_db')

@login_required
def inventory_all_status_page(request):
    return render(request, 'admin-mgoqa/inventrory/inventory_all_status.html')


@login_required
def getInventoryAllStatus(request):
    saleFilter   = request.GET.get('saleFilter')
    areaFilter  = request.GET.get('areaFilter', '[]')  
    pointFilter = request.GET.get('pointFilter', '[]') 

    # Parsing JSON
    areaFilter  = json.loads(areaFilter)  
    pointFilter = json.loads(pointFilter) 

    # Pagination setup
    page = int(request.GET.get('page', 1))
    per_page = 100
    offset = (page - 1) * per_page

    # Siapkan filter dinamis
    filters = []
    params = []

    if saleFilter:
        filters.append("t1.sale_adjust = %s")
        params.append(saleFilter)

    if areaFilter:
        filters.append(f"t1.stockpile IN ({', '.join(['%s'] * len(areaFilter))})")
        params.extend(areaFilter)

    if pointFilter:
        filters.append(f"t1.pile_id IN ({', '.join(['%s'] * len(pointFilter))})")
        params.extend(pointFilter)

    where_clause = ""
    if filters:
        where_clause = " AND " + " AND ".join(filters)

    # == SQL untuk menghitung total data ==
    count_query = f"""
        SELECT COUNT(*)
        FROM (
            SELECT t1.stockpile, t1.pile_id
            FROM inventory_by_dome AS t1
            LEFT JOIN selling_by_dome AS t2 
                ON t2.stockpile = t1.stockpile 
                AND t2.dome = t1.pile_id
             WHERE 1=1
            {where_clause}
            GROUP BY t1.stockpile, t1.pile_id, t1.total_ore, t1.released, 
                     t1.nama_material, t1.status_dome,  t1.Ni, t1.Co, t1.Al2O3, t1.CaO, 
                     t1.Cr2O3, t1.Fe, t1.Mgo, t1.SiO2, t1.MC, t1.SM
        ) AS sub
    """

    # Eksekusi count query
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(count_query, params)
        result = cursor.fetchone()
        total_data = result[0] if result else 0

    # == SQL utama untuk ambil data ==
    query = f"""
        SELECT
            t1.stockpile,
            t1.pile_id,
            t1.total_ore,
            t1.released,
            t1.nama_material,
            t1.status_dome,
            COALESCE(ROUND(SUM(
                CASE
                    WHEN t1.nama_material = 'LIM' AND t2.material = 'SAP' THEN t2.tonnage
                    WHEN t1.nama_material = 'SAP' AND t2.material = 'LIM' THEN t2.tonnage
                    WHEN t1.nama_material = t2.material THEN t2.tonnage
                    ELSE 0
                END
            )::numeric, 2), 0) AS total_selling,
            ROUND((
                t1.total_ore - COALESCE(SUM(
                    CASE
                        WHEN t1.nama_material = 'LIM' AND t2.material = 'SAP' THEN t2.tonnage
                        WHEN t1.nama_material = 'SAP' AND t2.material = 'LIM' THEN t2.tonnage
                        WHEN t1.nama_material = t2.material THEN t2.tonnage
                        ELSE 0
                    END
                ), 0)
            )::numeric, 2) AS balance,
            t1.Ni,
            t1.Co,
            t1.Al2O3,
            t1.CaO,
            t1.Cr2O3,
            t1.Fe,
            t1.Mgo,
            t1.SiO2,
            t1.MC,
            t1.SM
        FROM inventory_by_dome AS t1
        LEFT JOIN selling_by_dome AS t2 
            ON t2.stockpile = t1.stockpile 
            AND t2.dome = t1.pile_id
        WHERE 1=1
        {where_clause}
        GROUP BY
            t1.stockpile, t1.pile_id, t1.total_ore, t1.released, 
            t1.nama_material,t1.status_dome, t1.Ni, t1.Co, t1.Al2O3, t1.CaO, 
            t1.Cr2O3, t1.Fe, t1.Mgo, t1.SiO2, t1.MC, t1.SM
        ORDER BY t1.status_dome DESC,t1.nama_material ASC, t1.stockpile ASC
        LIMIT %s OFFSET %s;
    """

    params_with_paging = params + [per_page, offset]

    # Eksekusi query utama
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params_with_paging)
        columns = [col[0] for col in cursor.description]
        sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]

    # === Query summary (tanpa LIMIT/OFFSET) ===
    summary_query = f"""
        SELECT
            ROUND(SUM(t1.total_ore)::numeric, 2) AS total_ore,
            ROUND(SUM(t1.released)::numeric, 2) AS total_released,
            ROUND(SUM(t1.released::numeric * t1.ni::numeric)::numeric, 2) AS sumprod_ni,
            ROUND(SUM(t1.released::numeric * t1.fe::numeric)::numeric, 2) AS sumprod_fe,
            ROUND(SUM(t1.released::numeric * t1.al2o3::numeric)::numeric, 2) AS sumprod_al2o3,
		    ROUND(SUM(t1.released::numeric * t1.co::numeric)::numeric, 2) AS sumprod_co,
		    ROUND(SUM(t1.released::numeric * t1.mgo::numeric)::numeric, 2) AS sumprod_mgo,
		    ROUND(SUM(t1.released::numeric * t1.sio2::numeric)::numeric, 2) AS sumprod_sio2,
		    ROUND(SUM(t1.released::numeric * t1.cao::numeric)::numeric, 2) AS sumprod_cao,
		    ROUND(SUM(t1.released::numeric * t1.cr2o3::numeric)::numeric, 2) AS sumprod_cr2o3,
		    ROUND(SUM(t1.released::numeric * t1.mc::numeric)::numeric, 2) AS sumprod_mc
        FROM inventory_by_dome t1
        WHERE 1=1
        {where_clause}
    """

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(summary_query, params)
        summary_row = cursor.fetchone()   

    # === Query summary Selling (tanpa LIMIT/OFFSET) ===
    selling_query = f"""
        SELECT
            ROUND(SUM(
                CASE
                    WHEN t1.nama_material = 'LIM' AND t2.material = 'SAP' THEN t2.tonnage
                    WHEN t1.nama_material = 'SAP' AND t2.material = 'LIM' THEN t2.tonnage
                    WHEN t1.nama_material = t2.material THEN t2.tonnage
                    ELSE 0
                END
            )::numeric, 2) AS total_selling
        FROM inventory_by_dome AS t1
        LEFT JOIN selling_by_dome AS t2
            ON t2.stockpile = t1.stockpile AND t2.dome = t1.pile_id
        WHERE 1=1
        {where_clause}
    """

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(selling_query, params)
        selling_row = cursor.fetchone() 

    # === Proses summary di backend ===
    total_ore       = float(summary_row[0] or 0)
    total_released  = float(summary_row[1] or 0)
    sumprod = {
        'ni'    : float(summary_row[2] or 0),
        'fe'    : float(summary_row[3] or 0),
        'al2o3' : float(summary_row[4] or 0),
        'co'    : float(summary_row[5] or 0),
        'mgo'   : float(summary_row[6] or 0),
        'sio2'  : float(summary_row[7] or 0),
        'cao'   : float(summary_row[8] or 0),
        'cr2o3' : float(summary_row[9] or 0),
        'mc'    : float(summary_row[10] or 0),
        # 'sm': float(summary_row[10] or 0),
    }

    avg_grade = {
        k: round((v / total_released), 3) if total_released else 0
        for k, v in sumprod.items()
    }

    total_selling = float(selling_row[0] or 0)

    #  perhitungan balance di backend
    balance = round(total_ore - total_selling, 2)

    # Pagination
    more_data   = len(sql_data) == per_page
    total_pages = (total_data // per_page) + (1 if total_data % per_page > 0 else 0)

    return JsonResponse({
        'data': sql_data,
        'summary': {
            'total_ore'     : round(total_ore, 2),
            'total_released': round(total_released, 2),
            'total_selling' : round(total_selling, 2),
            'balance'       : round(balance, 2),
            'avg_grade'     : avg_grade
        },
        'pagination': {
            'more'          : more_data,
            'total_pages'   : total_pages,
            'current_page'  : page,
            'total_data'    : total_data
        }
    })

