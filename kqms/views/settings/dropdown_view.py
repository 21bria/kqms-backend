from django.http import JsonResponse, HttpRequest
from django.db import connections
from ...models.sample_method import SampleMethod
from ...models.sample_method_details import SampleMethodDetail
from ...models.sample_type import SampleType
from ...models.materials import Material
from ...models.ore_productions import OreProductions
from ...models.source_model import *
from ...models.block_model import Block
from ...models.mine_geologies import MineGeologies
from ...models.selling_code import SellingCode
from ...models.stock_factories import StockFactories
from ...models.ore_class import OreClass
from ...models.selling_official import SellingSurveyor
from ...models.vendors import Vendors
from ...models.mine_units import mineUnitsView
from ...models.source_model import SourceMines,SourceMinesLoading,SourceMinesDumping,SourceMinesDome
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from ...utils.db_utils import get_db_vendor
from typing import Optional
 # Memanggil fungsi utility
db_vendor = get_db_vendor('kqms_db')
@csrf_exempt 
def method_dropdown(request):
    if request.method == 'GET':
        try:
            # Ambil semua data SampleMethod
            methods = SampleMethod.objects.all()
            # Buat list untuk menampung data setiap objek
            data_list = []
            # Looping data dan ambil atribut yang diinginkan
            for method in methods:
                data_list.append({
                    'id': method.id,
                    'sample_method': method.sample_method,
                })
            # Buat respons JSON dengan list data
            data = {
                'methods': data_list,
            }

            return JsonResponse(data)
        except SampleMethod.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def method_detail(request, id):
    if request.method == 'GET':
        try:
            methods = SampleMethodDetail.objects.filter(type_id=id)
            # Check if no methods were found
            if not methods.exists():
                return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
            
            data_list = [{
                'id'           : method.id,
                'sample_method': method.sample_method,
                'type_id'      : method.type_id,
                'type_sample'  : method.type_sample,
            } for method in methods]

            # Create JSON response with the list of data
            data = {
                'methods': data_list,
            }
            
            return JsonResponse(data)
        except SampleMethodDetail.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


# def method_detail(request, id):
#     if request.method == 'GET':
#         with connections['kqms_db'].cursor() as cursor:
#             cursor.execute("""
#                 SELECT sample_method, type_id, type_sample
#                 FROM method_details
#                 WHERE type_id = %s
#             """, [id])
#             rows = cursor.fetchall()

#         if not rows:
#             return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

#         # Buat list dict dari hasil query
#         data_list = [{
#             # 'id': row[0],
#             'sample_method': row[0],
#              'type_sample': row[1],
#             'type_id': row[2]
           
#         } for row in rows]

#         return JsonResponse({'methods': data_list})

#     return JsonResponse({'error': 'Invalid request method'}, status=400)

def sample_type_dropdown(request):
    if request.method == 'GET':
        try:
            # Ambil semua data SampleMethod
            types = SampleType.objects.all()
            # Buat list untuk menampung data setiap objek
            data_list = []
            # Looping data dan ambil atribut yang diinginkan
            for type in types:
                data_list.append({
                    'id': type.id,
                    'type_sample': type.type_sample,
                })
            # Buat respons JSON dengan list data
            data = {
                'type': data_list,
            }

            return JsonResponse(data)
        except SampleMethod.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

# For Sample Entry
def sampleTypeId(request):
    if request.method == 'GET':
        try:
            # Ambil semua data SampleMethod
            types = SampleType.objects.exclude(type_sample__in=['HOS', 'ROS','HOS_SPC','ROS_SPC','ROS_CKS','ROS_SPC','ROS_PSI','HOS_CKS','HOS_SPC'])
            # Buat list untuk menampung data setiap objek
            data_list = []
            # Looping data dan ambil atribut yang diinginkan
            for type in types:
                data_list.append({
                    'id': type.id,
                    'type_sample': type.type_sample,
                })
            # Buat respons JSON dengan list data
            data = {
                'type': data_list,
            }

            return JsonResponse(data)
        except SampleMethod.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

