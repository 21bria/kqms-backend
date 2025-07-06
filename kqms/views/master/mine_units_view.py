from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ...models.mine_units import MineUnits,mineUnitsView
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from ...utils.utils import clean_string


@login_required
def MineUnits_page(request):
    return render(request, 'master/list-mine-units.html')

class MineUnits_List(View):
    def post(self, request):
        # Ambil semua data invoice yang valid
        mineUnitsView = self._datatables(request)
        return JsonResponse(mineUnitsView, safe=False)

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
        records_total = mineUnitsView.objects.all().count()
        # Set records filtered
        records_filtered = records_total
        # Ambil semua yang valid
        data = mineUnitsView.objects.all()

        if search:
            data = mineUnitsView.objects.filter(
                Q(unit_code__icontains=search) |
                Q(unit_model__icontains=search) |
                Q(category__icontains=search)
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
                "unit_code": item.unit_code,
                "unit_model": item.unit_model,
                "unit_type": item.unit_type,
                "supports": item.supports,
                "status": item.status,
                "category": item.category,
                "vendor_name": item.vendor_name
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
def get_MineUnits(request, id):
    # allowed_groups = ['superadmin','admin-mgoqa','admin-mining','admin-selling','data-control']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'GET':
        try:
            job = MineUnits.objects.get(id=id)
            data = {
                'id'         : job.id,
                'unit_code'  : clean_string(job.unit_code), 
                'unit_model' : clean_string(job.unit_model),
                'unit_type'  : clean_string(job.unit_type),
                'id_category': job.id_category,
                'id_vendor'  : job.id_vendor,
                'supports'   : clean_string(job.supports),
                'status'     : clean_string(job.status),
                'description': clean_string(job.description)
            }
            return JsonResponse(data)
        except MineUnits.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def insert_MineUnits(request):
    # allowed_groups = ['superadmin','admin-mgoqa','admin-mining','admin-selling','data-control']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'POST':
        try:
            # Aturan validasi
            rules = {
                'unit_code' : ['required'],
                'unit_model': ['required'],
                'category'  : ['required'],
                'vendor'    : ['required'],
            }

            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'unit_code.required' : 'Unit Code is required.',
                'unit_model.required': 'Unit Model is required.',
                'category.required'  : 'Category is required.',
                'vendor.required'    : 'Vendor is required.',
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
                unit_code   = request.POST.get('unit_code')
                unit_model  = request.POST.get('unit_model')
                unit_type   = request.POST.get('unit_type')
                # category    = request.POST.get('category')
                # vendor      = request.POST.getlist('vendor')
                category    = request.POST.get('category')
                vendor      = request.POST.get('vendor')
                supports    = request.POST.get('supports')
                description = request.POST.get('description')


                if MineUnits.objects.filter(unit_code=unit_code).exists():
                        return JsonResponse({'message': f'{unit_code} : already exists.'}, status=422)
    
                # Simpan data baru
                MineUnits.objects.create(
                    unit_code=unit_code,
                    unit_model=unit_model,
                    unit_type=unit_type,
                    id_category=int(category),  # Pastikan ini integer
                    id_vendor=int(vendor),      # Pastikan ini intege
                    supports=supports,
                    status=1,
                    description=description,
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
def update_MineUnits(request, id):
    # allowed_groups = ['superadmin','admin-mgoqa','admin-mining','admin-selling','data-control']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'POST':
        try:
        # Aturan validasi
            rules = {
                    'unit_code' : ['required'],
                    'unit_model': ['required'],
                    'category'  : ['required'],
                    'vendor'    : ['required'],
                }

            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'unit_code.required' : 'Unit Code is required.',
                'unit_model.required': 'Unit Model is required.',
                'category.required'  : 'Category is required.',
                'vendor.required'    : 'Vendor is required.',
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

            unit_code = request.POST.get('unit_code')
            if MineUnits.objects.exclude(id=id).filter(unit_code=unit_code).exists():
                return JsonResponse({'error': f'SampleID {unit_code} already exists.'}, status=400)

            # Dapatkan data yang akan diupdate berdasarkan ID
            data = MineUnits.objects.get(id=id)

            # Lakukan update data dengan nilai baru
            data.unit_code   = unit_code
            data.unit_model  = request.POST.get('unit_model')
            data.unit_type   = request.POST.get('unit_type')
            data.id_category = request.POST.get('category')
            data.id_vendor   = request.POST.get('vendor')
            data.supports    = request.POST.get('supports')
            data.description = request.POST.get('description')

            # Simpan perubahan ke dalam database
            data.save()

            # Kembalikan respons JSON sukses
            return JsonResponse({'success': True, 'message': 'Data berhasil diupdate.'})

        except MineUnits.DoesNotExist:
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
def delete_MineUnits(request):
    # allowed_groups = ['superadmin']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'DELETE':
        job_id = request.GET.get('id')
        if job_id:
            # Lakukan penghapusan berdasarkan ID di sini
            data = MineUnits.objects.get(id=int(job_id))
            data.delete()
            return JsonResponse({'status': 'deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
