from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import connections
import json 
from kqms.utils.db_utils import get_db_vendor
from kqms.utils.class_ore import get_grade_by_rules
from django.shortcuts import render
from decimal import Decimal

# Memanggil fungsi utility
db_vendor = get_db_vendor('kqms_db')

@login_required
def inventory_all_page(request):
    return render(request, 'admin-mgoqa/inventrory/inventory_all.html')

@login_required
def inventory_hpal_page(request):
    return render(request, 'admin-mgoqa/inventrory/inventory_hpal.html')

@login_required
def inventory_rkef_page(request):
    return render(request, 'admin-mgoqa/inventrory/inventory_rkef.html')

# Group by Stockpile
@login_required
def inventory_stockpile_page(request):
    return render(request, 'admin-mgoqa/inventrory/inventory_stockpile_all.html')

@login_required
def inventory_stockpile_hpal(request):
    return render(request, 'admin-mgoqa/inventrory/inventory_stockpile_hpal.html')

@login_required
def inventory_stockpile_rkef(request):
    return render(request, 'admin-mgoqa/inventrory/inventory_stockpile_rkef.html')

@login_required
def getInventoryAll(request):
    saleFilter   = request.GET.get('saleFilter')
    areaFilter   = json.loads(request.GET.get('areaFilter', '[]'))
    pointFilter  = json.loads(request.GET.get('pointFilter', '[]'))

    # Pagination setup
    page = int(request.GET.get('page', 1))
    per_page = 100
    offset = (page - 1) * per_page

    # === Filter Dinamis ===
    filters = []
    params  = []

    if saleFilter:
        filters.append("t1.sale_adjust = %s")
        params.append(saleFilter)

    if areaFilter:
        filters.append(f"t1.stockpile IN ({', '.join(['%s'] * len(areaFilter))})")
        params.extend(areaFilter)

    if pointFilter:
        filters.append(f"t1.pile_id IN ({', '.join(['%s'] * len(pointFilter))})")
        params.extend(pointFilter)

    where_clause = " AND " + " AND ".join(filters) if filters else ""

    # === Count Query pakai subquery + GROUP BY ===
    count_query = f"""
        SELECT COUNT(*)
        FROM (
            SELECT t1.stockpile, t1.pile_id
            FROM inventory_by_dome AS t1
            LEFT JOIN selling_by_dome AS t2
                ON t2.stockpile = t1.stockpile
                AND t2.dome = t1.pile_id
            WHERE t1.status_dome != 'Finished'
            {where_clause}
            GROUP BY t1.stockpile, t1.pile_id, t1.total_ore, t1.released,
                     t1.nama_material, t1.Ni, t1.Co, t1.Al2O3, t1.CaO,
                     t1.Cr2O3, t1.Fe, t1.Mgo, t1.SiO2, t1.MC, t1.SM
        ) AS sub
    """
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(count_query, params)
        total_data = cursor.fetchone()[0]

    # === Main Query pakai SUM CASE ===
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
            ROUND((t1.total_ore - COALESCE(SUM(
                CASE
                    WHEN t1.nama_material = 'LIM' AND t2.material = 'SAP' THEN t2.tonnage
                    WHEN t1.nama_material = 'SAP' AND t2.material = 'LIM' THEN t2.tonnage
                    WHEN t1.nama_material = t2.material THEN t2.tonnage
                    ELSE 0
                END
            ), 0))::numeric, 2) AS balance,
            t1.Ni, t1.Co, t1.Al2O3, t1.CaO, t1.Cr2O3,
            t1.Fe, t1.Mgo, t1.SiO2, t1.MC, t1.SM
        FROM inventory_by_dome AS t1
        LEFT JOIN selling_by_dome AS t2
            ON t2.stockpile = t1.stockpile
            AND t2.dome = t1.pile_id
        WHERE t1.status_dome != 'Finished'
        {where_clause}
        GROUP BY
            t1.stockpile, t1.pile_id, t1.total_ore, t1.released,
            t1.nama_material, t1.Ni, t1.Co, t1.Al2O3, t1.CaO,
            t1.Cr2O3, t1.Fe, t1.Mgo, t1.SiO2, t1.MC, t1.SM
        ORDER BY t1.nama_material ASC, t1.stockpile ASC
        LIMIT %s OFFSET %s;
    """
    params_with_paging = params + [per_page, offset]

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params_with_paging)
        columns = [col[0] for col in cursor.description]
        sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    for row in sql_data:
        row['grade'] = get_grade_by_rules(row['ni'], row['mgo'], row['fe'])

    # === Konversi angka ke float ===
    for item in sql_data:
        for field in [
            'total_ore', 'released', 'total_selling', 'balance',
            'ni', 'co', 'al2o3', 'cao', 'cr2o3', 'fe', 'mgo', 'sio2', 'mc', 'sm'
        ]:
            if field in item and item[field] is not None:
                item[field] = float(item[field])

    # === Summary sederhana ===
    total_released = sum(item['released'] for item in sql_data if item['released'])
    total_ore      = sum(item['total_ore'] for item in sql_data if item['total_ore'])
    total_selling  = sum(item['total_selling'] for item in sql_data if item['total_selling'])
    total_balance  = sum(item['balance'] for item in sql_data if item['balance'])

    def weighted_avg(field):
        return sum(item[field] * item['balance'] for item in sql_data if item['balance']) / total_balance if total_balance else 0

    summary = {
        'total_ore': total_ore,
        'total_released': total_released,
        'total_selling': total_selling,
        'total_balance': total_balance,
        'ni': weighted_avg('ni'),
        'co': weighted_avg('co'),
        'al2o3': weighted_avg('al2o3'),
        'cao': weighted_avg('cao'),
        'cr2o3': weighted_avg('cr2o3'),
        'fe': weighted_avg('fe'),
        'mgo': weighted_avg('mgo'),
        'sio2': weighted_avg('sio2'),
        'mc': weighted_avg('mc'),
    }

    # sm langsung dari summary
    summary['sm_ratio'] = summary['sio2'] / summary['mgo'] if summary['mgo'] else 0

    return JsonResponse({
        'data': sql_data,
        'summary': summary,
        'pagination': {
            'more': len(sql_data) == per_page,
            'total_pages' : (total_data // per_page) + (1 if total_data % per_page > 0 else 0),
            'current_page': page,
            'total_data'  : total_data
        }
    })

@login_required
def getInventoryHpal(request):
    areaFilter  = request.GET.get('areaFilter', '[]')
    pointFilter = request.GET.get('pointFilter', '[]')

    # Parsing JSON filter
    try:
        areaFilter  = json.loads(areaFilter) if areaFilter else []
        pointFilter = json.loads(pointFilter) if pointFilter else []
    except json.JSONDecodeError:
        areaFilter, pointFilter = [], []

    # Pagination setup
    page = int(request.GET.get('page', 1))
    per_page = 100
    offset = (page - 1) * per_page

    # Filters dinamis
    filters = ["t1.status_dome != 'Finished'", "t1.sale_adjust = 'HPAL'"]
    params = []

    if areaFilter:
        filters.append(f"t1.stockpile IN ({', '.join(['%s'] * len(areaFilter))})")
        params.extend(areaFilter)
    if pointFilter:
        filters.append(f"t1.pile_id IN ({', '.join(['%s'] * len(pointFilter))})")
        params.extend(pointFilter)

    # where_clause_sql = f"WHERE {' AND '.join(filters)}" if filters else ""
    where_clause_sql = " AND ".join(filters)

    # === Count query ===
    count_query = f"""
        SELECT COUNT(*)
        FROM (
            SELECT t1.stockpile, t1.pile_id
            FROM inventory_by_dome t1
            LEFT JOIN selling_by_dome t2
                ON t2.stockpile = t1.stockpile
            AND t2.dome = t1.pile_id
            AND t2.sale_adjust = 'HPAL'
            WHERE {where_clause_sql}
            GROUP BY t1.stockpile, t1.pile_id, t1.total_ore, t1.released, 
                    t1.nama_material, t1.Ni, t1.Co, t1.Al2O3, t1.CaO, 
                    t1.Cr2O3, t1.Fe, t1.Mgo, t1.SiO2, t1.MC, t1.SM
        ) AS sub
    """
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(count_query, params)
        total_data = cursor.fetchone()[0]

    # === Query utama ===
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
            t1.Ni, t1.Co, t1.Al2O3, t1.CaO, t1.Cr2O3,
            t1.Fe, t1.Mgo, t1.SiO2, t1.MC, t1.SM
        FROM inventory_by_dome t1
        LEFT JOIN selling_by_dome t2
            ON t2.stockpile = t1.stockpile
        AND t2.dome = t1.pile_id
        WHERE {where_clause_sql}
        GROUP BY
            t1.stockpile, t1.pile_id, t1.total_ore, t1.released, 
            t1.nama_material, t1.Ni, t1.Co, t1.Al2O3, t1.CaO, 
            t1.Cr2O3, t1.Fe, t1.Mgo, t1.SiO2, t1.MC, t1.SM
        ORDER BY t1.nama_material ASC, t1.stockpile ASC
        LIMIT %s OFFSET %s;
    """

    params_with_paging = params + [per_page, offset]

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params_with_paging)
        columns = [col[0] for col in cursor.description]
        sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]

    # Hitung grade
    for row in sql_data:
        row['grade'] = get_grade_by_rules(row['ni'], row['mgo'], row['fe'])

    # Konversi ke float
    for item in sql_data:
        for field in [
            'total_ore', 'released', 'total_selling', 'balance',
            'ni', 'co', 'al2o3', 'cao', 'cr2o3', 'fe', 'mgo', 'sio2', 'mc', 'sm'
        ]:
            if field in item and item[field] is not None:
                item[field] = float(item[field])

    # Summary sederhana
    total_released = sum(item['released'] for item in sql_data)
    total_ore      = sum(item['total_ore'] for item in sql_data)
    total_selling  = sum(item['total_selling'] for item in sql_data)
    total_balance  = sum(item['balance'] for item in sql_data)

    def weighted_avg(field):
        return sum(item[field] * item['balance'] for item in sql_data) / total_balance if total_balance else 0

    summary = {
        'total_ore': total_ore,
        'total_released': total_released,
        'total_selling': total_selling,
        'total_balance': total_balance,
        'ni': weighted_avg('ni'),
        'co': weighted_avg('co'),
        'al2o3': weighted_avg('al2o3'),
        'cao': weighted_avg('cao'),
        'cr2o3': weighted_avg('cr2o3'),
        'fe': weighted_avg('fe'),
        'mgo': weighted_avg('mgo'),
        'sio2': weighted_avg('sio2'),
        'mc': weighted_avg('mc'),
    }
    summary['sm_ratio'] = summary['sio2'] / summary['mgo'] if summary['mgo'] else 0

    more_data = len(sql_data) == per_page
    total_pages = (total_data // per_page) + (1 if total_data % per_page > 0 else 0)

    return JsonResponse({
        'data': sql_data,
        'summary': summary,
        'pagination': {
            'more': more_data,
            'total_pages': total_pages,
            'current_page': page,
            'total_data': total_data
        }
    })

@login_required
def getInventoryRkef(request):
    areaFilter  = request.GET.get('areaFilter', '[]')
    pointFilter = request.GET.get('pointFilter', '[]')

    # Parsing JSON filter
    try:
        areaFilter  = json.loads(areaFilter) if areaFilter else []
        pointFilter = json.loads(pointFilter) if pointFilter else []
    except json.JSONDecodeError:
        areaFilter, pointFilter = [], []

    # Pagination setup
    page = int(request.GET.get('page', 1))
    per_page = 100
    offset = (page - 1) * per_page

    # Filters
    filters = ["t1.status_dome != 'Finished'", "t1.sale_adjust = 'RKEF'"]
    params = []

    if areaFilter:
        filters.append(f"t1.stockpile IN ({', '.join(['%s'] * len(areaFilter))})")
        params.extend(areaFilter)
    if pointFilter:
        filters.append(f"t1.pile_id IN ({', '.join(['%s'] * len(pointFilter))})")
        params.extend(pointFilter)

    where_clause = " AND ".join(filters)

    # == Count query ==
    count_query = f"""
        SELECT COUNT(*)
        FROM (
            SELECT t1.stockpile, t1.pile_id
            FROM inventory_by_dome t1
            LEFT JOIN selling_by_dome t2
                ON t2.stockpile = t1.stockpile
               AND t2.dome = t1.pile_id
               AND t2.sale_adjust = 'RKEF'
            WHERE {where_clause}
            GROUP BY t1.stockpile, t1.pile_id, t1.total_ore, t1.released, 
                     t1.nama_material, t1.Ni, t1.Co, t1.Al2O3, t1.CaO, 
                     t1.Cr2O3, t1.Fe, t1.Mgo, t1.SiO2, t1.MC, t1.SM
        ) AS sub
    """

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(count_query, params)
        result = cursor.fetchone()
        total_data = result[0] if result else 0

    # == Query utama ==
    query = f"""
        SELECT
            t1.stockpile,
            t1.pile_id,
            t1.total_ore,
            t1.released,
            t1.nama_material,
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
            t1.Ni, t1.Co, t1.Al2O3, t1.CaO, t1.Cr2O3,
            t1.Fe, t1.Mgo, t1.SiO2, t1.MC, t1.SM
        FROM inventory_by_dome t1
        LEFT JOIN selling_by_dome t2
            ON t2.stockpile = t1.stockpile
           AND t2.dome = t1.pile_id
           --AND t2.sale_adjust = 'RKEF'
        WHERE {where_clause}
        GROUP BY
            t1.stockpile, t1.pile_id, t1.total_ore, t1.released, 
            t1.nama_material, t1.Ni, t1.Co, t1.Al2O3, t1.CaO, 
            t1.Cr2O3, t1.Fe, t1.Mgo, t1.SiO2, t1.MC, t1.SM
        ORDER BY t1.nama_material ASC, t1.stockpile ASC
        LIMIT %s OFFSET %s;
    """

    params_with_paging = params + [per_page, offset]

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params_with_paging)
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            sql_data = []

     # Hitung grade
    for row in sql_data:
        row['grade'] = get_grade_by_rules(row['ni'], row['mgo'], row['fe'])

    # Konversi ke float
    for item in sql_data:
        for field in [
            'total_ore', 'released', 'total_selling', 'balance',
            'ni', 'co', 'al2o3', 'cao', 'cr2o3', 'fe', 'mgo', 'sio2', 'mc', 'sm'
        ]:
            if field in item and item[field] is not None:
                item[field] = float(item[field])

    # Summary sederhana
    total_released = sum(item['released'] for item in sql_data)
    total_ore      = sum(item['total_ore'] for item in sql_data)
    total_selling  = sum(item['total_selling'] for item in sql_data)
    total_balance  = sum(item['balance'] for item in sql_data)

    def weighted_avg(field):
        return sum(item[field] * item['balance'] for item in sql_data) / total_balance if total_balance else 0

    summary = {
        'total_ore': total_ore,
        'total_released': total_released,
        'total_selling': total_selling,
        'total_balance': total_balance,
        'ni': weighted_avg('ni'),
        'co': weighted_avg('co'),
        'al2o3': weighted_avg('al2o3'),
        'cao': weighted_avg('cao'),
        'cr2o3': weighted_avg('cr2o3'),
        'fe': weighted_avg('fe'),
        'mgo': weighted_avg('mgo'),
        'sio2': weighted_avg('sio2'),
        'mc': weighted_avg('mc'),
    }
    summary['sm_ratio'] = summary['sio2'] / summary['mgo'] if summary['mgo'] else 0

    more_data = len(sql_data) == per_page
    total_pages = (total_data // per_page) + (1 if total_data % per_page > 0 else 0)

    return JsonResponse({
        'data': sql_data,
        'summary': summary,
        'pagination': {
            'more': more_data,
            'total_pages': total_pages,
            'current_page': page,
            'total_data': total_data
        }
    })

@login_required
def getStockpileAll(request):
    saleFilter  = request.GET.get('saleFilter')
    pointFilter = json.loads(request.GET.get('pointFilter', '[]'))

    page     = int(request.GET.get('page', 1))
    per_page = 100
    offset   = (page - 1) * per_page

    filters = []
    params  = []

    if saleFilter:
        filters.append("t1.sale_adjust = %s")
        params.append(saleFilter)

    if pointFilter:
        filters.append(f"t1.pile_id IN ({','.join(['%s'] * len(pointFilter))})")
        params.extend(pointFilter)

    where_clause = " AND " + " AND ".join(filters) if filters else ""

    # ===================== COUNT =====================
    count_query = f"""
        SELECT COUNT(*)
        FROM (
            SELECT t1.stockpile, t1.nama_material
            FROM inventory_by_dome t1
            WHERE t1.status_dome != 'Finished'
            {where_clause}
            GROUP BY t1.stockpile, t1.nama_material
        ) x
    """

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(count_query, params)
        total_data = cursor.fetchone()[0]

    # ===================== MAIN QUERY =====================
    query = f"""
        WITH base AS (
            SELECT
                t1.stockpile,
                t1.nama_material,
                t1.total_ore::numeric AS tonnage,
                t1.released::numeric AS released,
                t1.Ni::numeric    AS ni,
                t1.Co::numeric    AS co,
                t1.Al2O3::numeric AS al2o3,
                t1.CaO::numeric   AS cao,
                t1.Cr2O3::numeric AS cr2o3,
                t1.Fe::numeric    AS fe,
                t1.Mgo::numeric   AS mgo,
                t1.SiO2::numeric  AS sio2,
                t1.MC::numeric   AS mc,
                COALESCE(
                    CASE
                        WHEN t1.nama_material = t2.material THEN t2.tonnage
                        WHEN t1.nama_material = 'LIM' AND t2.material = 'SAP' THEN t2.tonnage
                        WHEN t1.nama_material = 'SAP' AND t2.material = 'LIM' THEN t2.tonnage
                        ELSE 0
                    END, 0
                )::numeric AS selling
            FROM inventory_by_dome t1
            LEFT JOIN selling_by_dome t2
                ON t2.stockpile = t1.stockpile
                AND t2.dome = t1.pile_id
            WHERE t1.status_dome != 'Finished'
            {where_clause}
        )
        SELECT
            stockpile,
            nama_material,
            SUM(tonnage)         AS total_ore,
            SUM(released)        AS total_released,
            SUM(selling)         AS total_selling,
            SUM(tonnage-selling) AS balance,
            -- WEIGHTED AVERAGE (FINAL)
            SUM(ni    * (tonnage-selling)) / NULLIF(SUM(tonnage-selling),0) AS ni,
            SUM(co    * (tonnage-selling)) / NULLIF(SUM(tonnage-selling),0) AS co,
            SUM(al2o3 * (tonnage-selling)) / NULLIF(SUM(tonnage-selling),0) AS al2o3,
            SUM(cao   * (tonnage-selling)) / NULLIF(SUM(tonnage-selling),0) AS cao,
            SUM(cr2o3 * (tonnage-selling)) / NULLIF(SUM(tonnage-selling),0) AS cr2o3,
            SUM(fe    * (tonnage-selling)) / NULLIF(SUM(tonnage-selling),0) AS fe,
            SUM(mgo   * (tonnage-selling)) / NULLIF(SUM(tonnage-selling),0) AS mgo,
            SUM(sio2  * (tonnage-selling)) / NULLIF(SUM(tonnage-selling),0) AS sio2,
            SUM(mc    * (tonnage-selling)) / NULLIF(SUM(tonnage-selling),0) AS mc,
            SUM(sio2) / NULLIF(SUM(mgo),0) AS sm
        FROM base
        GROUP BY stockpile, nama_material
        ORDER BY stockpile, nama_material
        LIMIT %s OFFSET %s
    """

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params + [per_page, offset])
        columns = [c[0] for c in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]

    # ===================== POST PROCESS =====================
    for row in data:
        row['grade'] = get_grade_by_rules(row['ni'], row['mgo'], row['fe'])
        for k in row:
            if isinstance(row[k], Decimal):
                row[k] = float(row[k])

    # ===================== SUMMARY =====================
    total_balance = sum(i['balance'] for i in data)

    def wavg(field):
        return (
            sum(i[field] * i['balance'] for i in data) / total_balance
            if total_balance else 0
        )

    summary = {
        'total_ore': sum(i['total_ore'] for i in data),
        'total_released': sum(i['total_released'] for i in data),
        'total_selling': sum(i['total_selling'] for i in data),
        'total_balance': total_balance,
        'ni': wavg('ni'),
        'co': wavg('co'),
        'al2o3': wavg('al2o3'),
        'cao': wavg('cao'),
        'cr2o3': wavg('cr2o3'),
        'fe': wavg('fe'),
        'mgo': wavg('mgo'),
        'sio2': wavg('sio2'),
        'mc': wavg('mc'),
    }

    summary['sm_ratio'] = summary['sio2'] / summary['mgo'] if summary['mgo'] else 0

    return JsonResponse({
        'data': data,
        'summary': summary,
        'pagination': {
            'more': len(data) == per_page,
            'current_page': page,
            'total_pages': (total_data // per_page) + (1 if total_data % per_page else 0),
            'total_data': total_data
        }
    })


# @login_required
# def getStockpileAll(request):
#     saleFilter = request.GET.get('saleFilter')
#     areaFilter = request.GET.get('areaFilter', '[]')
#     areaFilter = json.loads(areaFilter)

#     # Pagination setup
#     page = int(request.GET.get('page', 1))
#     per_page = 100
#     offset = (page - 1) * per_page

#     # --- Build filters ---
#     count_filters = ["t1.status_dome = 'Continue'"]
#     params = []

#     if saleFilter:
#         count_filters.append("t1.sale_adjust = %s")
#         params.append(saleFilter)

#     if areaFilter:
#         placeholders = ', '.join(['%s'] * len(areaFilter))
#         count_filters.append(f"t1.stockpile IN ({placeholders})")
#         params.extend(areaFilter)

#     where_clause = " AND ".join(count_filters)

#     # --- Count query ---
#     count_query = f"""
#         SELECT COUNT(*)
#         FROM inventory_by_stockpile AS t1
#         WHERE {where_clause}
#     """

#     with connections['kqms_db'].cursor() as cursor:
#         cursor.execute(count_query, params)
#         result = cursor.fetchone()
#         total_data = result[0] if result else 0

#     # --- Data query (pakai mapping selling) ---
#     if db_vendor == 'postgresql':
#         query = f"""
#             WITH selling_sum AS (
#                 SELECT 
#                     stockpile,
#                     CASE
#                         WHEN material = 'LIM' AND sale_adjust = 'HPAL' THEN 'LIM'
#                         WHEN material = 'LIM' AND sale_adjust = 'RKEF' THEN 'LIM'
#                         WHEN material = 'SAP' AND sale_adjust = 'HPAL' THEN 'SAP'
#                         WHEN material = 'SAP' AND sale_adjust = 'RKEF' THEN 'SAP'
#                         ELSE material
#                     END AS mapped_material,
#                     SUM(tonnage) AS total_selling
#                 FROM selling_by_stockpile
#                 WHERE (direct = 'No' OR direct IS NULL)
#                   AND sale_dome !='Finished'
#                 GROUP BY stockpile,
#                          CASE
#                              WHEN material = 'LIM' AND sale_adjust = 'HPAL' THEN 'LIM'
#                              WHEN material = 'LIM' AND sale_adjust = 'RKEF' THEN 'LIM'
#                              WHEN material = 'SAP' AND sale_adjust = 'HPAL' THEN 'SAP'
#                              WHEN material = 'SAP' AND sale_adjust = 'RKEF' THEN 'SAP'
#                              ELSE material
#                          END
#             )
#             SELECT
#                 t1.stockpile,
#                 t1.nama_material,
#                 SUM(t1.total_ore) AS total_ore,
#                 SUM(t1.released) AS released,
#                 COALESCE(ROUND(s.total_selling::numeric, 2), 0) AS total_selling,
#                 ROUND((SUM(t1.total_ore) - COALESCE(s.total_selling, 0))::numeric, 2) AS balance,
#                 ROUND((SUM(t1.Ni::numeric    * t1.total_ore) / NULLIF(SUM(t1.total_ore),0))::numeric, 2) AS Ni,
#                 ROUND((SUM(t1.Co::numeric    * t1.total_ore) / NULLIF(SUM(t1.total_ore),0))::numeric, 2) AS Co,
#                 ROUND((SUM(t1.Al2O3::numeric * t1.total_ore) / NULLIF(SUM(t1.total_ore),0))::numeric, 2) AS Al2O3,
#                 ROUND((SUM(t1.CaO::numeric   * t1.total_ore) / NULLIF(SUM(t1.total_ore),0))::numeric, 2) AS CaO,
#                 ROUND((SUM(t1.Cr2O3::numeric * t1.total_ore) / NULLIF(SUM(t1.total_ore),0))::numeric, 2) AS Cr2O3,
#                 ROUND((SUM(t1.Fe::numeric    * t1.total_ore) / NULLIF(SUM(t1.total_ore),0))::numeric, 2) AS Fe,
#                 ROUND((SUM(t1.Mgo::numeric   * t1.total_ore) / NULLIF(SUM(t1.total_ore),0))::numeric, 2) AS Mgo,
#                 ROUND((SUM(t1.SiO2::numeric  * t1.total_ore) / NULLIF(SUM(t1.total_ore),0))::numeric, 2) AS SiO2,
#                 ROUND((SUM(t1.MC::numeric    * t1.total_ore) / NULLIF(SUM(t1.total_ore),0))::numeric, 2) AS MC,
#                 ROUND((SUM(t1.SM::numeric    * t1.total_ore) / NULLIF(SUM(t1.total_ore),0))::numeric, 2) AS SM
#             FROM inventory_by_stockpile AS t1
#             LEFT JOIN selling_sum s
#                 ON s.stockpile = t1.stockpile
#                AND s.mapped_material = t1.nama_material
#             WHERE {where_clause}
#             GROUP BY 
#                 t1.stockpile, 
#                 t1.nama_material, 
#                 s.total_selling
#             ORDER BY t1.nama_material ASC, t1.stockpile ASC
#             LIMIT {per_page} OFFSET {offset};
#         """
#     else:
#         raise ValueError("Unsupported database vendor.")

#     # --- Execute data query ---
#     with connections['kqms_db'].cursor() as cursor:
#         cursor.execute(query, params)
#         if cursor.description:
#             columns = [col[0] for col in cursor.description]
#             sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
#         else:
#             sql_data = []

#     # Hitung grade
#     for row in sql_data:
#         row['grade'] = get_grade_by_rules(row['ni'], row['mgo'], row['fe'])


#     # --- Convert decimals to float ---
#     for item in sql_data:
#         for field in [
#             'total_ore', 'released', 'total_selling', 'balance',
#             'ni', 'co', 'al2o3', 'cao', 'cr2o3', 'fe', 'mgo', 'sio2', 'mc', 'sm'
#         ]:
#             val = item.get(field)
#             if isinstance(val, Decimal):
#                 item[field] = float(val)
#             elif isinstance(val, (float, int)):
#                 item[field] = float(val)
#             elif isinstance(val, str) and val.replace('.', '', 1).isdigit():
#                 item[field] = float(val)

#     # --- Summary ---
#     total_released = sum(item['released'] for item in sql_data if item['released'])
#     total_ore      = sum(item['total_ore'] for item in sql_data if item['total_ore'])
#     total_selling  = sum(item['total_selling'] for item in sql_data if item['total_selling'])
#     total_balance  = sum(item['balance'] for item in sql_data if item['balance'])

#     def weighted_avg(field):
#         return sum(item[field] * item['balance'] for item in sql_data if item['balance']) / total_balance if total_balance else 0

#     sum_results = {
#         'total_ore': total_ore,
#         'total_released': total_released,
#         'total_selling': total_selling,
#         'total_balance': total_balance,
#         'ni': weighted_avg('ni'),
#         'co': weighted_avg('co'),
#         'al2o3': weighted_avg('al2o3'),
#         'cao': weighted_avg('cao'),
#         'cr2o3': weighted_avg('cr2o3'),
#         'fe': weighted_avg('fe'),
#         'mgo': weighted_avg('mgo'),
#         'sio2': weighted_avg('sio2'),
#         'mc': weighted_avg('mc'),
#         'sm': weighted_avg('sm'),
#     }

#     # --- Pagination metadata ---
#     more_data = len(sql_data) == per_page
#     total_pages = (total_data // per_page) + (1 if total_data % per_page > 0 else 0)

#     return JsonResponse({
#         'data': sql_data,
#         'summary': sum_results,
#         'pagination': {
#             'more': more_data,
#             'total_pages': total_pages,
#             'current_page': page,
#             'total_data': total_data
#         }
#     })


@login_required
def getStockpileHpal(request):
    materialFilter = request.GET.get('materialFilter')
    areaFilter = request.GET.get('areaFilter', '[]')

    if db_vendor == 'postgresql':
            query = """
                SELECT
                    t1.stockpile,
                    t1.total_ore,
                    t1.released,
                    t1.nama_material,
                    COALESCE(ROUND(t2.tonnage::numeric, 2), 0) AS total_selling,
                    ROUND((t1.released - COALESCE(t2.tonnage, 0))::numeric, 2) AS balance,
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
                WHERE t1.status_dome != 'Finished' 
                        AND t1.sale_adjust='HPAL'
            """
    else:
        raise ValueError("Unsupported database vendor.")

    filters = []
    params  = []

    if materialFilter:
        filters.append("t1.nama_material = %s")
        params.append(materialFilter)

    if areaFilter:
        filters.append("t1.stockpile = %s")
        params.append(areaFilter)

    if filters:
        query += " AND " + " AND ".join(filters)

    query += " ORDER BY t1.nama_material ASC, t1.stockpile ASC;"

    
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query)
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            sql_data = []
    # print(sql_data)  # Cetak hasil query
    
    return JsonResponse({'data': sql_data})

@login_required
def getStockpileRkef(request):
    materialFilter = request.GET.get('materialFilter')
    areaFilter     = request.GET.get('areaFilter')
    if db_vendor == 'postgresql':
        query = """
            SELECT
                t1.stockpile,
                t1.total_ore,
                t1.released,
                t1.nama_material,
                COALESCE(ROUND(t2.tonnage::numeric, 2), 0) AS total_selling,
                ROUND((t1.released - COALESCE(t2.tonnage, 0))::numeric, 2) AS balance,
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
            WHERE t1.status_dome != 'Finished' 
                    AND t1.sale_adjust='RKEF'
        """

    else:
        raise ValueError("Unsupported database vendor.")

    filters = []
    params = []

    if materialFilter:
        filters.append("t1.nama_material = %s")
        params.append(materialFilter)

    if areaFilter:
        filters.append("t1.stockpile = %s")
        params.append(areaFilter)

    if filters:
        query += " AND " + " AND ".join(filters)

    query += " ORDER BY t1.nama_material ASC, t1.stockpile ASC;"

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query)
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            sql_data = []
    # print(sql_data)  # Cetak hasil query
    
    return JsonResponse({'data': sql_data})