#For Selling samples
def sampleTypeSaleId(request):
    if request.method == 'GET':
        try:
            # Ambil semua data SampleMethod
            types = SampleType.objects.filter(type_sample__in=['HOS', 'ROS','HOS_SPC','ROS_SPC','ROS_CKS','ROS_SPC','ROS_PSI','HOS_CKS','HOS_SPC'])
            # Buat list untuk menampung data setiap objek
            data_list = []
            # Looping data dan ambil atribut yang diinginkan
            for type in types:
                data_list.append({
                    'id': type.id,
                    'type_sample': type.type_sample,
                })
            # Buat respons JSON dengan list data
            data = {
                'type': data_list,
            }

            return JsonResponse(data)
        except SampleMethod.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def material_sale(request):
    if request.method == 'GET':
        try:
            # Ambil semua data 
            dataGet = Material.objects.filter(nama_material__in=['LIM', 'SAP','PULP'])
            # Buat list untuk menampung data setiap objek
            data_list = []
            # Looping data dan ambil atribut yang diinginkan
            for row in dataGet:
                data_list.append({
                    'id'            : row.id,
                    'nama_material' : row.nama_material,
                })
            # Buat respons JSON dengan list data
            data = {
                'list': data_list,
            }
            
            return JsonResponse(data)
        except Material.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def sampleAreaId(request):
    if request.method == 'GET':
        try:
            stockpile = SourceMinesDumping.objects.all().values('id', 'dumping_point')
            # Buat respons JSON dengan list data
            data = {
                'area': list(stockpile),
            }
            return JsonResponse(data)
        except SourceMinesDumping.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def samplePointId(request):
    if request.method == 'GET':
        try:
            dome = SourceMinesDome.objects.all().values('id', 'pile_id')
            # Buat respons JSON dengan list data
            data = {
                'point': list(dome),
            }
            return JsonResponse(data)
        except SourceMinesDome.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def sampleMaterialId(request):
    if request.method == 'GET':
        try:
            material = Material.objects.all().values('id', 'nama_material')
            # Buat respons JSON dengan list data
            data = {
                'list': list(material),
            }
            return JsonResponse(data)
        except Material.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def codeProductId(request):
    if request.method == 'GET':
        try:
            get_data = SellingCode.objects.all().values('id', 'product_code')
            # Buat respons JSON dengan list data
            data = {
                'list': list(get_data),
            }
            return JsonResponse(data)
        except SellingCode.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def stockFactoryId(request):
    if request.method == 'GET':
        try:
            get_data = StockFactories.objects.all().values('id', 'factory_stock')
            # Buat respons JSON dengan list data
            data = {
                'list': list(get_data),
            }
            return JsonResponse(data)
        except StockFactories.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def material_dropdown(request):
    if request.method == 'GET':
        try:
            # Contoh list nilai
            material_list = ['LIM', 'SAP']
            # Query materials dengan menggunakan filter
            materials = Material.objects.filter(nama_material__in=material_list).values('id', 'nama_material')
            # Buat respons JSON dengan list data
            data = {
                'materials': list(materials),
            }
            return JsonResponse(data)
        except Material.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=400)


def get_details_point(request):
    if request.method == 'GET':
        try:
            # Buat SQL raw query dengan LEFT JOIN
            sql_query = """
                SELECT DISTINCT  ore_productions.id_pile, sampling_points.sampling_point
                FROM ore_productions
                LEFT JOIN sampling_points ON ore_productions.id_pile = sampling_points.id
                ORDER BY sampling_points.sampling_point ASC
            """

             # Eksekusi query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query)
                result = cursor.fetchall()

            # Ubah hasil query menjadi list of dictionaries
            data_list = [{'id_pile': row[0], 'sampling_point': row[1]} for row in result]

            # Buat respons JSON dengan list data
            response_data = {
                'details_point': data_list,
            }

            return JsonResponse(response_data)
        except OreProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_details_sources(request):
    if request.method == 'GET':
        try:
            # Buat SQL raw query dengan LEFT JOIN
            sql_query = """
                SELECT DISTINCT  
                        t1.id_prospect_area,
                        TRIM(t2.loading_point) loading_point
                FROM ore_productions as t1
                LEFT JOIN mine_sources_point_loading as t2 ON t1.id_prospect_area = t2.id
                ORDER BY TRIM(t2.loading_point) ASC
            """

             # Eksekusi query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query)
                result = cursor.fetchall()

            # Ubah hasil query menjadi list of dictionaries
            data_list = [{'id_prospect_area': row[0], 'loading_point': row[1]} for row in result]

            # Buat respons JSON dengan list data
            response_data = {
                'details_source': data_list,
            }

            return JsonResponse(response_data)
        except OreProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_details_truck(request):
    if request.method == 'GET':
        try:
            # Buat SQL raw query dengan LEFT JOIN
            sql_query = """
                SELECT DISTINCT trim(unit_truck) as unit_truck
                FROM ore_productions
                ORDER BY unit_truck ASC
            """

             # Eksekusi query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query)
                result = cursor.fetchall()

            # Ubah hasil query menjadi list of dictionaries
            data_list = [{'unit_truck': row[0]} for row in result]

            # Buat respons JSON dengan list data
            response_data = {
                'list': data_list,
            }

            return JsonResponse(response_data)
        except OreProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

