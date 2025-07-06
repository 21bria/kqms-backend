from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ....models.ore_class import OreClass
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
from ....utils.utils import clean_string

@login_required
def OreClass_page(request):
    return render(request, 'master/list-ore-class.html')

class OreClass_List(View):
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
        records_total = OreClass.objects.all().count()
        # Set records filtered
        records_filtered = records_total
        # Ambil semua yang valid
        data = OreClass.objects.all()

        if search:
            data = OreClass.objects.filter(
                Q(ore_class__icontains=search)
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
                "ore_class":item.ore_class,
                "min_grade":item.min_grade,
                "max_grade":item.max_grade,
                "status":item.status,
                "created_at":item.created_at
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
def get_OreClass(request, id):
    # allowed_groups = ['superadmin','admin-mgoqa']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'GET':
        try:
            job = OreClass.objects.get(id=id)
            data = {
                'id'         : job.id,
                'ore_class'  : clean_string(job.ore_class), 
                'min_grade'  : clean_string(job.min_grade),
                'max_grade'  : clean_string(job.max_grade),
                'status'     : job.status
            }
            return JsonResponse(data)
        except OreClass.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def insert_OreClass(request):
    # allowed_groups = ['superadmin','admin-mgoqa']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'POST':
        try:
            # Aturan validasi
            rules = {
                'ore_class': ['required'],
                'min_grade': ['required'],
                'max_grade': ['required']
            }

            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'ore_class.required' : 'Class Ore is required.',
                'min_grade.required': 'Min is required.',
                'max_grade.required'  : 'Max is required.'
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
                ore_class   = request.POST.get('ore_class')
                min_grade  = request.POST.get('min_grade')
                max_grade   = request.POST.get('max_grade')

                if OreClass.objects.filter(ore_class=ore_class).exists():
                        return JsonResponse({'message': f'{ore_class} : already exists.'}, status=422)
    
                # Simpan data baru
                OreClass.objects.create(
                    ore_class=ore_class,
                    min_grade=min_grade,
                    max_grade=max_grade,
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
def update_OreClass(request, id):
    # allowed_groups = ['superadmin','admin-mgoqa']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'POST':
        try:
            # validasi
            rules = {
                'ore_class': ['required'],
                'min_grade': ['required'],
                'max_grade': ['required']
            }

            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'ore_class.required' : 'Class Ore is required.',
                'min_grade.required': 'Min is required.',
                'max_grade.required'  : 'Max is required.'
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

            ore_class = request.POST.get('ore_class')
            if OreClass.objects.exclude(id=id).filter(ore_class=ore_class).exists():
                return JsonResponse({'error': f'SampleID {ore_class} already exists.'}, status=400)

            # Dapatkan data yang akan diupdate berdasarkan ID
            data = OreClass.objects.get(id=id)

            # Lakukan update data dengan nilai baru
            data.ore_class=ore_class
            data.min_grade=request.POST.get('min_grade')
            data.max_grade=request.POST.get('max_grade')

            # Simpan perubahan ke dalam database
            data.save()

            # Kembalikan respons JSON sukses
            return JsonResponse({'success': True, 'message': 'Data berhasil diupdate.'})

        except OreClass.DoesNotExist:
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
def delete_OreClass(request):
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
            data = OreClass.objects.get(id=int(job_id))
            data.delete()
            return JsonResponse({'status': 'deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
