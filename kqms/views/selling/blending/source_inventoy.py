# views.py
import logging
from django.http import JsonResponse
from django.db import connections
from django.views.decorators.csrf import csrf_exempt
from prophet import Prophet
import pandas as pd
from django.db.models import Sum
logger = logging.getLogger(__name__) #tambahkan ini untuk multi database.
import json
from decimal import Decimal

# Get Inventory
from decimal import Decimal
import json
from django.http import JsonResponse
from django.db import connections

def get_data_source(request):
    saleFilter   = request.GET.get('saleFilter')
    areaFilter   = request.GET.get('areaFilter', '[]')
    pointFilter  = request.GET.get('pointFilter', '[]')

    # Parsing JSON aman
    try:
        areaFilter  = json.loads(areaFilter) if areaFilter else []
        pointFilter = json.loads(pointFilter) if pointFilter else []
    except json.JSONDecodeError:
        areaFilter, pointFilter = [], []

    # Pagination
    page     = int(request.GET.get('page', 1))
    per_page = 100
    offset   = (page - 1) * per_page

    # ===== Dynamic filters =====
    filters, params = [], []

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

    # ===== Count query =====
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
                     t1.nama_material, t1.Ni, t1.Co, t1.Al2O3, t1.Fe, 
                     t1.Mgo, t1.SiO2, t1.MC, t1.SM
        ) AS sub
    """

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(count_query, params)
        result = cursor.fetchone()
        total_data = result[0] if result else 0

    # ===== Main query =====
    query = f"""
        SELECT
            t1.stockpile,
            t1.pile_id,
            t1.total_ore,
            t1.released,
            t1.nama_material,
            COALESCE(ROUND(SUM(t2.tonnage)::numeric, 2), 0) AS total_selling,
            ROUND((t1.released - COALESCE(SUM(t2.tonnage), 0))::numeric, 2) AS balance,
            t1.Ni,
            t1.Co,
            t1.Al2O3,
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
        {where_clause}
        GROUP BY
            t1.stockpile, t1.pile_id, t1.total_ore, t1.released,
            t1.nama_material, t1.Ni, t1.Co, t1.Al2O3, t1.Fe, 
            t1.Mgo, t1.SiO2, t1.MC, t1.SM
        ORDER BY t1.nama_material ASC, t1.stockpile ASC
        LIMIT %s OFFSET %s;
    """

    params_with_paging = params + [per_page, offset]

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params_with_paging)
        columns = [col[0] for col in cursor.description]
        sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]

    # Konversi numeric/Decimal → float
    for item in sql_data:
        for field in [
            'total_ore', 'released', 'total_selling', 'balance',
            'ni', 'co', 'al2o3', 'fe', 'mgo', 'sio2', 'mc', 'sm'
        ]:
            val = item.get(field)
            if isinstance(val, Decimal):
                item[field] = float(val)

    # Pagination
    more_data   = len(sql_data) == per_page
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