# Get Year (Table)
def get_year_ore(request):
    if request.method == 'GET':
        try:
            # Buat SQL raw query dengan LEFT JOIN
            if db_vendor == 'postgresql':
                sql_query = """
                        SELECT DISTINCT DATE_PART('year', tgl_production) AS tahun
                        FROM ore_productions
                        ORDER BY tahun ASC;
                    """
            elif db_vendor in ['mssql', 'microsoft','mysql']:
                    # Query untuk SQL Server
                sql_query = """
                        SELECT DISTINCT YEAR(tgl_production) AS tahun
                        FROM ore_productions
                        GROUP BY YEAR(tgl_production)
                        ORDER BY YEAR(tgl_production) ASC
                    """
            else:
                raise ValueError("Unsupported database vendor.")

             # Eksekusi query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query)
                result = cursor.fetchall()

            # Ubah hasil query menjadi list of dictionaries
            data_list = [{'tahun': row[0]} for row in result]

            # Buat respons JSON dengan list data
            response_data = {
                'tahun_pds': data_list,
            }

            return JsonResponse(response_data)
        except OreProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_year_sale(request):
    if request.method== 'GET':
        try:
            # Buat SQL raw query
            sql_query = """
                SELECT DISTINCT tahun
                FROM details_selling
                ORDER BY tahun ASC
            """

             # Eksekusi query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query)
                result = cursor.fetchall()

            # Ubah hasil query menjadi list of dictionaries
            data_list = [{'tahun': row[0]} for row in result]

            # Buat respons JSON dengan list data
            response_data = {
                'tahun': data_list,
            }

            return JsonResponse(response_data)
        except OreProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_year_sample(request):
    if request.method == 'GET':
        try:
            # Buat SQL raw query 
            if db_vendor == 'postgresql':
                sql_query = """
                        SELECT DISTINCT DATE_PART('year', tgl_sample) AS tahun
                        FROM samples_productions
                        ORDER BY tahun ASC;
                    """
            elif db_vendor in ['mssql', 'microsoft','mysql']:
                    # Query untuk SQL Server
                sql_query = """
                        SELECT DISTINCT YEAR(tgl_sample) AS tahun
                        FROM samples_productions
                        ORDER BY YEAR(tgl_sample) ASC
                    """
            else:
                raise ValueError("Unsupported database vendor.")

             # Eksekusi query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query)
                result = cursor.fetchall()

            # Ubah hasil query menjadi list of dictionaries
            data_list = [{'tahun': row[0]} for row in result]

            # Buat respons JSON dengan list data
            response_data = {
                'tahun_sample': data_list,
            }

            return JsonResponse(response_data)
        except OreProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

# For Insert & Edit Ore
def dropdownBlockId(request):
    if request.method == 'GET':
        try:
            blocks = Block.objects.all().values('id', 'mine_block')
            # Buat respons JSON dengan list data
            data = {
                'blocks': list(blocks),
            }
            return JsonResponse(data)
        except Block.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def dropdownMaterialId(request):
    if request.method == 'GET':
        try:
            dataGet = Material.objects.filter(nama_material__in=['LIM', 'SAP'])
            # Buat list untuk menampung data setiap objek
            data_list = []
            # Looping data dan ambil atribut yang diinginkan
            for row in dataGet:
                data_list.append({
                    'id'            : row.id,
                    'nama_material' : row.nama_material,
                })
            # Buat respons JSON dengan list data
            data = {
                'list': data_list,
            }
            return JsonResponse(data)
        except Material.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def dropdownStockpileId(request):
    if request.method == 'GET':
        try:
            stockpile = SourceMinesDumping.objects.all().values('id', 'dumping_point')
            # Buat respons JSON dengan list data
            data = {
                'stockpile': list(stockpile),
            }
            return JsonResponse(data)
        except SourceMinesDumping.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def dropdownDomeId(request):
    if request.method == 'GET':
        try:
            dome = SourceMinesDome.objects.all().values('id', 'pile_id')
            # Buat respons JSON dengan list data
            data = {
                'dome': list(dome),
            }
            return JsonResponse(data)
        except SourceMinesDome.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def dropdownMineGoes(request):
    if request.method == 'GET':
        try:
            geos = MineGeologies.objects.all().values('mg_code', 'mg_code')
            # Buat respons JSON dengan list data
            data = {
                'list_data': list(geos),
            }
            return JsonResponse(data)
        except MineGeologies.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def dropdownOreClass(request,id):
    if request.method == 'GET':
        try:
            # Ambil semua data 
            dataGet = OreClass.objects.filter(material=id)
            # Buat list untuk menampung data setiap objek
            data_list = []
            # Looping data dan ambil atribut yang diinginkan
            for row in dataGet:
                data_list.append({
                    'id'        : row.id,
                    'ore_class' : row.ore_class,
                })
            # Buat respons JSON dengan list data
            data = {
                'list': data_list,
            }
            
            return JsonResponse(data)
        except OreClass.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def dropdownOreClassGet(request):
    if request.method == 'GET':
        try:
            # Ambil semua data 
            dataGet = OreClass.objects.all()
            # Buat list untuk menampung data setiap objek
            data_list = []
            # Looping data dan ambil atribut yang diinginkan
            for row in dataGet:
                data_list.append({
                    'id'        : row.id,
                    'ore_class' : row.ore_class,
                })
            # Buat respons JSON dengan list data
            data = {
                'list': data_list,
            }
            
            return JsonResponse(data)
        except OreClass.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

