from django.contrib.auth.decorators import login_required
from django.db import connections
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from ....models.ore_truck_factor import OreTruckFactorAdjust
from ....models.ore_productions import OreProductions
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.shortcuts import render
from django.views.generic import View
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.db.models import F  # Import F for field references
from ....utils.db_utils import get_db_vendor
from ....utils.utils import clean_string

# Memanggil fungsi utility
db_vendor = get_db_vendor('kqms_db')

@login_required
def ore_adjustment_page(request):
    return render(request, 'master/list-ore-adjust.html')

class OreFactorsAdjustList(View):

    def post(self, request):
        data = self._datatables(request)
        return JsonResponse(data, safe=False)

    def _datatables(self, request):
        datatables = request.POST
        draw    = int(datatables.get('draw', 1))
        start   = int(datatables.get('start', 0))
        length  = int(datatables.get('length', 10))
        search  = datatables.get('search[value]', '')
        order_column = int(datatables.get('order[0][column]', 0))
        order_dir = datatables.get('order[0][dir]', 'asc')

        # Mapping kolom berdasarkan urutan kolom DataTables frontend
        columns = [
            't1.id',
            't1.unit_truck',
            't3.loading_point',
            't2.nama_material',
            't1.date_start',
            't1.date_end',
            't1.ton',
            't1.status',
            't1.reference_tf'
        ]

        order_by = columns[order_column]
        order_dir = 'ASC' if order_dir.lower() == 'asc' else 'DESC'

        base_query = """
            FROM ore_truck_factors_adjust AS t1
            LEFT JOIN materials AS t2 ON t2.id = t1.material
            LEFT JOIN mine_sources_point_loading AS t3 ON t3.id = t1.sources
        """

        where_clause = ""
        params = []

        if search:
            where_clause = """
                WHERE t1.unit_truck LIKE %s
                OR t2.nama_material LIKE %s
                OR t3.loading_point LIKE %s
            """
            params.extend(['%' + search + '%'] * 3)

        # Total data sebelum filter
        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) {base_query}")
            records_total = cursor.fetchone()[0]

            if search:
                cursor.execute(f"SELECT COUNT(*) {base_query} {where_clause}", params)
                records_filtered = cursor.fetchone()[0]
            else:
                records_filtered = records_total

        # Query data dengan filter + order + pagination
        data_query = f"""
            SELECT
                t1.id, t1.unit_truck, t3.loading_point, t2.nama_material,
                t1.date_start, t1.date_end, t1.ton, t1.status, t1.reference_tf
            {base_query}
            {where_clause}
            ORDER BY {order_by} {order_dir}
        """

        # Tambahkan LIMIT/OFFSET berdasarkan vendor
        if db_vendor == 'mysql' or db_vendor == 'postgresql':
            data_query += " LIMIT %s OFFSET %s"
            params.extend([length, start])
        elif db_vendor in ['mssql', 'microsoft']:
            data_query += " OFFSET %s ROWS FETCH NEXT %s ROWS ONLY"
            params.extend([start, length])
        else:
            raise ValueError("Unsupported database vendor.")

        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(data_query, params)
            result = cursor.fetchall()

        data_list = [
            {
                'id': row[0],
                'unit_truck': row[1],
                'prospect_area': row[2],
                'nama_material': row[3],
                'date_start': row[4],
                'date_end': row[5],
                'ton': row[6],
                'status': row[7],
                'reference_tf': row[8],
            }
            for row in result
        ]

        return {
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data_list,
        }

    
