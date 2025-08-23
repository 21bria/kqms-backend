from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ...models.selling_plan_barging import SellingPlanBarging
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
import calendar
from datetime import datetime, timedelta
from django.db.models import Case, When, Value, IntegerField

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
        data = SellingPlanBarging.objects.all()

        if search:
            data = data.filter(
                Q(type_ore__icontains=search)
            )
       

        # Filter berdasarkan parameter dari request
        startDate  = request.POST.get('startDate')
        endDate    = request.POST.get('endDate')
        materialFilter  = request.POST.get('materialFilter')

        if startDate and endDate:
            data = data.filter(plan_date__range=[startDate, endDate])

        if materialFilter:
            data = data.filter(type_ore=materialFilter)

        # Atur sorting
        # if order_dir == 'desc':
        #     order_by = f'-{data.model._meta.fields[order_column].name}'
        # else:
        #     order_by = f'{data.model._meta.fields[order_column].name}'

        # data = data.order_by(order_by)


        # mapping order column datatables
        columns_map = {
            0: 'plan_date',
            1: 'type_ore',
            2: 'tonnage_plan',
            3: 'ni_plan',
            4: 'co_plan',
            5: 'fe_plan',
            6: 'sio2_plan',
            7: 'al2o3_plan',
            8: 'mgo_plan',
            9: 'sm_plan',
        }

        order_column = int(datatables.get('order[0][column]', -1))
        order_dir = datatables.get('order[0][dir]', 'asc')

        if order_column in columns_map:
            field_name = columns_map[order_column]
            order_by = f'-{field_name}' if order_dir == 'desc' else field_name
            data = data.order_by(order_by)
        else:
            data = data.annotate(
                material_order=Case(
                    When(type_ore="LIM", then=Value(1)),
                    When(type_ore="SAP", then=Value(2)),
                    default=Value(3),
                    output_field=IntegerField(),
                )
            ).order_by('-plan_date', 'material_order')

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
                "tonnage_plan": item.tonnage_plan,
                "ni_plan"     : item.ni_plan,
                "co_plan"     : item.co_plan,
                "fe_plan"     : item.fe_plan,
                "sio2_plan"   : item.sio2_plan,
                "al2o3_plan"  : item.al2o3_plan,
                "mgo_plan"    : item.mgo_plan,
                "sm_plan"     : item.sm_plan,
                "created_at"  : item.created_at.strftime('%Y-%m-%d %H:%M:%S')
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
                'ni_plan[]'     : ['required'],
                'co_plan[]'     : ['required'],
                'fe_plan[]'     : ['required'],
                'sio2_plan[]'   : ['required'],
                'al2o3_plan[]'   : ['required'],
                'mgo_plan[]'    : ['required']
            }

            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'plan_date[].required'   : 'Plan date is required.',
                'type_ore[].required'    : 'Tipe ore is required.',
                'tonnage_plan[].required': 'Tonnage is required.',
                'ni_plan[].required'     : 'Ni Plan is required.',
                'co_plan[].required'     : 'Co Plan is required.',
                'fe_plan[].required'     : 'Fe Plan is required.',
                'sio2_plan[].required'   : 'SiO2 Plan is required.',
                'al2o3_plan[].required'  : 'Al2O3 Plan is required.',
                'mgo_plan[].required'    : 'MgO Plan is required.'
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
                        
            # Ambil data dari form
            plan_date   = request.POST.getlist('plan_date[]')   # format input <input type="month"> → "YYYY-MM"
            type_ore    = request.POST.getlist('type_ore[]')
            tonnage_plan= request.POST.getlist('tonnage_plan[]')
            ni_plan     = request.POST.getlist('ni_plan[]')
            co_plan     = request.POST.getlist('co_plan[]')
            fe_plan     = request.POST.getlist('fe_plan[]')
            sio2_plan   = request.POST.getlist('sio2_plan[]')
            al2o3_plan  = request.POST.getlist('al2o3_plan[]')
            mgo_plan    = request.POST.getlist('mgo_plan[]')

                
            # Gunakan transaksi database untuk memastikan integritas data
            with transaction.atomic():
                for idx in range(len(plan_date)):

                    # plan_date di form pakai <input type="month"> → format "YYYY-MM"
                    year, month   = map(int, plan_date[idx].split('-'))
                    days_in_month = calendar.monthrange(year, month)[1]

                    # hitung tonnase per hari, dikali 1000
                    total_tonnage   = float(tonnage_plan[idx]) * 1000
                    tonnage_per_day = total_tonnage / days_in_month

                    # hitung sm_plan = SiO2 / MgO
                    try:
                        sm_value = float(sio2_plan[idx]) / float(mgo_plan[idx]) if float(mgo_plan[idx]) != 0 else None
                    except Exception:
                        sm_value = None

                    # generate tanggal harian
                    for day in range(1, days_in_month + 1):
                        current_date = datetime(year, month, day).date()

                        checkDup = f"{current_date}{type_ore[idx]}"

                        if SellingPlanBarging.objects.filter(check_duplicated=checkDup).exists():
                            continue  # skip kalau sudah ada

                        SellingPlanBarging.objects.create(
                            plan_date        = current_date,
                            type_ore         = type_ore[idx],
                            tonnage_plan     = tonnage_per_day,
                            ni_plan          = ni_plan[idx],
                            co_plan          = co_plan[idx],
                            fe_plan          = fe_plan[idx],
                            sio2_plan        = sio2_plan[idx],
                            al2o3_plan       = al2o3_plan[idx],
                            mgo_plan         = mgo_plan[idx],
                            sm_plan          = sm_value,
                            check_duplicated = checkDup,
                            id_user          = request.user.id
                        )

            return JsonResponse({'success': True, 'message': 'Data berhasil digenerate per hari dan disimpan.'})

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
            items = SellingPlanBarging.objects.get(id=id)
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
        except SellingPlanBarging.DoesNotExist:
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
            'ni_plan.required'     : 'Ni Plan is required.',
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
        if SellingPlanBarging.objects.exclude(id=id).filter(check_duplicated=checkDup).exists(): 
            return JsonResponse({'message': f'{checkDup} : already exists.'}, status=422)
        
        if plan_date:
            # Ubah string tanggal menjadi objek datetime
            date_obj = datetime.strptime(plan_date, '%Y-%m-%d') 
            left_date = date_obj.day
        else:
            left_date = None  # Atau berikan nilai default 

        # Dapatkan data yang akan diupdate berdasarkan ID
        data = SellingPlanBarging.objects.get(id=id)

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

    except SellingPlanBarging.DoesNotExist:
        return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    except IntegrityError as e:
        return JsonResponse({'error': 'Terjadi kesalahan integritas database', 'message': str(e)}, status=400)

    except ValidationError as e:
        return JsonResponse({'error': 'Validasi gagal', 'message': str(e)}, status=400)

    except Exception as e:
        return JsonResponse({'error': 'Terjadi kesalahan', 'message': str(e)}, status=500)

@login_required
@csrf_exempt
def delete_sale_plan(request):
    allowed_groups = ['superadmin','data-control','admin-mining','admin-mgoqa']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
        )

    if request.method == 'DELETE':
        try:
            import json
            body = json.loads(request.body.decode('utf-8'))
            month_date = body.get('month_date')   # format: YYYY-MM
            materials  = body.get('materials')    # bisa kosong / null / string

            if not month_date:
                return JsonResponse({'status': 'error', 'message': 'Month date required'}, status=400)

            # ambil tahun & bulan
            try:
                year, month = map(int, month_date.split('-'))
            except Exception:
                return JsonResponse({'status': 'error', 'message': 'Invalid month_date format'}, status=400)

            days_in_month = calendar.monthrange(year, month)[1]
            start_date = datetime(year, month, 1).date()
            end_date   = datetime(year, month, days_in_month).date()

            # filter query
            qs = SellingPlanBarging.objects.filter(plan_date__range=[start_date, end_date])
            if materials:
                qs = qs.filter(type_ore=materials)

            deleted_count, _ = qs.delete()

            return JsonResponse({'status': 'deleted', 'message': f'{deleted_count} record(s) deleted'})

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON body'}, status=400)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)