# For Sale Details (Stockpile,Dome, Discharge, Product Code)
def get_sale_stockpile(request):
    if request.method == 'GET':
        try:
            # Buat SQL raw query dengan LEFT JOIN
            sql_query = """
                SELECT DISTINCT  ore_sellings.id_stockpile, sampling_areas.sampling_area
                FROM ore_sellings
                LEFT JOIN sampling_areas ON ore_sellings.id_stockpile = sampling_areas.id
                ORDER BY sampling_areas.sampling_area ASC
            """

             # Eksekusi query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query)
                result = cursor.fetchall()

            # Ubah hasil query menjadi list of dictionaries
            data_list = [{'id_stockpile': row[0], 'sampling_area': row[1]} for row in result]

            # Buat respons JSON dengan list data
            response_data = {
                'details_area': data_list,
            }

            return JsonResponse(response_data)
        except OreProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_sale_dome(request):
    if request.method == 'GET':
        try:
            # Buat SQL raw query dengan LEFT JOIN
            sql_query = """
                SELECT DISTINCT  ore_sellings.id_pile, sampling_points.sampling_point
                FROM ore_sellings
                LEFT JOIN sampling_points ON ore_sellings.id_pile = sampling_points.id
                ORDER BY sampling_points.sampling_point ASC
            """

             # Eksekusi query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query)
                result = cursor.fetchall()

            # Ubah hasil query menjadi list of dictionaries
            data_list = [{'id_pile': row[0], 'sampling_point': row[1]} for row in result]

            # Buat respons JSON dengan list data
            response_data = {
                'details_point': data_list,
            }

            return JsonResponse(response_data)
        except OreProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_sale_discharge(request):
    if request.method == 'GET':
        try:
            # Buat SQL raw query dengan LEFT JOIN
            sql_query = """
                SELECT DISTINCT ore_sellings.id_factory, stock_factories.factory_stock
                FROM ore_sellings
                LEFT JOIN stock_factories ON ore_sellings.id_factory = stock_factories.id
                ORDER BY stock_factories.factory_stock ASC;
            """

             # Eksekusi query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query)
                result = cursor.fetchall()

            # Ubah hasil query menjadi list of dictionaries
            data_list = [{'id_factory': row[0], 'factory_stock': row[1]} for row in result]

            # Buat respons JSON dengan list data
            response_data = {
                'details_discharge': data_list,
            }

            return JsonResponse(response_data)
        except OreProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_sale_product(request):
    if request.method == 'GET':
        try:
            # Buat SQL raw query dengan LEFT JOIN
            sql_query = """
                SELECT DISTINCT delivery_order
                FROM ore_sellings
                ORDER BY delivery_order ASC;
            """

             # Eksekusi query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query)
                result = cursor.fetchall()

            # Ubah hasil query menjadi list of dictionaries
            data_list = [{'delivery_order': row[0]} for row in result]

            # Buat respons JSON dengan list data
            response_data = {
                'details_product': data_list,
            }

            return JsonResponse(response_data)
        except OreProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

# For Sample Detail Data (samping Point, Area, Discharge, Product)
def get_discharge(request):
    if request.method == 'GET':
        try:
            # Buat SQL raw query dengan LEFT JOIN
            sql_query = """
                SELECT *
                FROM stock_factories
                ORDER BY factory_stock ASC;
            """

             # Eksekusi query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query)
                result = cursor.fetchall()

            # Ubah hasil query menjadi list of dictionaries
            data_list = [{'id': row[0], 'factory_stock': row[1]} for row in result]

            # Buat respons JSON dengan list data
            response_data = {
                'details_discharge': data_list,
            }

            return JsonResponse(response_data)
        except OreProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_product_code(request):
    if request.method == 'GET':
        try:
            # Buat SQL raw query dengan LEFT JOIN
            sql_query = """
              SELECT 
                    DISTINCT samples_productions.product_code, ore_selling_code_product.product_code
              FROM 
                    samples_productions
            LEFT JOIN 
                   ore_selling_code_product ON samples_productions.product_code = ore_selling_code_product.id  
            ORDER BY 
                    ore_selling_code_product.product_code DESC;
            """

             # Eksekusi query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query)
                result = cursor.fetchall()

            # Ubah hasil query menjadi list of dictionaries
            data_list = [{'product_code': row[1]} for row in result]

            # Buat respons JSON dengan list data
            response_data = {
                'details_product': data_list,
            }

            return JsonResponse(response_data)
        except OreProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_sample_material(request):
    if request.method == 'GET':
        try:
            # Buat SQL raw query dengan LEFT JOIN
            sql_query = """
                SELECT *
                FROM materials
                ORDER BY nama_material ASC;
            """

             # Eksekusi query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query)
                result = cursor.fetchall()

            # Ubah hasil query menjadi list of dictionaries
            data_list = [{'id': row[0], 'nama_material': row[1]} for row in result]

            # Buat respons JSON dengan list data
            response_data = {
                'details_materials': data_list,
            }

            return JsonResponse(response_data)
        except OreProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def saleSurveyor(request):
    if request.method == 'GET':
        try:
            get_data = SellingSurveyor.objects.all().values('id', 'code_surveyor')
            # Buat respons JSON dengan list data
            data = {
                'list': list(get_data),
            }
            return JsonResponse(data)
        except SellingSurveyor.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_sample_crm(request):
    if request.method == 'GET':
        try:
            sql_query = """
                SELECT DISTINCT oreas_name as oreas_name
                FROM oreas_diff_abs_roa
                ORDER BY oreas_name ASC;
            """

             # Eksekusi query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query)
                result = cursor.fetchall()

            # Ubah hasil query menjadi list of dictionaries
            data_list = [{'oreas_name': row[0]} for row in result]

            # Buat respons JSON dengan list data
            response_data = {
                'data_crm': data_list,
            }

            return JsonResponse(response_data)
        except OreProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