@login_required        
@csrf_exempt
def get_ore_adjustment(request, id):
    # allowed_groups = ['superadmin','data-control']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'GET':
        try:
            item = OreTruckFactorAdjust.objects.get(id=id)
            data = {
                'id'           : item.id,
                'unit_truck'   : clean_string(item.unit_truck),
                'material'     : item.material, 
                'date_start'   : item.date_start,
                'date_end'     : item.date_end,
                'ton'          : item.ton,
                'sources'      : item.sources,
                'status'       : item.status,
                'created_at'   : item.created_at
            }
            return JsonResponse(data)
        except OreTruckFactorAdjust.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def insert_ore_adjustment(request):
    allowed_groups = ['superadmin','data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )
    if request.method == 'POST':
        try:
            # Aturan validasi
            rules = {
                'sources'   : ['required'],
                'material'  : ['required'],
                'date_start': ['required'],
                'date_end'  : ['required'],
                'unit_truck': ['required'],
                'ton'       : ['required']
            }

            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'sources.required'   : 'Sources is required.',
                'material.required'  : 'Material is required.',
                'date_start.required': 'Date Start is required.',
                'date_end.required'  : 'Date End is required.',
                'unit_truck.required': 'Truck is required.',
                'ton.required'       : 'Tonnage is required.'
            }

            # Validasi request
            for field, field_rules in rules.items():
                for rule in field_rules:
                    if rule == 'required':
                        if not request.POST.get(field):
                            return JsonResponse({'error': custom_messages[f'{field}.required']}, status=400)

            # Dapatkan data dari request dengan default nilai
            sources     = request.POST.get('sources')
            material    = request.POST.get('material')
            date_start  = request.POST.get('date_start')
            date_end    = request.POST.get('date_end')
            unit_truck  = request.POST.get('unit_truck')
            ton         = request.POST.get('ton')

            # Pastikan semua nilai yang diperlukan ada sebelum diubah
            if any(v is None for v in [sources, material, date_start, date_end, unit_truck, ton]):
                return JsonResponse({'error': 'Semua field harus diisi.'}, status=400)

            # Gunakan transaksi database untuk memastikan integritas data
            with transaction.atomic():
                reference_tf = f"{unit_truck}{material}{sources}{date_start}{date_end}"

                if OreTruckFactorAdjust.objects.filter(reference_tf=reference_tf).exists():
                    return JsonResponse({'message': f'{reference_tf} : already exists.'}, status=422)

                # Simpan data baru
                OreTruckFactorAdjust.objects.create(
                    sources=int(sources),
                    material=int(material),
                    date_start=date_start,
                    date_end=date_end,
                    unit_truck=unit_truck,
                    ton=float(ton),
                    reference_tf=reference_tf,
                    status='adjustment'
                    # id_user=request.user.id  # Sesuaikan dengan cara Anda mendapatkan user ID
                )

                # Update OreProduction
                OreProductions.objects.filter(
                    tgl_production__gte=date_start,
                    tgl_production__lte=date_end,
                    id_prospect_area=sources,
                    id_material=material,
                    unit_truck=unit_truck
                ).update(
                    tonnage=F('ritase') * float(ton),
                    remarks='tonnage adjustment'
                )

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
def update_ore_adjustment(request, id):
    # allowed_groups = ['superadmin','data-control']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'POST':
        try:
            # Validasi menggunakan Django Forms atau manual
            required_fields = {
                'sources': 'Sources is required.',
                'material': 'Material is required.',
                'date_start': 'Date Start is required.',
                'date_end': 'Date End is required.',
                'unit_truck': 'Truck is required.',
                'ton': 'Tonnage is required.'
            }

            # Validasi request
            for field, message in required_fields.items():
                if not request.POST.get(field):
                    return JsonResponse({'error': message}, status=400)

            # Ambil data dari request
            sources = int(request.POST['sources'])
            material = request.POST['material']
            date_start = request.POST['date_start']
            date_end = request.POST['date_end']
            unit_truck = request.POST['unit_truck']
            ton = float(request.POST['ton'])

            # Dapatkan objek yang akan diupdate
            data = get_object_or_404(OreTruckFactorAdjust, id=id)

            # Update data
            data.ton = ton
            data.status = 'restore'
            data.save()

            # Update OreProductions
            OreProductions.objects.filter(
                tgl_production__gte=date_start,
                tgl_production__lte=date_end,
                id_prospect_area=sources,
                id_material=material,
                unit_truck=unit_truck
            ).update(
                tonnage=F('ritase') * ton,
                remarks='tonnage restore'
            )

            return JsonResponse({'success': True, 'message': 'Data berhasil diupdate.'})

        except IntegrityError as e:
            return JsonResponse({'error': 'Terjadi kesalahan integritas database', 'message': str(e)}, status=400)
        except ValidationError as e:
            return JsonResponse({'error': 'Validasi gagal', 'message': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'Terjadi kesalahan', 'message': str(e)}, status=500)

    return JsonResponse({'error': 'Metode tidak diizinkan'}, status=405)

@login_required
def delete_ore_adjustment(request):
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
            data = OreTruckFactorAdjust.objects.get(id=int(job_id))
            data.delete()
            return JsonResponse({'status': 'deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
