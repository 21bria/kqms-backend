from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.db import connections
import json 
from ....utils.db_utils import get_db_vendor

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
    # Ambil filter dari request
    areaFilter  = request.GET.get('areaFilter', '[]')  # Menggunakan '[]' sebagai default jika None
    pointFilter = request.GET.get('pointFilter', '[]')  # Menggunakan '[]' sebagai default jika None

    # Parsing JSON
    areaFilter  = json.loads(areaFilter)  # Parsing JSON menjadi list
    pointFilter = json.loads(pointFilter)  # Parsing JSON menjadi lis

    # Pagination setup
    page = int(request.GET.get('page', 1))
    per_page = 50
    offset = (page - 1) * per_page

    # Query to count total data
    count_query = """
        SELECT COUNT(*)
        FROM inventory_by_dome AS t1
        LEFT JOIN selling_by_dome AS t2 ON 
            t2.sampling_area = t1.stockpile AND
            t2.sampling_point = t1.pile_id
        WHERE t1.status_dome = 'Finished'
    """

    # Apply filters to the count query
    count_filters = []
    params = []

    if saleFilter:
        count_filters.append("t1.sale_adjust = %s")
        params.append(saleFilter)

    # Memeriksa dan menambahkan filter untuk stockpile
    if areaFilter: 
        count_filters.append(f"t1.stockpile IN ({', '.join(['%s'] * len(areaFilter))})")
        params.extend(areaFilter)

    # Memeriksa dan menambahkan filter untuk pile_id
    if pointFilter:  
        count_filters.append(f"t1.pile_id IN ({', '.join(['%s'] * len(pointFilter))})")
        params.extend(pointFilter)


    if count_filters:
        count_query += " AND " + " AND ".join(count_filters)

    # Execute count query
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(count_query,params)
        result = cursor.fetchone()
        total_data = result[0] if result else 0 


    # Main data query with pagination
    if db_vendor == 'postgresql':
        query = """
            SELECT
                t1.stockpile,
                t1.pile_id,
                t1.total_ore,
                t1.released,
                t1.nama_material,
                COALESCE(ROUND(t2.tonnage::numeric, 2), 0) AS total_selling,
                COALESCE(ROUND((t1.total_ore - t2.tonnage)::numeric, 2), 0) AS balance,
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
                ON t2.sampling_area = t1.stockpile 
                AND t2.sampling_point = t1.pile_id
            WHERE t1.status_dome != 'Finished'
        """
    else:
        raise ValueError("Unsupported database vendor.")
    
    if count_filters:
        query += " AND " + " AND ".join(count_filters)

    # Add pagination and order by clauses
    query += " ORDER BY t1.nama_material ASC, t1.stockpile ASC"
    
    # Query untuk mengambil data 
    if db_vendor == 'postgresql':
        query += f" LIMIT {per_page} OFFSET {offset};"
       
    elif db_vendor in ['mssql', 'microsoft']:
        # Adding pagination (OFFSET-FETCH) SQL SERVER
        query += f" OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY;"
    else:
        raise ValueError("Unsupported database vendor.")

    # Fetch paginated data
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query,params)
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            sql_data = []


    # Calculate if there is more data
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
    areaFilter  = request.GET.get('areaFilter', '[]')  # Menggunakan '[]' sebagai default jika None
    # Parsing JSON
    areaFilter  = json.loads(areaFilter)  # Parsing JSON menjadi list

    # Pagination setup
    page = int(request.GET.get('page', 1))
    per_page = 50
    offset = (page - 1) * per_page

    # Query to count total data
    count_query = """
        SELECT COUNT(*)
        FROM inventory_by_dome AS t1
        LEFT JOIN selling_by_dome AS t2 ON 
            t2.sampling_area = t1.stockpile AND
            t2.sampling_point = t1.pile_id
        WHERE t1.status_dome = 'Finished'
    """

    # Apply filters to the count query
    count_filters = []
    params = []

    if saleFilter:
        count_filters.append("t1.sale_adjust = %s")
        params.append(saleFilter)

    if areaFilter:  # Pastikan areaFilter tidak kosong
        count_filters.append(f"t1.stockpile IN ({', '.join(['%s'] * len(areaFilter))})")
        params.extend(areaFilter)

    if count_filters:
        count_query += " AND " + " AND ".join(count_filters)

    # Execute count query
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(count_query,params)
        result = cursor.fetchone()
        total_data = result[0] if result else 0 
   

    if db_vendor == 'postgresql':
            query = """
                SELECT
                    t1.stockpile,
                    SUM(t1.total_ore) AS total_ore,
                    SUM(t1.released) AS released,
                    t1.nama_material,
                    COALESCE(ROUND(SUM(t2.tonnage)::numeric, 2), 0) AS total_selling,
                    COALESCE(ROUND((SUM(t1.total_ore) - SUM(t2.tonnage))::numeric, 2), 0) AS balance,
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
                    ON t2.sampling_area = t1.stockpile 
                    AND t2.sampling_point = t1.pile_id
                WHERE t1.status_dome='Finished'
            """
    else:
        raise ValueError("Unsupported database vendor.")
    
    if count_filters:
            query += " AND " + " AND ".join(count_filters)

    query += """
            GROUP BY 
                t1.stockpile, 
                t1.nama_material, 
                t2.sale_adjust, 
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
        """

    # Add ordering and pagination (if needed)
    query += """
            ORDER BY t1.nama_material ASC, t1.stockpile ASC
        """ 
    # Query untuk mengambil data dengan pagination
    if db_vendor == 'postgresql':
        query += f" LIMIT {per_page} OFFSET {offset};"
       
    elif db_vendor in ['mssql', 'microsoft']:
        # Adding pagination (OFFSET-FETCH) SQL SERVER
        query += f" OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY;"
    else:
        raise ValueError("Unsupported database vendor.")

    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(query, params)
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            sql_data = []

    # print(sql_data)  # Cetak hasil query
    
    # Calculate if there is more data
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