# Dinamis by filter
def get_dome_pds_active(request):
    tgl_pertama  = request.GET.get('startDate')
    tgl_terakhir = request.GET.get('endDate')

    if request.method == 'GET':
        try:
            sql_query = """
                SELECT 
                    DISTINCT pile_id as dome
                FROM 
                    ore_production
                 WHERE 
                    tgl_production BETWEEN %s AND %s
                ORDER BY pile_id ASC;
            """
            params = [tgl_pertama, tgl_terakhir]
             # Eksekusi query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query,params)
                result = cursor.fetchall()
           
            list=[]
            # Ubah hasil query menjadi list of dictionaries
            list = [{'dome': row[0]} for row in result]

            # Buat respons JSON dengan list data
            response_data = {
                'list': list,
            }

            return JsonResponse(response_data)
        except OreProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

# For Load list Task to Import to Excel 
def get_task_import(request):
    if request.method == 'GET':
        try:
            # Ambil nama grup user (bukan ID lagi)
            user_group_names = list(request.user.groups.values_list('name', flat=True))

            if request.user.is_staff or request.user.groups.filter(name='superadmin').exists():
                sql_query = """
                    SELECT t.id, t.type_table
                    FROM task_table_list t
                    WHERE t.status = 1
                    ORDER BY t.type_table ASC;
                """
                params = []
            elif user_group_names:
                sql_query = """
                 SELECT t.id, t.type_table
                    FROM task_table_list t
                    WHERE t.status = 1
                    AND EXISTS (
                        SELECT 1 FROM jsonb_array_elements_text(t.allowed_group_names) AS g
                        WHERE g = ANY(%s)
                    )
                ORDER BY t.type_table ASC;

                """
                # params = [tuple(user_group_names)]  # ini penting!
                params = [user_group_names]
            else:
                return JsonResponse({'list': []})

            print(user_group_names)
            print(sql_query)

            # Eksekusi
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query, params)
                result = cursor.fetchall()

            data_list = [{'id': row[0], 'type_table': row[1]} for row in result]
            return JsonResponse({'list': data_list})


        except Exception as e:
            return JsonResponse({'error': f'Error: {str(e)}'}, status=500)


# For Mine units Categories
def get_units_categories(request):
    if request.method == 'GET':
        try:
            sql_query = """
                SELECT *
                FROM units_categories
                ORDER BY category ASC;
            """
            # Eksekusi query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query)
                result = cursor.fetchall()

            # Ubah hasil query menjadi list of dictionaries
            data_list = [{'id': row[0], 'category': row[1]} for row in result]

            # Buat respons JSON dengan list data
            response_data = {
                'list': data_list,
            }

            return JsonResponse(response_data)
        except OreProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_units_vendors(request):
    if request.method == 'GET':
        try:
            sql_query = """
                SELECT *
                FROM vendors
                ORDER BY vendor_name ASC;
            """
            # Eksekusi query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query)
                result = cursor.fetchall()

            # Ubah hasil query menjadi list of dictionaries
            data_list = [{'id': row[0], 'vendor_name': row[1]} for row in result]

            # Buat respons JSON dengan list data
            response_data = {
                'list': data_list,
            }

            return JsonResponse(response_data)
        except OreProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

#For Merge Data
def get_merge_dome(request):
    if request.method == 'GET':
        try:
            sql_query = """
                SELECT
                    DISTINCT mine_sources_point_dome.pile_id AS sampling_point,
                    mine_sources_point_dome.id,
                    ore_productions.id_pile
                FROM ore_productions
                LEFT JOIN mine_sources_point_dome ON ore_productions.id_pile = mine_sources_point_dome.id
                ORDER BY pile_id
            """
            # Eksekusi query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query)
                result = cursor.fetchall()

            # Ubah hasil query menjadi list of dictionaries
            data_list = [{'sampling_point': row[0], 'id': row[1]} for row in result]

            # Buat respons JSON dengan list data
            response_data = {
                'list': data_list,
            }

            return JsonResponse(response_data)
        except OreProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_merge_stockpile(request):
    if request.method == 'GET':
        try:
            sql_query = """
               SELECT DISTINCT 
                    mine_sources_point_dumping.dumping_point AS sampling_area,
                    mine_sources_point_dumping.id
                FROM ore_productions
                LEFT JOIN mine_sources_point_dumping 
                    ON ore_productions.id_stockpile = mine_sources_point_dumping.id
                WHERE mine_sources_point_dumping.dumping_point IS NOT NULL
                ORDER BY dumping_point

            """
            # Eksekusi query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query)
                result = cursor.fetchall()

            # Ubah hasil query menjadi list of dictionaries
            data_list = [{'sampling_area': row[0], 'id': row[1]} for row in result]

            # Buat respons JSON dengan list data
            response_data = {
                'list': data_list,
            }

            return JsonResponse(response_data)
        except OreProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


