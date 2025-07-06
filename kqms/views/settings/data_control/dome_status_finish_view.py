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
from ....models.selling_data import SellingProductions
from ....models.source_model import SourceMinesDome
from ....utils.utils import clean_string


@login_required
def dome_finish_page(request):
    return render(request, 'master/list-finish-dome.html')

class domeFinishList(View):
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
        records_total = domeStatusFinishView.objects.all().count()
        # Set records filtered
        records_filtered = records_total
        # Ambil semua yang valid
        data = domeStatusFinishView.objects.all()

        if search:
            data = domeStatusFinishView.objects.filter(
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
                "sampling_point": item.sampling_point,
                "sampling_area": item.sampling_area,
                "tonnage_dome": item.tonnage_dome,
                "status_dome": item.status_dome,
                "description": item.description
            } for item in object_list
        ]

        return {
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        }

@csrf_exempt
def get_dome_finish(request, id):
    # allowed_groups = ['superadmin','data-control']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'GET':
        try:
            item = domeStatusFinishView.objects.get(id=id)
            data = {
                'id':item.id,
                'id_dome':item.id_dome,
                'sampling_point' :clean_string(item.sampling_point),
                'sampling_area'  :clean_string(item.sampling_area),
                'tonnage_dome'   :item.tonnage_dome, 
                'status_dome'    :item.status_dome, 
                'description'    :clean_string(item.description)
            }
            return JsonResponse(data)
        except domeStatusFinishView.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def insert_dome_finish(request):
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
                'id_dome': ['required']
            }

            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'id_dome.required': 'Dome is required.'
            }

            # Validasi request
            for field, field_rules in rules.items():
                for rule in field_rules:
                    if rule == 'required':
                        if not request.POST.get(field):
                            return JsonResponse({'error': custom_messages[f'{field}.required']}, status=400)

            # Dapatkan data dari request dengan default nilai
            id_dome      = request.POST.get('id_dome')
            tonnage_dome = request.POST.get('tonnage_dome')
            description  = request.POST.get('description')

            status_dome='Finished'

            # Pastikan semua nilai yang diperlukan ada sebelum diubah
            if any(v is None for v in [id_dome, tonnage_dome, description]):
                return JsonResponse({'error': 'Semua field harus diisi.'}, status=400)

            # Gunakan transaksi database untuk memastikan integritas data
            with transaction.atomic():
                cek_data = f"{id_dome}{status_dome}"

                if domeStatusFinish.objects.filter(cek_duplicated=cek_data).exists():
                    return JsonResponse({'error': f'Data already exists.'}, status=400)

                # Simpan data baru
                domeStatusFinish.objects.create(
                    id_dome=int(id_dome),
                    tonnage_dome=float(tonnage_dome),
                    status_dome=status_dome,
                    description=description,
                    cek_duplicated=cek_data,
                )

                # Update OreProduction
                OreProductions.objects.filter(id_pile=id_dome).update(status_dome=status_dome)

                # Update Selling Data
                SellingProductions.objects.filter(id=id_dome).update(sale_dome=status_dome)

                # Update SourceMinesDome
                SourceMinesDome.objects.filter(id=id_dome).update(dome_finish=status_dome)

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
def update_dome_finish(request, id):
    # allowed_groups = ['superadmin','data-control']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'POST':
        try:
            rules = {
                'id_dome': ['required'],
            }
            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'id_dome.required':'Dome is required.'
            }

            # Validasi request
            for field, field_rules in rules.items():
                for rule in field_rules:
                    if rule == 'required':
                        if not request.POST.get(field):
                            return JsonResponse({'error': custom_messages[f'{field}.required']}, status=400)
            # Ambil data dari request
            id_dome      = int(request.POST['id_dome'])
            description  = request.POST['description']

            status_dome  ='Continue'

            # Dapatkan objek yang akan diupdate
            data = get_object_or_404(domeStatusFinish, id=id)

            # Update data
            data.description = description
            data.status_dome = status_dome
            data.save()

            # Update OreProductions
            OreProductions.objects.filter(
                    id_pile=id_dome
                ).update(
                    status_dome=status_dome
                )

            # Update Selling Data
            SellingProductions.objects.filter(id=id_dome).update(sale_dome=status_dome)

            # Update SourceMinesDome
            SourceMinesDome.objects.filter(id=id_dome).update(dome_finish=status_dome)
            return JsonResponse({'success': True, 'message': 'Data berhasil diupdate.'})

        except IntegrityError as e:
            return JsonResponse({'error': 'Terjadi kesalahan integritas database', 'message': str(e)}, status=400)
        except ValidationError as e:
            return JsonResponse({'error': 'Validasi gagal', 'message': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'Terjadi kesalahan', 'message': str(e)}, status=500)

    return JsonResponse({'error': 'Metode tidak diizinkan'}, status=405)

@login_required
def delete_dome_finish(request):
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
            data = domeStatusFinish.objects.get(id=int(job_id))
            data.delete()
            return JsonResponse({'status': 'deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

