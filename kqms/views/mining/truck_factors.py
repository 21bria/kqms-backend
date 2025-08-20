from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ...models.mine_addition_factor import mineAdditionFactor
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from ...utils.utils import clean_string
from django.views.decorators.http import require_http_methods


@login_required
def truck_factors_page(request):
    return render(request, 'admin-mine/master/list-truck-factors.html')

class dataTruckFactors(View):
    def post(self, request):
        data_list = self._datatables(request)
        return JsonResponse(data_list, safe=False)

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

        # get Data
        data = mineAdditionFactor.objects.all()

        if search:
            data = data.filter(
                Q(type_unit__icontains=search) |
                Q(material__icontains=search)
            )
       

        # Filter berdasarkan parameter dari request
  
        # Atur sorting
        if order_dir == 'desc':
            order_by = f'-{data.model._meta.fields[order_column].name}'
        else:
            order_by = f'{data.model._meta.fields[order_column].name}'

        data = data.order_by(order_by)

        # Menghitung jumlah total sebelum filter
        records_total = data.count()

        # Menerapkan pagination
        paginator   = Paginator(data, length)
        total_pages = paginator.num_pages

        # Menghitung jumlah total setelah filter
        total_records_filtered = paginator.count

        # Atur paginator
        try:
            object_list = paginator.page(start // length + 1).object_list
        except PageNotAnInteger:
            object_list = paginator.page(1).object_list
        except EmptyPage:
            object_list = paginator.page(paginator.num_pages).object_list

        data = [
            {
                "id"             : item.id,
                "type_unit"      : item.type_unit,
                "material"       : item.material,
                "bucket_capacity": item.bucket_capacity,
                "density_lcm"    : item.density_lcm,
                "remarks"        : item.remarks
            } for item in object_list
        ]

        return {
            'draw'           : draw,
            'recordsTotal'   : records_total,
            'recordsFiltered': total_records_filtered,
            'data'           : data,
            'start'          : start,
            'length'         : length,
            'totalPages'     : total_pages,
        }

@login_required
@csrf_exempt
def create_truck_factors(request):
    allowed_groups = ['superadmin','admin-mgoqa','admin-mining','data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
        )
    if request.method == 'POST':
        try:
            # Aturan validasi
            rules = {
                'type_unit[]'       : ['required'],
                'material[]'        : ['required'],
                'bucket_capacity[]' : ['required'],
                'density_lcm[]'     : ['required'],
            }

            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'type_unit[].required'       : 'Type truck is required.',
                'material[].required'        : 'Material ore is required.',
                'bucket_capacity[].required' : 'Bcm is required.',
                'density_lcm[].required'     : 'Tonnage is required.',
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
                type_unit       = request.POST.getlist('type_unit[]')
                material        = request.POST.getlist('material[]')
                bucket_capacity = request.POST.getlist('bucket_capacity[]')
                density_lcm     = request.POST.getlist('density_lcm[]')

                # Loop untuk menyimpan setiap data sample
                for idx in range(len(type_unit)):
                    checkDup = type_unit[idx] + material[idx] 
                    if mineAdditionFactor.objects.filter(validation=checkDup).exists():
                            return JsonResponse({'message': f'{checkDup} : already exists.'}, status=422)
    
                    # Simpan data baru
                    mineAdditionFactor.objects.create(
                        type_unit       = type_unit[idx],
                        material        = material[idx],
                        bucket_capacity = bucket_capacity[idx],
                        density_lcm     = density_lcm[idx],
                        validation      = checkDup
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
def getIdTruckFactors(request):
    allowed_groups = ['superadmin','admin-mgoqa','admin-mining','data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
        )
    if request.method == 'GET':
        try:
            get_id   = request.GET.get('id')
            items     = mineAdditionFactor.objects.get(id=get_id)
            data = {
                'id'        : items.id,
                'type_unit': clean_string(items.type_unit),
                'material'  : clean_string(items.material),
                'bucket_capacity'    : items.bucket_capacity,
                'density_lcm'    : items.density_lcm,
                'remarks'   : items.remarks
        
            }
            return JsonResponse(data)
        except mineAdditionFactor.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
@require_http_methods(["POST"])
def update_truck_factors(request, id):
    allowed_groups = ['superadmin','admin-mgoqa','admin-mining','data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
        )
    try:
        # Aturan validasi
        rules = {
            'type_unit' : ['required'],
            'material'   : ['required'],
            'bucket_capacity'     : ['required'],
            'density_lcm'     : ['required'],
        }

        # Pesan kesalahan validasi yang disesuaikan
        custom_messages = {
            'type_unit.required': 'Type truck is required.',
            'material.required'  : 'Materials required.',
            'bucket_capacity.required'    : 'Bcm is required.',
            'density_lcm.required'    : 'Tonnage is required.'
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

        type_unit = request.POST.get('type_unit')
        material   = request.POST.get('material')
        bucket_capacity     = request.POST.get('bucket_capacity')
        density_lcm     = request.POST.get('density_lcm')
        remarks    = request.POST.get('remarks')


        # Validasi duplikat
        checkDup = type_unit + material 
        if mineAdditionFactor.objects.exclude(id=id).filter(validation=checkDup).exists(): 
            return JsonResponse({'message': f'{checkDup} : already exists.'}, status=422)
        
        # Dapatkan data yang akan diupdate berdasarkan ID
        data = mineAdditionFactor.objects.get(id=id)

        # Lakukan update data dengan nilai baru
        data.type_unit   = type_unit
        data.material     = material
        data.bucket_capacity       = bucket_capacity
        data.density_lcm       = density_lcm
        data.remarks      = remarks

        # Simpan perubahan ke dalam database
        data.save()

        # Kembalikan respons JSON sukses
        return JsonResponse({'success': True, 'message': 'Data berhasil diupdate.'})

    except mineAdditionFactor.DoesNotExist:
        return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    except IntegrityError as e:
        return JsonResponse({'error': 'Terjadi kesalahan integritas database', 'message': str(e)}, status=400)

    except ValidationError as e:
        return JsonResponse({'error': 'Validasi gagal', 'message': str(e)}, status=400)

    except Exception as e:
        return JsonResponse({'error': 'Terjadi kesalahan', 'message': str(e)}, status=500)

@login_required
def delete_truck_factors(request):
    allowed_groups = ['superadmin','admin-mgoqa','admin-mining','data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
        )
    if request.method == 'DELETE':
        job_id = request.GET.get('id')
        if job_id:
            data = mineAdditionFactor.objects.get(id=int(job_id))
            data.delete()
            return JsonResponse({'status': 'deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