# For Entry List Table Form *{pagination}
def get_mine_vendors(request):
    if request.method == 'GET':
        try:
            get_data = Vendors.objects.all().values('vendor_name', 'code')
            # Buat respons JSON dengan list data
            data = {
                'list': list(get_data),
            }
            return JsonResponse(data)
        except Vendors.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_mine_materials(request):
    if request.method == 'GET':
        try:
            sql_query = """
                SELECT
                    DISTINCT id_material as id_material,nama_material 
               FROM 
                    productions_mines_quick
            LEFT JOIN 
                   materials ON productions_mines_quick.id_material = materials.id  
            ORDER BY 
                    materials.nama_material ASC;
            """
            # Eksekusi query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query)
                result = cursor.fetchall()

            # Ubah hasil query menjadi list of dictionaries
            data_list = [{'id_material': row[0],'nama_material': row[1]} for row in result]

            # Buat respons JSON dengan list data
            response_data = {
                'list': data_list,
            }

            return JsonResponse(response_data)
        except OreProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_mine_units(request):
    try:
        search_term = request.GET.get('q', '')
        category    = request.GET.get('category')
        page        = int(request.GET.get('page', 1))
        per_page    = 10  # Jumlah item per halaman

        # Query dasar
        options = mineUnitsView.objects.all()

        # Filter berdasarkan kategori jika ada
        if category:
            options = options.filter(category=category)

        # Filter berdasarkan pencarian jika ada
        if search_term:
            options = options.filter(unit_code__icontains=search_term)

        # Paginasi
        start   = (page - 1) * per_page
        end     = start + per_page
        results = options[start:end]

        # Format data untuk Select2
        data = {
            'results': [{'id': option.unit_code, 'text': option.unit_code} for option in results],
            'pagination': {'more': options.count() > end}
        }

        return JsonResponse(data)

    except Exception as e:
        # Log the error jika perlu
        print(f"Error occurred: {e}")
        
        # Return response dengan status error
        return JsonResponse({'error': 'An error occurred while fetching data.'}, status=500)

def get_mine_sources(request):
    try:
        query    = request.GET.get('q', '')
        page     = int(request.GET.get('page', 1))
        per_page = 10  # Jumlah item per halaman

        # Filter berdasarkan query,
        data_get = SourceMines.objects.filter(sources_area__icontains=query).order_by('sources_area')
        # Pagination
        start   = (page - 1) * per_page
        end     = start + per_page
        results = data_get[start:end]

        data = {
            'results'   : [{'id' : data_get.id, 'text': data_get.sources_area} for data_get in results],
            'pagination': {'more': len(data_get) > end}  
        }
        
        return JsonResponse(data)
    
    except Exception as e:
        print(f"Error occurred: {e}") 
        # Return an error response
        return JsonResponse({'error': 'An error occurred while fetching data.'}, status=500)

def get_mine_loading_points(request):
    try:
        query    = request.GET.get('q', '')
        page     = int(request.GET.get('page', 1))
        per_page = 10  # Jumlah item per halaman

        # Filter berdasarkan query,
        data_get = SourceMinesLoading.objects.filter(loading_point__icontains=query).order_by('loading_point')
        # Pagination
        start   = (page - 1) * per_page
        end     = start + per_page
        results = data_get[start:end]

        data = {
            'results'   : [{'id' : data_get.id, 'text': data_get.loading_point} for data_get in results],
            'pagination': {'more': len(data_get) > end}  
        }
        return JsonResponse(data)
    
    except Exception as e:
        print(f"Error occurred: {e}") 
        # Return an error response
        return JsonResponse({'error': 'An error occurred while fetching data.'}, status=500)

def get_mine_dumping_points(request):
    try:
        query    = request.GET.get('q', '')
        page     = int(request.GET.get('page', 1))
        per_page = 10  # Jumlah item per halaman

        # Filter berdasarkan query
        data_get = SourceMinesDumping.objects.filter(dumping_point__icontains=query).order_by('dumping_point')
        # Pagination
        start   = (page - 1) * per_page
        end     = start + per_page
        results = data_get[start:end]
        data = {
            'results'   : [{'id': data_get.id, 'text': data_get.dumping_point} for data_get in results],
            'pagination': {'more': len(data_get) > end}  
        }
        return JsonResponse(data, safe=False)
    
    except Exception as e:
        # Log the error if necessary (optional)
        print(f"Error occurred: {e}") 
        # Return an error response
        return JsonResponse({'error': 'An error occurred while fetching data.'}, status=500)
    
