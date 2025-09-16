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
from ....models.selling_dircet_transfer import SellingDirectTransferView
from ....models.selling_barging import SellingBarging
from ....models.selling_barging_adjust import bargingAdjust
from ....utils.db_utils import get_db_vendor
from django.db.models import Sum
 # Memanggil fungsi utility
db_vendor = get_db_vendor('kqms_db')

@login_required
def staging_data_page(request):
    return render(request, 'admin-selling/entry/list-direct-barging.html')

class dataStagingList(View):
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
        records_total = SellingDirectTransferView.objects.all().count()
        # Set records filtered
        records_filtered = records_total
        # Ambil semua yang valid
        data = SellingDirectTransferView.objects.all()

        if search:
            data = SellingDirectTransferView.objects.filter(
                Q(dome__icontains=search) |
                Q(barge_code__icontains=search) |
                Q(material__icontains=search) |
                Q(stockpile__icontains=search)
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
                # "id": item.id,
                "date_hauling"    : item.date_hauling,
                "direct"          : item.direct,
                "dome"            : item.dome,
                "stockpile"       : item.stockpile,
                "material"        : item.material,
                "barge_code"      : item.barge_code,
                "ritase"          : item.ritase,
                "tonnage"         : round(item.tonnage,2),
                "status_transfer" : item.status_transfer
            } for item in object_list
        ]

        return {
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        }

@login_required
def transfers_direct_production(request):
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
            'date_from': ['required'],
            'date_to': ['required']
        }
        custom_messages = {
            'date_from.required': 'Date from is required.',
            'date_to.required': 'Date to is required.',
        }

        # === Validasi ===
        for field, field_rules in rules.items():
            for rule in field_rules:
                if rule == 'required' and not request.POST.get(field):
                    return JsonResponse(
                        {'error': custom_messages.get(f'{field}.required', f'{field} is required.')},
                        status=400
                    )

        date_from = request.POST.get('date_from')
        date_to = request.POST.get('date_to')
        description = request.POST.get('description')

        # === Ambil data dengan GROUP BY pile + batch ===
        grouped = SellingBarging.objects.filter(
            date_hauling__range=[date_from, date_to],
            direct="Yes"
        ).values(
            "date_hauling", "shift", "id_material", "id_stockpile", "id_pile", "batch"
        ).annotate(
            total_ritase=Sum("ritase_group"),
            total_tonnage=Sum("tonnage")
        )

        if not grouped:
            return JsonResponse({'status': 'error', 'message': 'Tidak ada data untuk ditransfer'}, status=404)

        inserted_count = 0
        skipped_count = 0

        shift_map = {
            "Day": "D",
            "Night": "N"
        }

        with transaction.atomic():
            for g in grouped:
                shift_val = shift_map.get(g["shift"], g["shift"])  # default tetap aslinya

                exists = OreProductions.objects.filter(
                    tgl_production=g["date_hauling"],
                    shift=shift_val,
                    id_stockpile=g["id_stockpile"],
                    id_pile=g["id_pile"],
                    id_material=g["id_material"],
                    kode_batch=g["batch"],
                    direct="Yes"
                ).exists()

                if exists:
                    skipped_count += 1
                    continue

                OreProductions.objects.create(
                    tgl_production=g["date_hauling"],
                    shift=shift_val,  # gunakan D atau N
                    id_material=g["id_material"],
                    id_prospect_area=g["id_stockpile"],
                    id_stockpile=g["id_stockpile"],
                    id_pile=g["id_pile"],
                    ritase=g["total_ritase"],
                    tonnage=g["total_tonnage"],
                    increment=0,
                    kode_batch=g["batch"],
                    truck_factor='DT-30',
                    pile_status='Continue',
                    direct="Yes",
                    remarks=description,
                    status_dome='Continue',
                    id_user=request.user.id
                )
                inserted_count += 1


            return JsonResponse({
                'status': 'success',
                'message': f'{inserted_count} data berhasil ditransfer, {skipped_count} dilewati (sudah ada).'
            })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    

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
def get_tonnage_direct(request):
    date_from  = request.POST.get('date_from')
    date_to    = request.POST.get('date_to')

    if request.method == 'POST':   # sebaiknya POST kalau ambil dari form
        try:
            if db_vendor == 'postgresql':
                query = """
                        SELECT 
                            ROUND(SUM(ritase_group)::numeric, 0) AS ritase,
                            ROUND(SUM(tonnage)::numeric, 0) AS tonnage
                        FROM ore_sellings_barging
                        WHERE direct = 'Yes'
                          AND date_hauling BETWEEN %s AND %s
                        """
            else:
                raise ValueError("Unsupported database vendor.")

            # Execute query
            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(query, [date_from, date_to])
                result = cursor.fetchall()  

            data_list = [
                {
                    'ritase' : row[0],
                    'tonnage': row[1]
                } for row in result
            ]

            return JsonResponse({'list': data_list})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)
