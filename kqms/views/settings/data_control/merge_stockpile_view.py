from django.contrib.auth.decorators import login_required
from django.db import connections
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from ....models.merge_stock import stockpileMerge
from ....models.merge_stock_view import stockpileMergeView
from ....models.ore_productions import OreProductions
from ....models.source_model import SourceMinesDumping
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.shortcuts import render
from django.views.generic import View
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from ....utils.utils import clean_string
from ....utils.utils import generate_stockpile_merger
from ....utils.db_utils import get_db_vendor


 # Memanggil fungsi utility
db_vendor = get_db_vendor('kqms_db')

@login_required
def stockpile_merge_page(request):
    stockpile_merger = generate_stockpile_merger()
    context = {
        'stockpile_merger': stockpile_merger,
    }
    return render(request, 'master/list-merge-stockpile.html',context)

class stockpileMergeList(View):

    def post(self, request):
        # Ambil semua data yang valid
        stockpile = self._datatables(request)
        return JsonResponse(stockpile, safe=False)

    def _datatables(self, request):
        datatables = request.POST
        # Ambil draw
        draw = int(datatables.get('draw'))
        # Ambil start
        start = int(datatables.get('start'))
        # Ambil length (limit)
        length = int(datatables.get('length'))
        # Ambil data search
        search = datatables.get('search[value]')
        # Ambil order column
        order_column = int(datatables.get('order[0][column]'))
        # Ambil order direction
        order_dir = datatables.get('order[0][dir]')

        # Set record total
        records_total = stockpileMergeView.objects.all().count()
        # Set records filtered
        records_filtered = records_total
        # Ambil semua yang valid
        data = stockpileMergeView.objects.all()

        if search:
            data = data.filter(
                Q(stockpile__icontains=search) |
                Q(stockpile_new__icontains=search) 
            )
            
            records_total = data.count()
            records_filtered = records_total

        # Atur sorting
        if order_dir == 'desc':
            order_by = f'-{data.model._meta.fields[order_column].name}'
        else:
            order_by = f'{data.model._meta.fields[order_column].name}'

        data = data.order_by(order_by)

        # Atur paginator
        paginator = Paginator(data, length)

        try:
            object_list = paginator.page(start // length + 1).object_list
        except PageNotAnInteger:
            object_list = paginator.page(1).object_list
        except EmptyPage:
            object_list = paginator.page(paginator.num_pages).object_list

        data = [
            {
                "id"             :item.id,
                "stockpile"      :item.stockpile,
                "tonnage_primary":item.tonnage_primary,
                "stockpile_new"  :item.stockpile_new,
                "tonnage_second" :item.tonnage_second,
                "sum_tonnage"    :item.sum_tonnage,
                "status"         :item.status,
                "ref_id"         :item.ref_id
            } for item in object_list
        ]

        return {
            'draw'           : draw,
            'recordsTotal'   : records_total,
            'recordsFiltered': records_filtered,
            'data'           : data,
        }
       
@login_required        
@csrf_exempt
def get_stockpile_merge(request, id):
    # allowed_groups = ['superadmin','data-control']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'GET':
        try:
            item = stockpileMergeView.objects.get(id=id)
            data = {
                'id':item.id,
                'stockpile'       :clean_string(item.stockpile), 
                'stockpile_ori'   :item.stockpile_ori, 
                'tonnage_primary' :item.tonnage_primary,
                'stockpile_new'   :clean_string(item.stockpile_new),
                'stockpile_second':item.stockpile_second,
                'tonnage_second'  :item.tonnage_second,
                'sum_tonnage'     :item.sum_tonnage,
                'ref_id'          :clean_string(item.ref_id),
                'status'          :clean_string(item.status),
                'remarks'         :clean_string(item.remarks)
            }
            return JsonResponse(data)
        except stockpileMergeView.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def insert_stockpile_merge(request):
    # allowed_groups = ['superadmin','data-control']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'POST':
        try:
            # Aturan validasi
            rules = {
                'stockpile_ori'    : ['required'],
                'stockpile_second' : ['required']
            }

            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'stockpile_ori.required'    : 'Stockpile is required.',
                'stockpile_second.required' : 'Stockpile New is required.',
            }

            # Validasi request
            for field, field_rules in rules.items():
                for rule in field_rules:
                    if rule == 'required':
                        if not request.POST.get(field):
                            return JsonResponse({'error': custom_messages[f'{field}.required']}, status=400)

            # Dapatkan data dari request dengan default nilai
            stockpile_ori    = request.POST.get('stockpile_ori')
            tonnage_primary  = request.POST.get('tonnage_primary')
            stockpile_second = request.POST.get('stockpile_second')
            tonnage_second   = request.POST.get('tonnage_second')
            ref_id           = request.POST.get('ref_id')
            remarks          = request.POST.get('remarks')

            # Pastikan semua nilai yang diperlukan ada sebelum diubah
            if any(v is None for v in [ stockpile_ori, tonnage_primary, stockpile_second, tonnage_second]):
                return JsonResponse({'error': 'Semua field harus diisi.'}, status=400)

            # Gunakan transaksi database untuk memastikan integritas data
            with transaction.atomic():

                # Simpan data baru
                stockpileMerge.objects.create(
                    stockpile_ori=int(stockpile_ori),
                    tonnage_primary=float(tonnage_primary),
                    stockpile_second=int(stockpile_second),
                    tonnage_second=float(tonnage_second),
                    status='Merger',
                    ref_id=ref_id,
                    remarks=remarks
                    # id_user=request.user.id  # Sesuaikan dengan cara Anda mendapatkan user ID
                )

                # Update OreProduction
                OreProductions.objects.filter(
                    id_stockpile=stockpile_ori
                ).update(
                    id_stockpile=stockpile_second,
                    stockpile_ori=stockpile_ori,
                    stock_compositing=ref_id
                )

                # Update SourceMinesDumping
                SourceMinesDumping.objects.filter(id=stockpile_ori).update(compositing='Yes')

            # Kembalikan respons JSON sukses
            return JsonResponse({'success': True, 'message': 'Data berhasil disimpan.'})

        except IntegrityError as e:
            return JsonResponse({'error': 'Terjadi kesalahan integritas database', 'message': str(e)}, status=400)

        except ValidationError as e:
            return JsonResponse({'error': 'Validasi gagal', 'message': str(e)}, status=400)

        except Exception as e:
            return JsonResponse({'error': 'Terjadi kesalahan', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Metode HTTP tidak diizinkan'}, status=405)
    
@login_required
def update_stockpile_merge(request, id):
    # allowed_groups = ['superadmin','data-control']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'POST':
        try:
            rules = {
                'stockpile_second': ['required'],
                'stockpile_ori'   : ['required']
            }
            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'stockpile_second.required' : 'Stockpile New is required.',
                'stockpile_ori.required'    : 'Stockpile is required.'
            }

            # Validasi request
            for field, field_rules in rules.items():
                for rule in field_rules:
                    if rule == 'required':
                        if not request.POST.get(field):
                            return JsonResponse({'error': custom_messages[f'{field}.required']}, status=400)

            # Ambil data dari request
            stockpile_second = int(request.POST['stockpile_second'])
            ref_id           = request.POST['ref_id']
            stockpile_ori    = int(request.POST['stockpile_ori'])
            remarks          = request.POST['remarks']

            if stockpileMerge.objects.filter(ref_id=ref_id,status='Restore').exists():
                return JsonResponse({'error': f'Data {ref_id} already exists.'}, status=400)

            # Dapatkan objek yang akan diupdate
            data = get_object_or_404(stockpileMerge, id=id)

            # Update data
            data.remarks = remarks
            data.status = 'Restore'
            data.save()

            # Update OreProductions
            OreProductions.objects.filter(
                    id_stockpile=stockpile_second,
                    stock_compositing=ref_id
                ).update(
                    id_stockpile=stockpile_ori
                )
            
            # Update SourceMinesDumping
            SourceMinesDumping.objects.filter(id=stockpile_ori).update(compositing='No')

            return JsonResponse({'success': True, 'message': 'Data berhasil diupdate.'})

        except IntegrityError as e:
            return JsonResponse({'error': 'Terjadi kesalahan integritas database', 'message': str(e)}, status=400)
        except ValidationError as e:
            return JsonResponse({'error': 'Validasi gagal', 'message': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'Terjadi kesalahan', 'message': str(e)}, status=500)

    return JsonResponse({'error': 'Metode tidak diizinkan'}, status=405)

@login_required
def delete_stockpile_merge(request):
    # allowed_groups = ['superadmin','data-control']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'DELETE':
        job_id = request.GET.get('id')
        if job_id:
            # Lakukan penghapusan berdasarkan ID di sini
            data = stockpileMerge.objects.get(id=int(job_id))
            data.delete()
            return JsonResponse({'status': 'deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    
@login_required
def get_oreStockpile(request, id):
    if request.method == 'GET':
        try:
            # Create SQL raw query 
            if db_vendor == 'postgresql':
                query = """
                        SELECT 
                            t1.id_stockpile,
                            ROUND(SUM(t1.tonnage)::numeric, 0) AS tonnage
                        FROM 
                            ore_productions as t1
                        LEFT JOIN 
                            mine_sources_point_dumping AS t2 ON t2.id=t1.id_stockpile
                        WHERE 
                            t1.id_stockpile = %s
                        GROUP BY 
                    t1.id_stockpile
                    """
            elif db_vendor in ['mssql', 'microsoft','mysql']:
                    # Query untuk SQL Server
                query = """
                        SELECT 
                            t1.id_stockpile,
                            ROUND(SUM(t1.tonnage), 0) AS tonnage
                        FROM 
                            ore_productions as t1
                        LEFT JOIN 
                            mine_sources_point_dumping AS t2 ON t2.id=t1.id_stockpile
                        WHERE 
                            t1.id_stockpile = %s
                        GROUP BY 
                            t1.id_stockpile
                    """
            else:
                raise ValueError("Unsupported database vendor.")

            # Execute query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(query, [id])
                result = cursor.fetchall()  # Use fetchall to get all results

            # Convert query results into list of dictionaries
            data_list = [
                {
                    'id_stockpile': row[0], 
                    'tonnage': row[1]
                } for row in result
            ]

            # Create JSON response with list data
            response_data = {
                'list': data_list,
            }

            return JsonResponse(response_data)
        except OreProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