def get_mine_dome(request):
    try:    
        query    = request.GET.get('q', '')
        page     = int(request.GET.get('page', 1))
        per_page = 10  # Jumlah item per halaman

        # Filter berdasarkan query
        data_get = SourceMinesDome.objects.filter(pile_id__icontains=query).order_by('pile_id')
        # Pagination
        start   = (page - 1) * per_page
        end     = start + per_page
        results = data_get[start:end]
        data = {
            'results'   : [{'id': data_get.id, 'text': data_get.pile_id} for data_get in results],
            'pagination': {'more': len(data_get) > end}  
        }
        return JsonResponse(data, safe=False)
    
    except Exception as e:
        # Log the error if necessary (optional)
        print(f"Error occurred: {e}") 
        # Return an error response
        return JsonResponse({'error': 'An error occurred while fetching data.'}, status=500)
    
def get_materials(request):
    try:
        query    = request.GET.get('q', '')
        page     = int(request.GET.get('page', 1))
        per_page = 10  # Jumlah item per halaman

        # Filter berdasarkan query
        data_get = Material.objects.filter(nama_material__icontains=query).order_by('nama_material')
        # Pagination
        start   = (page - 1) * per_page
        end     = start + per_page
        results = data_get[start:end]
        data = {
            'results'   : [{'id': data_get.id, 'text': data_get.nama_material} for data_get in results],
            'pagination': {'more': len(data_get) > end}  
        }
        return JsonResponse(data, safe=False)
    
    except Exception as e:
        # Log the error if necessary (optional)
        print(f"Error occurred: {e}") 
        # Return an error response
        return JsonResponse({'error': 'An error occurred while fetching data.'}, status=500)

def get_category_mine(request):
    try:
        search_term = request.GET.get('q', '')

        # Menyiapkan query SQL untuk mengambil kategori
        sql_query = """
            SELECT category FROM mine_category ORDER BY category
        """
        # Eksekusi query dan ambil hasil
        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(sql_query)
            results = cursor.fetchall()

        # Memformat hasil untuk Select2
        # Jika ada istilah pencarian
        if search_term:
            filtered_results = [row for row in results if search_term.lower() in row[0].lower()]
            # options = filtered_results[:10]  # Batasi hasil ke 10
            options = filtered_results
        else:
            # options = results[:10]  # Ambil 10 data pertama jika tidak ada pencarian
            options = results
        
        # Format data untuk Select2
        data = [{'id': option[0], 'text': option[0]} for option in options]
        
        return JsonResponse(data, safe=False)
    
    except Exception as e:
        # Return an error response
        return JsonResponse({'error': 'An error occurred while fetching materials.'}, status=500)

def get_mineMaterials(request):
    if request.method == 'GET':
        try:
            included = ['Top Soil','OB','LGLO','MGLO','HGLO','MWS',
                        'LGSO','MGSO','HGSO','Quarry','Ballast','Biomass','Mud','Waste']
            # Ambil data dari model Material dan urutkan berdasarkan 'nama_material'
            # data_get = Material.objects.filter(nama_material__in=included).order_by('nama_material')
            data_get = Material.objects.filter(nama_material__in=included)
            
            # Ubah queryset menjadi list of dictionaries dengan format id dan text untuk Select2
            data = [{'id': item.id, 'text': item.nama_material} for item in data_get]

            return JsonResponse({'results': data})  # Menggunakan key 'results' sesuai dengan format Select2
        except Material.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_sample_type(request):
    try:
        search_term = request.GET.get('q', '')
        excluded_samples = ['HOS', 'ROS', 'HOS_SPC', 'ROS_SPC', 'ROS_CKS', 'ROS_PSI', 'HOS_CKS', 'HOS_SPC']
        
        if search_term:
            # Filter berdasarkan type_sample dengan pencarian dan exclude tipe sampel tertentu
            options = SampleType.objects.filter(type_sample__icontains=search_term).exclude(type_sample__in=excluded_samples)[:10]
        else:
            # Ambil 10 data pertama dan exclude tipe sampel tertentu jika tidak ada pencarian
            options = SampleType.objects.exclude(type_sample__in=excluded_samples)[:10]
        
        # Format data untuk response
        data = [{'id': option.id, 'text': option.type_sample} for option in options]
        
        return JsonResponse(data, safe=False)
    
    except Exception as e:
        # Log the error if necessary (optional)
        print(f"Error occurred: {e}")
        # Return an error response
        return JsonResponse({'error': 'An error occurred while fetching sample types.'}, status=500)
 
