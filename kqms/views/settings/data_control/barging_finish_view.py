from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import connections
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.shortcuts import render
from django.views.generic import View
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from ....models.ore_productions import OreProductions
from ....models.selling_barging import SellingBarging
from ....models.selling_barging_adjust import bargingAdjust
from ....utils.utils import clean_string
from ....utils.db_utils import get_db_vendor
from typing import Optional
 # Memanggil fungsi utility
db_vendor = get_db_vendor('kqms_db')

@login_required
def barging_finish_page(request):
    return render(request, 'admin-selling/entry/list-finish-barging.html')

class bargingFinishList(View):
    def post(self, request):
        dataView = self._datatables(request)
        return JsonResponse(dataView, safe=False)

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
        records_total = bargingAdjust.objects.all().count()
        # Set records filtered
        records_filtered = records_total
        # Ambil semua yang valid
        data = bargingAdjust.objects.all()

        if search:
            data = bargingAdjust.objects.filter(
                Q(sampling_point__icontains=search) |
                Q(sampling_area__icontains=search)
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
                "id": item.id,
                "date_arrival"    : item.date_arrival,
                "date_departure"  : item.date_departure,
                "jetty_departure" : item.jetty_departure,
                "code_lot"        : item.code_lot,
                "ritase_ori"      : item.ritase_ori,
                "tonnage_ori"     : item.tonnage_ori,
                "tonnage_adjust"  : item.tonnage_adjust,
                "status"          : item.status,
                "remarks"         : item.remarks
            } for item in object_list
        ]

        return {
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        }


@login_required
def insert_barging_finish(request):
    allowed_groups = ['superadmin', 'data-control', 'admin-mgoqa']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'},
            status=403
        )

    if request.method != 'POST':
        return JsonResponse({'error': 'Metode HTTP tidak diizinkan'}, status=405)

    try:
        rules = {
            'code_lot'        : ['required'],
            'ritase_ori'      : ['required'],
            'tonnage_ori'     : ['required'],
            'date_arrival'    : ['required'],
            'date_departure'  : ['required'],
            'jetty_departure' : ['required'],
            'tonnage_adjust'  : ['required'],
        }

        custom_messages = {
            'code_lot.required'        : 'Code Lot is required.',
            'ritase_ori.required'      : 'Ritase is required.',
            'tonnage_ori.required'     : 'Tonnage is required.',
            'date_arrival.required'    : 'Arrival is required.',
            'date_departure.required'  : 'Departure is required.',
            'jetty_departure.required' : 'Jetty is required.',
            'tonnage_adjust.required'  : 'Adjustment Tonnage is required.',
        }

        # === Validasi ===
        for field, field_rules in rules.items():
            for rule in field_rules:
                if rule == 'required' and not request.POST.get(field):
                    return JsonResponse(
                        {'error': custom_messages.get(f'{field}.required', f'{field} is required.')},
                        status=400
                    )

          # === Ambil data ===
        code_lot        = request.POST.get('code_lot')
        ritase_ori      = int(request.POST.get('ritase_ori'))
        tonnage_ori     = float(request.POST.get('tonnage_ori'))
        date_arrival    = request.POST.get('date_arrival')
        date_departure  = request.POST.get('date_departure')
        jetty_departure = request.POST.get('jetty_departure')
        tonnage_adjust  = float(request.POST.get('tonnage_adjust'))
        description     = request.POST.get('description')

        cek_data = str(code_lot)

        with transaction.atomic():
            existing = bargingAdjust.objects.filter(code_lot=cek_data).first()

            if existing:
                # Kalau sudah ada → ubah jadi Complete
                existing.status = "Complete"
                existing.save(update_fields=["status"])

                # Update SellingBarging tonase & tanggal
                SellingBarging.objects.filter(code_lot=cek_data).update(
                    tonnage=(tonnage_adjust / ritase_ori) if ritase_ori > 0 else 0,
                    date_barge_in=date_arrival,
                    date_barge_out=date_departure,
                )

                return JsonResponse({'success': True, 'message': 'Data sudah ada, status diubah menjadi Complete.'})

            else:
                # Hitung tonnage per ritase
                tonnage_per_ritase = (tonnage_adjust / ritase_ori) if ritase_ori > 0 else 0

                # Simpan ke bargingAdjust
                bargingAdjust.objects.create(
                    code_lot=code_lot,
                    ritase_ori=ritase_ori,
                    tonnage_ori=tonnage_ori,
                    date_arrival=date_arrival,
                    date_departure=date_departure,
                    jetty_departure=jetty_departure,
                    tonnage_adjust=tonnage_adjust,
                    status="Complete",
                    remarks=description,
                )

                # Update SellingBarging → tonase & tanggal
                SellingBarging.objects.filter(code_lot=cek_data).update(
                    tonnage=tonnage_per_ritase,
                    date_barge_in=date_arrival,
                    date_barge_out=date_departure,
                    status_barging="Complete"
                )

                return JsonResponse({'success': True, 'message': 'Data berhasil disimpan dengan status Complete.'})

    except IntegrityError as e:
        return JsonResponse({'error': 'Kesalahan integritas database', 'message': str(e)}, status=400)
    except ValidationError as e:
        return JsonResponse({'error': 'Validasi gagal', 'message': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Terjadi kesalahan', 'message': str(e)}, status=500)


@login_required
def delete_barging_finish(request):
    allowed_groups = ['superadmin','data-control','admin-mgoqa']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )
    if request.method == 'DELETE':
        job_id = request.GET.get('id')
        if job_id:
            # Lakukan penghapusan berdasarkan ID di sini
            data = bargingAdjust.objects.get(id=int(job_id))
            data.delete()
            return JsonResponse({'status': 'deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

   
@login_required
def get_tonnage_lot(request, code_lot):
    if request.method == 'GET':
        try:
            # Create SQL raw query 
            if db_vendor == 'postgresql':
                query = """
                        SELECT 
                            ROUND(SUM(t1.ritase_group)::numeric, 0) AS ritase,
                            ROUND(SUM(t1.tonnage)::numeric, 0) AS tonnage
                        FROM 
                            ore_sellings_barging AS t1
                        WHERE 
                            t1.code_lot = %s
                    """
            elif db_vendor in ['mssql', 'microsoft','mysql']:
                    # Query untuk SQL Server
                query = """
                       SELECT 
                            ROUND(SUM(t1.ritase_group), 0) AS ritase,
                            ROUND(SUM(t1.tonnage), 0) AS tonnage
                        FROM 
                            ore_sellings_barging as t1
                        WHERE 
                            t1.code_lot = %s
                    """
            else:
                raise ValueError("Unsupported database vendor.")

            # Execute query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(query, [code_lot])
                result = cursor.fetchall()  

            data_list = [
                {
                    'ritase'   : row[0],
                    'tonnage'  : row[1]
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


