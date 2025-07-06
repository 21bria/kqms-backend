from django.contrib.auth.decorators import login_required
from django.db import connections
from django.http import JsonResponse
from ....models.ore_truck_factor import OreTruckFactor
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.shortcuts import render
from django.views.generic import View
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from ....models.ore_truck_factor_view import OreTruckFactorView


@login_required
def ore_factors_page(request):
    return render(request, 'master/list-truck-factor.html')

class OreFactorsList(View):
    def post(self, request):
        # Ambil semua data yang valid
        OreClass = self._datatables(request)
        return JsonResponse(OreClass, safe=False)

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
        records_total = OreTruckFactorView.objects.all().count()
        # Set records filtered
        records_filtered = records_total
        # Ambil semua yang valid
        data = OreTruckFactorView.objects.all()

        if search:
            data = OreTruckFactorView.objects.filter(
                 Q(nama_material__icontains=search) |
                 Q(type_tf__icontains=search)
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
                "id":item.id,
                "type_tf":item.type_tf,
                "nama_material":item.nama_material,
                "bcm":item.bcm,
                "density":item.density,
                "ton":item.ton
            } for item in object_list
        ]

        return {
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        }

@login_required        
@csrf_exempt
def get_ore_factors(request, id):
    # allowed_groups = ['superadmin','data-control']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'GET':
        try:
            item = OreTruckFactor.objects.get(id=id)
            data = {
                'id'           : item.id,
                'type_tf'      : item.type_tf,
                'material'     : item.material, 
                'bcm'          : item.bcm,
                'density'      : item.density,
                'ton'          : item.ton,
                'reference_tf' : item.reference_tf,
                'status'       : item.status,
                'created_at'   : item.created_at
            }
            return JsonResponse(data)
        except OreTruckFactor.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def insert_ore_factors(request):
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
                'type_tf': ['required'],
                'material': ['required'],
                'ton': ['required']
            }

            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'type_tf.required' : 'Type Truck is required.',
                'material.required': 'Material is required.',
                'ton.required'     : 'Tonnage is required.'
            }

            # Validasi request
            for field, field_rules in rules.items():
                for rule in field_rules:
                    if rule == 'required':
                        if not request.POST.get(field):
                            return JsonResponse({'error': custom_messages[f'{field}.required']}, status=400)
                    elif rule.startswith('min_length'):
                        min_length = int(rule.split(':')[1])
                        if len(request.POST.get(field, '')) < min_length:
                            return JsonResponse({'error': custom_messages[f'{field}.min_length']}, status=400)
                    elif rule.startswith('max_length'):
                        max_length = int(rule.split(':')[1])
                        if len(request.POST.get(field, '')) > max_length:
                            return JsonResponse({'error': custom_messages[f'{field}.max_length']}, status=400)
                    elif rule == 'regex':
                        import re
                        pattern = re.compile(r'^[a-zA-Z0-9]*$')
                        if not pattern.match(request.POST.get(field, '')):
                            return JsonResponse({'error': custom_messages[f'{field}.regex']}, status=400)

                
            # Gunakan transaksi database untuk memastikan integritas data
            with transaction.atomic():
                # Dapatkan data dari request
                type_tf      = request.POST.get('type_tf')
                material     = request.POST.get('material')
                bcm          = request.POST.get('bcm')
                density      = request.POST.get('density')
                ton          = request.POST.get('ton')
                reference_tf = request.POST.get('reference_tf')

                if OreTruckFactor.objects.filter(reference_tf =reference_tf).exists():
                        return JsonResponse({'message': f'{reference_tf} : already exists.'}, status=422)
    
                # Simpan data baru
                OreTruckFactor.objects.create(
                    type_tf=type_tf,
                    material=int(material),
                    bcm=float(bcm),
                    density=float(density),
                    ton=float(ton),
                    reference_tf=reference_tf,
                    status=1,
                    # id_user=request.user.id  # Sesuaikan dengan cara Anda mendapatkan user ID
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
def update_ore_factors(request, id):
    # allowed_groups = ['superadmin','data-control']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'POST':
        try:
            # validasi
            rules = {
                'type_tf': ['required'],
                'material': ['required'],
                'ton': ['required']
            }

            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'type_tf.required' : 'Type Truck is required.',
                'material.required': 'Material is required.',
                'ton.required'     : 'Tonnage is required.'
            }

            # Validasi request
            for field, field_rules in rules.items():
                for rule in field_rules:
                    if rule == 'required':
                        if not request.POST.get(field):
                            return JsonResponse({'error': custom_messages[f'{field}.required']}, status=400)
                    elif rule.startswith('min_length'):
                        min_length = int(rule.split(':')[1])
                        if len(request.POST.get(field, '')) < min_length:
                            return JsonResponse({'error': custom_messages[f'{field}.min_length']}, status=400)
                    elif rule.startswith('max_length'):
                        max_length = int(rule.split(':')[1])
                        if len(request.POST.get(field, '')) > max_length:
                            return JsonResponse({'error': custom_messages[f'{field}.max_length']}, status=400)
                    elif rule == 'regex':
                        import re
                        pattern = re.compile(r'^[a-zA-Z0-9]*$')
                        if not pattern.match(request.POST.get(field, '')):
                            return JsonResponse({'error': custom_messages[f'{field}.regex']}, status=400)

            reference_tf = request.POST.get('reference_tf')
            if OreTruckFactor.objects.exclude(id=id).filter(reference_tf=reference_tf).exists():
                return JsonResponse({'error': f'Data {reference_tf} already exists.'}, status=400)

            # Dapatkan data yang akan diupdate berdasarkan ID
            data = OreTruckFactor.objects.get(id=id)

            # Lakukan update data dengan nilai baru
            data.type_tf=request.POST.get('type_tf')
            data.material=request.POST.get('material')
            data.density=request.POST.get('density')
            data.bcm=request.POST.get('bcm')
            data.ton=request.POST.get('ton')
            data.reference_tf=reference_tf
           

            # Simpan perubahan ke dalam database
            data.save()

            # Kembalikan respons JSON sukses
            return JsonResponse({'success': True, 'message': 'Data berhasil diupdate.'})

        except OreTruckFactor.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

        except IntegrityError as e:
            return JsonResponse({'error': 'Terjadi kesalahan integritas database', 'message': str(e)}, status=400)

        except ValidationError as e:
            return JsonResponse({'error': 'Validasi gagal', 'message': str(e)}, status=400)

        except Exception as e:
            return JsonResponse({'error': 'Terjadi kesalahan', 'message': str(e)}, status=500)
     
    else:
        return JsonResponse({'error': 'Metode tidak diizinkan'}, status=405)    
   
@login_required
def delete_ore_factors(request):
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
            data = OreTruckFactor.objects.get(id=int(job_id))
            data.delete()
            return JsonResponse({'status': 'deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