def get_sampleTypeSale(request):
    try:
        search_term = request.GET.get('q', '')
        included_samples = ['HOS', 'ROS', 'HOS_SPC', 'ROS_SPC', 'ROS_CKS', 'ROS_PSI', 'HOS_CKS', 'HOS_SPC']
        
        if search_term:
            # Filter berdasarkan type_sample dengan pencarian dan hanya include tipe sampel tertentu
            options = SampleType.objects.filter(type_sample__icontains=search_term, type_sample__in=included_samples)[:10]
        else:
            # Ambil 10 data pertama yang termasuk dalam tipe sampel tertentu jika tidak ada pencarian
            options = SampleType.objects.filter(type_sample__in=included_samples)[:10]
        
        # Format data untuk response
        data = [{'id': option.id, 'text': option.type_sample} for option in options]
        
        return JsonResponse(data, safe=False)
    
    except Exception as e:
        # Log the error if necessary (optional)
        print(f"Error occurred: {e}")
        # Return an error response
        return JsonResponse({'error': 'An error occurred while fetching sample types.'}, status=500)
    
def get_stockFactories(request):
    try:
        query    = request.GET.get('q', '')
        page     = int(request.GET.get('page', 1))
        per_page = 10  # Jumlah item per halaman

        # Filter berdasarkan query
        data_get = StockFactories.objects.filter(factory_stock__icontains=query).order_by('factory_stock')
        # Pagination
        start   = (page - 1) * per_page
        end     = start + per_page
        results = data_get[start:end]
        data = {
            'results'   : [{'id': data_get.id, 'text': data_get.factory_stock} for data_get in results],
            'pagination': {'more': len(data_get) > end}  
        }
        return JsonResponse(data, safe=False)
    
    except Exception as e:
        # Log the error if necessary (optional)
        print(f"Error occurred: {e}")
        # Return an error response
        return JsonResponse({'error': 'An error occurred while fetching sample types.'}, status=500)
    
def get_codeProduct(request):
    try:
        query    = request.GET.get('q', '')
        page     = int(request.GET.get('page', 1))
        per_page = 10  # Jumlah item per halaman

        # Filter berdasarkan query
        data_get = SellingCode.objects.filter(product_code__icontains=query).order_by('product_code')
        # Pagination
        start   = (page - 1) * per_page
        end     = start + per_page
        results = data_get[start:end]
        data = {
            'results'   : [{'id': data_get.id, 'text': data_get.product_code} for data_get in results],
            'pagination': {'more': len(data_get) > end}  
        }
        return JsonResponse(data, safe=False)
    
    except Exception as e:
        # Log the error if necessary (optional)
        print(f"Error occurred: {e}")
        # Return an error response
        return JsonResponse({'error': 'An error occurred while fetching sample types.'}, status=500)
    
def get_mine_geos(request):
    try:
        query    = request.GET.get('q', '')
        page     = int(request.GET.get('page', 1))
        per_page = 10  # Jumlah item per halaman

        # Filter berdasarkan query
        data_get = MineGeologies.objects.filter(mg_code__icontains=query).order_by('mg_code')
        # Pagination
        start   = (page - 1) * per_page
        end     = start + per_page
        results = data_get[start:end]
        data = {
            'results'   : [{'id': data_get.mg_code, 'text': data_get.mg_code} for data_get in results],
            'pagination': {'more': len(data_get) > end}  
        }
        return JsonResponse(data)
    
    except Exception as e:
        print(f"Error occurred: {e}")
        return JsonResponse({'error': 'An error occurred while fetching sample types.'}, status=500)
    
def get_blockMine(request):
    query = request.GET.get('q', '')
    page = int(request.GET.get('page', 1))
    per_page = 10  # Jumlah item per halaman

    # Filter berdasarkan query
    block = Block.objects.filter(mine_block__icontains=query).order_by('mine_block')
    # Pagination
    start = (page - 1) * per_page
    end = start + per_page
    results = block[start:end]

    data = {
        'results': [{'id': block.id, 'text': block.mine_block} for block in results],
        'pagination': {'more': len(block) > end}  
    }
    return JsonResponse(data)

# Not Pagination
def get_mine_category(request):
    if request.method == 'GET':
        try:
            sql_query = """
                SELECT TRIM(category) category FROM mine_category ORDER BY category
            """
            # Eksekusi query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(sql_query)
                result = cursor.fetchall()

            # Ubah hasil query menjadi list of dictionaries dengan format id dan text untuk Select2
            data = [{'id': row[0], 'text': row[0]} for row in result]

            return JsonResponse({'results': data})  # Menggunakan key 'results' sesuai dengan format Select2
        except OreProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_sources_mine(request):
    if request.method == 'GET':
        try:
            data_get =  SourceMines.objects.all().order_by('sources_area')
            data = [{'id': item.id, 'text': item.sources_area} for item in data_get]
            return JsonResponse({'results': data})  
        
        except OreProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

# For Truck Factors Mine
def getMaterialsFactors(request):
    if request.method == 'GET':
        try:
            # Ambil semua data SampleMethod
            types = Material.objects.filter(keterangan__in=['Mine', 'All_mine'])
            # Buat list untuk menampung data setiap objek
            data_list = []
            # Looping data dan ambil atribut yang diinginkan
            for type in types:
                data_list.append({
                    'id': type.id,
                    'nama_material': type.nama_material,
                })
            # Buat respons JSON dengan list data
            data = {
                'list': data_list,
            }

            return JsonResponse(data)
        except SampleMethod.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)