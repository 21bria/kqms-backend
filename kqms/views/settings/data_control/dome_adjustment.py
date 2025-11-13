from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from decimal import Decimal, getcontext
from django.db import transaction
from django.db.models import Sum
from decimal import Decimal
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from kqms.models import OreProductions,domeAdjustment
from kqms.models.dome_adjustment_view import domeAdjustmentView
from ....utils.utils import clean_string

class domeAdjustmentList(View):
    def post(self, request):
        dataView = self._datatables(request)
        return JsonResponse(dataView, safe=False)

    def _datatables(self, request):
        datatables = request.POST
        draw = int(datatables.get('draw'))
        start = int(datatables.get('start'))
        length = int(datatables.get('length'))
        search = datatables.get('search[value]')
        order_column = int(datatables.get('order[0][column]'))
        order_dir = datatables.get('order[0][dir]')

        columns = [
            'id',
            'dome',
            'current_total',
            'tonnage_dome',
            'target_total',
            'scale_factor',
            'description',
            'created_at',
        ]

        if order_column >= len(columns):
            order_by = 'created_at'
        else:
            order_by = columns[order_column]

        if order_dir == 'desc':
            order_by = '-' + order_by

        data = domeAdjustmentView.objects.all()

        if search:
            data = data.filter(
                Q(dome__icontains=search) |
                Q(description__icontains=search)
            )

        records_total = domeAdjustmentView.objects.all().count()
        records_filtered = data.count()

        data = data.order_by(order_by)

        paginator = Paginator(data, length)
        try:
            object_list = paginator.page(start // length + 1).object_list
        except PageNotAnInteger:
            object_list = paginator.page(1).object_list
        except EmptyPage:
            object_list = paginator.page(paginator.num_pages).object_list

        result = [
            {
                "id"            : item.id,
                "dome"          : item.dome,
                "current_total" : item.current_total,
                "target_total"  : item.target_total,
                "scale_factor"  : item.scale_factor,
                "description"   : item.description,
                "created_at"    : item.created_at
            } for item in object_list
        ]

        return {
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': result,
        }

def scale_dome_tonnage(request,dome_id: str, target_total: Decimal):
    """
    Scale semua tonnage dome tertentu agar total = target_total
    tapi rasio antar tanggal dan ritase tetap sama.
    """
    getcontext().prec = 12  # presisi tinggi untuk akurasi

    qs = OreProductions.objects.filter(id_pile=dome_id)
    current_total = qs.aggregate(total=Sum('tonnage'))['total'] or Decimal('0')
    current_total = Decimal(str(current_total))  #  pastikan Decimal
    if current_total == 0:
        raise ValueError(f"Total tonnage = 0 untuk dome {dome_id}")

    scale_factor = target_total / current_total

    
    with transaction.atomic():
        objs = []
        for obj in qs:
            tonnage_decimal = Decimal(str(obj.tonnage or 0))
            obj.tonnage = (tonnage_decimal * scale_factor).quantize(Decimal('0.000001'))
            objs.append(obj)
        OreProductions.objects.bulk_update(objs, ['tonnage'])

        # Koreksi residu kecil
        new_total = qs.aggregate(total=Sum('tonnage'))['total'] or Decimal('0')
        new_total = Decimal(str(new_total))
        delta = target_total - new_total
        if abs(delta) > Decimal('0.000001'):
            largest = qs.order_by('-tonnage').first()
            largest.tonnage = (Decimal(str(largest.tonnage)) + delta).quantize(Decimal('0.000001'))
            largest.save(update_fields=['tonnage'])

        # Simpan catatan penyesuaian (insert baru)
        domeAdjustment.objects.create(
            id_dome        = dome_id,
            current_total  = float(current_total),
            target_total   = float(target_total),
            scale_factor   = float(scale_factor),
            description    = f'Scaling tonnage dome {dome_id} dari {current_total} ke {target_total}',
            cek_duplicated = f'{dome_id}-{target_total.normalize()}',
            id_user        = request.user.id if hasattr(request, 'user') else None
        )

    print(f"✅ Scaling selesai untuk dome {dome_id}")
    print(f"Total awal: {current_total}")
    print(f"Total baru: {target_total}")
    print(f"Faktor skala: {scale_factor}")

# ==== Cara pakai ====
# scale_dome_tonnage(request, dome_id='DOME123', target_total=Decimal('1500.0'))
def adjust_dome_insert(request):
    allowed_groups = ['superadmin', 'data-control', 'admin-mgoqa']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'},
            status=403
        )

    if request.method != 'POST':
        return JsonResponse({'error': 'Metode HTTP tidak diizinkan'}, status=405)
     # === Validasi input wajib ===
    rules = {
            'id_dome': ['required'],
            'target_total': ['required'],
        }

    custom_messages = {
            'id_dome.required': 'Dome harus dipilih.',
            'target_total.required': 'Target tonnage tidak boleh kosong.',
    }

    # === Proses validasi ===
    for field, field_rules in rules.items():
        for rule in field_rules:
            if rule == 'required' and not request.POST.get(field):
                return JsonResponse(
                    {'status': 'error', 'message': custom_messages.get(f'{field}.required', f'{field} wajib diisi.')},
                    status=400
                )

    dome_id = request.POST.get('id_dome')
    target_total_str = request.POST.get('target_total')

    try:
        target_total = Decimal(target_total_str)
        if target_total <= 0:
            return JsonResponse({'status': 'error', 'message': 'Target tonnage harus lebih dari 0.'}, status=400)

        # === Cek duplikasi (dome + target_total) ===
        cek_key = f"{dome_id}-{target_total.normalize()}"
        duplicate_exists = domeAdjustment.objects.filter(
            Q(cek_duplicated=cek_key)
        ).exists()

        if duplicate_exists:
            return JsonResponse({
                'status': 'warning',
                'message': f'Penyesuaian untuk Dome {dome_id} dengan target {target_total:,} sudah pernah dilakukan.'
            }, status=409)

        # === Jalankan scaling ===
        scale_dome_tonnage(request, dome_id, target_total)

        return JsonResponse({
            'status': 'success',
            'message': f'Tonnage dome {dome_id} berhasil di-adjust ke {target_total:,}.'
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
# @csrf_exempt
# def get_id_adjustment_dome(request, id):
#     allowed_groups = ['superadmin','data-control','admin-mgoqa']
#     if not request.user.groups.filter(name__in=allowed_groups).exists():
#         return JsonResponse(
#             {'status': 'error', 'message': 'You do not have permission'}, 
#             status=403
#     )
#     if request.method == 'GET':
#         try:
#             item = domeAdjustmentView.objects.get(id=id)
#             data = {
#                 'id':item.id,
#                 'dome'         :item.dome,
#                 'current_total':item.current_total,
#                 'target_total' :item.target_total,
#                 'scale_factor' :item.scale_factor,
#                 'description'  :clean_string(item.description)
#             }
#             return JsonResponse(data)
#         except domeAdjustmentView.DoesNotExist:
#             return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

#     return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def get_id_adjustment_dome(request, id):
    allowed_groups = ['superadmin', 'data-control', 'admin-mgoqa']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse({'status': 'error', 'message': 'You do not have permission'}, status=403)

    if request.method == 'GET':
        try:
            # Gunakan filter, bukan get
            item = (
                domeAdjustmentView.objects
                .filter(id=id)
                .order_by('-created_at')  # ambil data terbaru berdasarkan created_at view
                .first()  # ambil 1 data teratas
            )

            if not item:
                return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

            data = {
                'id'            : item.id_dome if hasattr(item, 'id_dome') else item.id,
                'dome'          : item.dome,
                'current_total' : item.current_total,
                'target_total'  : item.target_total,
                'scale_factor'  : item.scale_factor,
                'description'   : clean_string(item.description),
            }
            return JsonResponse(data)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def restore_dome_tonnage(request, id: int):
    """
    Restore tonnage dome ke kondisi sebelum scaling terakhir.
    """
    getcontext().prec = 12  # presisi tinggi

    # Ambil data scaling terakhir
    last_adj = (
        domeAdjustment.objects.filter(id_dome=id)
        .order_by('-created_at')  # pastikan punya field timestamp
        .first()
    )

    if not last_adj:
        return JsonResponse({'status': 'error', 'message': 'Tidak ada data scaling sebelumnya untuk dome ini.'}, status=404)

    # Ambil nilai yang diperlukan
    prev_total   = Decimal(str(last_adj.current_total))
    scaled_total = Decimal(str(last_adj.target_total))

    if scaled_total == 0:
        return JsonResponse({'status': 'error', 'message': 'Data scaling tidak valid (target_total = 0).'}, status=400)

    # Faktor kebalikan untuk restore
    restore_factor = prev_total / scaled_total

    qs = OreProductions.objects.filter(id_pile=id)
    if not qs.exists():
        return JsonResponse({'status': 'error', 'message': 'Tidak ada data produksi untuk dome ini.'}, status=404)

    with transaction.atomic():
        objs = []
        for obj in qs:
            tonnage_decimal = Decimal(str(obj.tonnage or 0))
            obj.tonnage = (tonnage_decimal * restore_factor).quantize(Decimal('0.000001'))
            objs.append(obj)
        OreProductions.objects.bulk_update(objs, ['tonnage'])

        # Koreksi residu kecil biar total pas
        new_total = qs.aggregate(total=Sum('tonnage'))['total'] or Decimal('0')
        new_total = Decimal(str(new_total))
        delta = prev_total - new_total
        if abs(delta) > Decimal('0.000001'):
            largest = qs.order_by('-tonnage').first()
            largest.tonnage = (Decimal(str(largest.tonnage)) + delta).quantize(Decimal('0.000001'))
            largest.save(update_fields=['tonnage'])

        # Simpan log restore baru
        domeAdjustment.objects.create(
            id_dome        = id,
            current_total  = float(scaled_total),
            target_total   = float(prev_total),
            scale_factor   = float(restore_factor),
            description    = f'Restore tonnage dome {id} dari {scaled_total} ke {prev_total}',
            cek_duplicated = f'{id}-restore-{prev_total.normalize()}',
            id_user        = request.user.id if hasattr(request, 'user') else None
        )

    return JsonResponse({
        'status' : 'success',
        'message': f'Dome {id} berhasil direstore ke kondisi awal ({prev_total:,}).'
    })
