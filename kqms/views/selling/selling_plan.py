from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ...models.selling_plan import SellingPlan
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from datetime import datetime
from django.views.decorators.http import require_http_methods
from uuid import UUID

@login_required
def sale_plan_page(request):
    return render(request, 'admin-selling/plan/list-plan.html')

class sellingDataPlan(View):
    def post(self, request):
        # Ambil semua data invoice yang valid
        data_ore = self._datatables(request)
        return JsonResponse(data_ore, safe=False)

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
        data = SellingPlan.objects.all()

        if search:
            data = data.filter(
                Q(type_ore__icontains=search)
            )
       

        # Filter berdasarkan parameter dari request
        startDate  = request.POST.get('startDate')
        endDate    = request.POST.get('endDate')
        oreFilter  = request.POST.get('oreFilter')

        if startDate and endDate:
            data = data.filter(plan_date__range=[startDate, endDate])

        if oreFilter:
            data = data.filter(type_ore=oreFilter)

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
                "id"          : item.id,
                "plan_date"   : item.plan_date,
                "type_ore"    : item.type_ore,
                "ni_plan"     : item.ni_plan,
                "tonnage_plan": item.tonnage_plan,
                "created_at"  : item.created_at.strftime('%Y-%m-%d %H:%M:%S'), 
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
def create_plan_sale(request):
    if request.method == 'POST':
        try:
            # Aturan validasi
            rules = {
                'plan_date[]'   : ['required'],
                'type_ore[]'    : ['required'],
                'tonnage_plan[]': ['required'],
                'plan_ni[]'     : ['required'],
            }

            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'plan_date[].required'   : 'Plan date is required.',
                'type_ore[].required'    : 'Tipe ore is required.',
                'tonnage_plan[].required': 'Tonnage is required.',
                'plan_ni[].required'     : 'Ni Plan is required.',
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
                plan_date   = request.POST.getlist('plan_date[]')
                tonnage_plan= request.POST.getlist('tonnage_plan[]')
                plan_ni     = request.POST.getlist('plan_ni[]')
                type_ore    = request.POST.getlist('type_ore[]')

                # Loop untuk menyimpan setiap data sample
                for idx in range(len(plan_date)):

                    checkDup = plan_date[idx] + type_ore[idx] 

                    if plan_date[idx]:  # Akses elemen list menggunakan indeks `idx`
                        date_obj = datetime.strptime(plan_date[idx], '%Y-%m-%d')
                        left_date = date_obj.day
                    else:
                        left_date = None

                    if SellingPlan.objects.filter(check_duplicated=checkDup).exists():
                            return JsonResponse({'message': f'{checkDup} : already exists.'}, status=422)
    
                    # Simpan data baru
                    SellingPlan.objects.create(
                        plan_date        = plan_date[idx],
                        type_ore         = type_ore[idx],
                        tonnage_plan     = tonnage_plan[idx],
                        ni_plan          = plan_ni[idx],
                        check_duplicated = checkDup,
                        left_date        = left_date,
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
def getIdPlanSale(request, id):
    if request.method == 'GET':
        try:
            items = SellingPlan.objects.get(id=id)
            data = {
                'id'              : items.id,
                'plan_date'       : items.plan_date.strftime('%Y-%m-%d'),
                'type_ore'        : items.type_ore,
                'type_selling'    : items.type_selling,
                'tonnage_plan'    : items.tonnage_plan,
                'ni_plan'         : items.ni_plan,
                'check_duplicated': items.check_duplicated,
                'description'     : items.description,
                'left_date'       : items.left_date
        
            }
            return JsonResponse(data)
        except SellingPlan.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
@require_http_methods(["POST"])
def update_sale_plan(request, id):
    try:
        # Aturan validasi
        rules = {
            'plan_date'   : ['required'],
            'type_ore'    : ['required'],
            'tonnage_plan': ['required'],
            'ni_plan'     : ['required'],
        }

        # Pesan kesalahan validasi yang disesuaikan
        custom_messages = {
            'plan_date.required'   : 'Plan date is required.',
            'type_ore.required'    : 'Tipe ore is required.',
            'tonnage_plan.required': 'Tonnage is required.',
            'plan_ni.required'     : 'Ni Plan is required.',
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

        plan_date     = request.POST.get('plan_date')
        type_ore      = request.POST.get('type_ore')
        tonnage_plan  = request.POST.get('tonnage_plan')
        ni_plan       = request.POST.get('ni_plan')
        description   = request.POST.get('description')


        # Validasi duplikat
        checkDup = plan_date + type_ore 
        if SellingPlan.objects.exclude(id=id).filter(check_duplicated=checkDup).exists(): 
            return JsonResponse({'message': f'{checkDup} : already exists.'}, status=422)
        
        if plan_date:
            # Ubah string tanggal menjadi objek datetime
            date_obj = datetime.strptime(plan_date, '%Y-%m-%d') 
            left_date = date_obj.day
        else:
            left_date = None  # Atau berikan nilai default 

        # Dapatkan data yang akan diupdate berdasarkan ID
        data = SellingPlan.objects.get(id=id)

        # Lakukan update data dengan nilai baru
        data.plan_date    = plan_date
        data.type_ore     = type_ore
        data.tonnage_plan = tonnage_plan
        data.ni_plan      = ni_plan
        data.description  = description
        data.left_date    = left_date
        # data.id_user    = id_user

        # Simpan perubahan ke dalam database
        data.save()

        # Kembalikan respons JSON sukses
        return JsonResponse({'success': True, 'message': 'Data berhasil diupdate.'})

    except SellingPlan.DoesNotExist:
        return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    except IntegrityError as e:
        return JsonResponse({'error': 'Terjadi kesalahan integritas database', 'message': str(e)}, status=400)

    except ValidationError as e:
        return JsonResponse({'error': 'Validasi gagal', 'message': str(e)}, status=400)

    except Exception as e:
        return JsonResponse({'error': 'Terjadi kesalahan', 'message': str(e)}, status=500)

@login_required
def delete_sale_plan(request):
    # allowed_groups = ['superadmin','data-control']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    #     )

    if request.method == 'DELETE':
        job_id = request.GET.get('id')
        if not job_id:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'}, status=400)
        
        try:
            job_uuid = UUID(job_id)  # validasi UUID
            data = SellingPlan.objects.get(id=job_uuid)
            data.delete()
            return JsonResponse({'status': 'deleted'})
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid UUID format'}, status=400)
        except SellingPlan.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Data not found'}, status=404)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
