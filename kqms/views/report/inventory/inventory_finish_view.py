from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.db import connections
import json 
from kqms.utils.class_ore import get_grade_by_rules
from kqms.utils.db_utils import get_db_vendor

# Memanggil fungsi utility
db_vendor = get_db_vendor('kqms_db')

@login_required
def inventory_finished_page(request):
    return render(request, 'admin-mgoqa/inventrory/inventory_finished.html')

# Group by Stockpile
@login_required
def stockpile_finished_page(request):
    return render(request, 'admin-mgoqa/inventrory/inventory_stockpile_finished.html')


@login_required
def getInventoryFinished(request):
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
            WHERE t1.status_dome = 'Finished'
            {where_clause}
            GROUP BY t1.stockpile, t1.pile_id, t1.total_ore, t1.released, 
                     t1.nama_material, t1.Ni, t1.Co, t1.Al2O3, t1.CaO, 
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
        WHERE t1.status_dome ='Finished'
        {where_clause}
        GROUP BY
            t1.stockpile, t1.pile_id, t1.total_ore, t1.released, 
            t1.nama_material, t1.Ni, t1.Co, t1.Al2O3, t1.CaO, 
            t1.Cr2O3, t1.Fe, t1.Mgo, t1.SiO2, t1.MC, t1.SM
        ORDER BY t1.nama_material ASC, t1.stockpile ASC
        LIMIT %s OFFSET %s;
    """

    params_with_paging = params + [per_page, offset]

    # Eksekusi query utama
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params_with_paging)
        columns = [col[0] for col in cursor.description]
        sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    for row in sql_data:
            row['grade'] = get_grade_by_rules(row['ni'], row['mgo'], row['fe'])

    # Pagination
    more_data = len(sql_data) == per_page
    total_pages = (total_data // per_page) + (1 if total_data % per_page > 0 else 0)

    return JsonResponse({
        'data': sql_data,
        'pagination': {
            'more': more_data,
            'total_pages': total_pages,
            'current_page': page,
            'total_data': total_data
        }
    })

@login_required
def getStockpileFinished(request):
    saleFilter = request.GET.get('saleFilter')
    areaFilter = request.GET.get('areaFilter', '[]')
    areaFilter = json.loads(areaFilter)  # parsing JSON → list

    # Pagination setup
    page = int(request.GET.get('page', 1))
    per_page = 100
    offset = (page - 1) * per_page

    # --- Build base filters ---
    count_filters = ["t1.status_dome = 'Finished'"]  # default filter
    params = []

    if saleFilter:
        count_filters.append("t1.sale_adjust = %s")
        params.append(saleFilter)

    if areaFilter:  # pastikan areaFilter tidak kosong
        placeholders = ', '.join(['%s'] * len(areaFilter))
        count_filters.append(f"t1.stockpile IN ({placeholders})")
        params.extend(areaFilter)

    where_clause = " AND ".join(count_filters)

    # --- Count query ---
    count_query = f"""
        SELECT COUNT(*)
        FROM inventory_by_stockpile AS t1
        WHERE {where_clause}
    """

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(count_query, params)
        result = cursor.fetchone()
        total_data = result[0] if result else 0

    # --- Data query ---
    if db_vendor == 'postgresql':
        query = f"""
            WITH selling_sum AS (
                SELECT 
                    stockpile,
                    CASE
                        WHEN material = 'LIM' AND sale_adjust = 'HPAL' THEN 'LIM'
                        WHEN material = 'LIM' AND sale_adjust = 'RKEF' THEN 'SAP'
                        WHEN material = 'SAP' AND sale_adjust = 'HPAL' THEN 'LIM'
                        WHEN material = 'SAP' AND sale_adjust = 'RKEF' THEN 'SAP'
                        ELSE material
                    END AS mapped_material,
                    SUM(tonnage) AS total_selling
                FROM selling_by_stockpile
                WHERE (direct = 'No' OR direct IS NULL)
                  AND sale_dome = 'Finished'
                GROUP BY stockpile,
                         CASE
                             WHEN material = 'LIM' AND sale_adjust = 'HPAL' THEN 'LIM'
                             WHEN material = 'LIM' AND sale_adjust = 'RKEF' THEN 'SAP'
                             WHEN material = 'SAP' AND sale_adjust = 'HPAL' THEN 'LIM'
                             WHEN material = 'SAP' AND sale_adjust = 'RKEF' THEN 'SAP'
                             ELSE material
                         END
            )
            SELECT
                t1.stockpile,
                t1.nama_material,
                SUM(t1.total_ore) AS total_ore,
                SUM(t1.released) AS released,
                COALESCE(ROUND(s.total_selling::numeric, 2), 0) AS total_selling,
                ROUND((SUM(t1.total_ore) - COALESCE(s.total_selling, 0))::numeric, 2) AS balance,
                ROUND((SUM(t1.Ni::numeric    * t1.total_ore) / NULLIF(SUM(t1.total_ore),0))::numeric, 2) AS Ni,
                ROUND((SUM(t1.Co::numeric    * t1.total_ore) / NULLIF(SUM(t1.total_ore),0))::numeric, 2) AS Co,
                ROUND((SUM(t1.Al2O3::numeric * t1.total_ore) / NULLIF(SUM(t1.total_ore),0))::numeric, 2) AS Al2O3,
                ROUND((SUM(t1.CaO::numeric   * t1.total_ore) / NULLIF(SUM(t1.total_ore),0))::numeric, 2) AS CaO,
                ROUND((SUM(t1.Cr2O3::numeric * t1.total_ore) / NULLIF(SUM(t1.total_ore),0))::numeric, 2) AS Cr2O3,
                ROUND((SUM(t1.Fe::numeric    * t1.total_ore) / NULLIF(SUM(t1.total_ore),0))::numeric, 2) AS Fe,
                ROUND((SUM(t1.Mgo::numeric   * t1.total_ore) / NULLIF(SUM(t1.total_ore),0))::numeric, 2) AS Mgo,
                ROUND((SUM(t1.SiO2::numeric  * t1.total_ore) / NULLIF(SUM(t1.total_ore),0))::numeric, 2) AS SiO2,
                ROUND((SUM(t1.MC::numeric    * t1.total_ore) / NULLIF(SUM(t1.total_ore),0))::numeric, 2) AS MC,
                ROUND((SUM(t1.SM::numeric    * t1.total_ore) / NULLIF(SUM(t1.total_ore),0))::numeric, 2) AS SM
            FROM inventory_by_stockpile AS t1
            LEFT JOIN selling_sum s
                ON s.stockpile = t1.stockpile
               AND s.mapped_material = t1.nama_material
            WHERE {where_clause}
            GROUP BY 
                t1.stockpile, 
                t1.nama_material, 
                s.total_selling
            ORDER BY t1.nama_material ASC, t1.stockpile ASC
            LIMIT {per_page} OFFSET {offset};
        """
    else:
        raise ValueError("Unsupported database vendor.")

    # --- Execute data query ---
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params)
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            sql_data = []
            
    for row in sql_data:
        row['grade'] = get_grade_by_rules(row['ni'], row['mgo'], row['fe'])

    # --- Pagination metadata ---
    more_data = len(sql_data) == per_page
    total_pages = (total_data // per_page) + (1 if total_data % per_page > 0 else 0)

    return JsonResponse({
        'data': sql_data,
        'pagination': {
            'more': more_data,
            'total_pages': total_pages,
            'current_page': page,
            'total_data': total_data
        }
    })
