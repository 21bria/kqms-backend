from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.shortcuts import render
from django.views.generic import View
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from ....models.dome_setup import domeStatusFinish
from ....models.dome_setup_view import domeStatusFinishView
from ....models.ore_productions import OreProductions
from ....models.selling_barging import SellingBarging
from ....models.source_model import SourceMinesDome
from ....utils.utils import clean_string


class domeFinishList(View):
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
            'sampling_point',
            'sampling_area',
            'tonnage_dome',
            'status_dome',
            'description'
        ]

        if order_column >= len(columns):
            order_by = 'created_at'
        else:
            order_by = columns[order_column]

        if order_dir == 'desc':
            order_by = '-' + order_by

        data = domeStatusFinishView.objects.all()

        if search:
            data = data.filter(
                Q(sampling_point__icontains=search) |
                Q(sampling_area__icontains=search)
            )

        records_total = domeStatusFinishView.objects.all().count()
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
                "id": item.id,
                "sampling_point": item.sampling_point,
                "sampling_area" : item.sampling_area,
                "tonnage_dome"  : item.tonnage_dome,
                "status_dome"   : item.status_dome,
                "description"   : item.description,
                "created_at"    : item.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            } for item in object_list
        ]

        return {
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': result,
        }
    
@login_required
def insert_dome_finish(request):
    allowed_groups = ['superadmin', 'data-control', 'admin-mgoqa']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'},
            status=403
        )

    if request.method != 'POST':
        return JsonResponse({'error': 'Metode HTTP tidak diizinkan'}, status=405)

    try:
        # === Aturan validasi ===
        rules = {
            'id_dome'       : ['required'],
            'tonnage_dome'  : ['required'],
            # 'description' : ['required'],  # kalau mau opsional → hapus 'required'
        }

        custom_messages = {
            'id_dome.required'      : 'Dome is required.',
            'tonnage_dome.required' : 'Tonnage is required.',
            # 'description.required': 'Description is required.',
        }

        # === Proses validasi ===
        for field, field_rules in rules.items():
            for rule in field_rules:
                if rule == 'required' and not request.POST.get(field):
                    return JsonResponse(
                        {'error': custom_messages.get(f'{field}.required', f'{field} is required.')},
                        status=400
                    )

        # === Ambil data ===
        id_dome      = request.POST.get('id_dome')
        tonnage_dome = request.POST.get('tonnage_dome')
        description  = request.POST.get('description')

        cek_data = f"{id_dome}_FINISHED".upper()

        with transaction.atomic():
            # Update jika sudah ada, buat baru jika belum
            obj, created = domeStatusFinish.objects.update_or_create(
                cek_duplicated=cek_data,
                defaults={
                    'id_dome'       : int(id_dome),
                    'tonnage_dome'  : float(tonnage_dome),
                    'status_dome'   : 'Finished',
                    'description'   : description,
                }
            )

            # Update relasi lain tetap disamakan
            OreProductions.objects.filter(id_pile=int(id_dome)).update(status_dome="Finished", pile_status="Close")
            SourceMinesDome.objects.filter(pile_id=str(id_dome)).update(dome_finish="Finished", status_dome="Close")
            SellingBarging.objects.filter(id_pile=int(id_dome)).update(sale_dome="Finished")

            msg = 'Data baru disimpan dengan status Finished.' if created else 'Data sudah ada, diperbarui ke status Finished.'
            return JsonResponse({'success': True, 'message': msg})

    except IntegrityError as e:
        return JsonResponse({'error': 'Kesalahan integritas database', 'message': str(e)}, status=400)
    except ValidationError as e:
        return JsonResponse({'error': 'Validasi gagal', 'message': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Terjadi kesalahan', 'message': str(e)}, status=500)

@login_required
def delete_dome_finish(request):
    allowed_groups = ['superadmin','data-control','admin-mgoqa']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
        )

    if request.method == 'DELETE':
        job_id = request.GET.get('id')

        if not job_id:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})

        try:
            # Ambil data domeStatusFinish untuk mendapatkan id_pile / id_dome
            dome = domeStatusFinish.objects.get(id=int(job_id))
            id_dome = dome.id_dome  # pastikan fieldnya benar di model kamu

            # Update status kembali ke Continue
            status_dome = 'Continue'

            OreProductions.objects.filter(id_pile=id_dome).update(status_dome=status_dome)
            SellingBarging.objects.filter(id_pile=id_dome).update(sale_dome=status_dome)
            SourceMinesDome.objects.filter(id=id_dome).update(dome_finish=status_dome)

            # Hapus data domeStatusFinish
            dome.delete()

            return JsonResponse({'status': 'deleted', 'message': 'Status dikembalikan ke Continue'})

        except domeStatusFinish.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Data not found'}, status=404)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
