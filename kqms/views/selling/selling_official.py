from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ...models.selling_official import SellingOfficial
from ...models.selling_official_view import sellingOfficialView
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from ...models.selling_code import SellingCode
from django.views.decorators.http import require_http_methods
from ...utils.utils import clean_string
@login_required
def sale_official_page(request):
    return render(request, 'admin-selling/official/list-official.html')

class sellingDataOfficial(View):
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
        data = sellingOfficialView.objects.all()

        if search:
            data = data.filter(
                Q(product_code__icontains=search) |
                Q(code_surveyor__icontains=search) |
                Q(type_selling__icontains=search)
            )
       
        # Filter berdasarkan parameter dari request
        typeFilter = request.POST.get('typeFilter')

        if typeFilter:
            data = data.filter(type_selling=typeFilter)

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
                "id"                : item.id,
                "type_selling"      : item.type_selling,
                "code_surveyor"     : item.code_surveyor,
                "name_surveyor"     : item.name_surveyor,
                "barge_code"        : item.barge_code,
                "so_number"         : item.so_number,
                "product_code"      : item.product_code,
                "tonnage"           : item.tonnage,
                "ni"                : item.ni,
                "co"                : item.co,
                "al2o3"             : item.al2o3,
                "cao"               : item.cao,
                "cr2o3"             : item.cr2o3,
                "fe"                : item.fe,
                "mgo"               : item.mgo,
                "sio2"              : item.sio2,
                "mno"               : item.mno,
                "mc"                : item.mc,
                "sm"                : item.sm,
                "start_date"        : item.start_date,
                "end_date"          : item.end_date
                # "created_at"  : item.created_at.strftime('%Y-%m-%d %H:%M:%S'), 

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
def create_official_sale(request):
    if request.method == 'POST':
        try:
            # Aturan validasi
            rules = {
                'type_selling' : ['required'],
                'product_code' : ['required'],
                'id_surveyor'  : ['required'],
                'id_factory'   : ['required'],
                'official'    : ['required'],
                'tonnage'      : ['required'],
                'ni'           : ['required'],
                'fe'           : ['required'],
                'co'           : ['required'],
                'mgo'          : ['required'],
                'al2o3'        : ['required'],
                'sio2'         : ['required'],
                'cao'          : ['required'],
                'cr2o3'        : ['required'],
                'mno'          : ['required'],
                'mc'           : ['required'],
            }

            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'type_selling.required'  : 'Type* !!',
                'product_code.required'  : 'Code* !!',
                'id_surveyor.required'   : 'Surveyor* !!',
                'id_factory.required'    : 'Discharging* !!',
                'official.required'      : 'Official* !!',
                'tonnage.required'       : 'Tonagge* ',
                'ni.required'            : 'Ni* ',
                'fe.required'            : 'Fe* ',
                'co.required'            : 'Co* ',
                'mgo.required'           : 'Mgo* ',
                'al2o3.required'         : 'Al2O3* ',
                'sio2.required'          : 'SiO2* ',
                'cao.required'           : 'CaO* ',
                'cr2o3.required'         : 'Cr2O3* ',
                'mno.required'           : 'MnO* ',
                'mc.required'            : 'MC* '
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
                product_code = request.POST.get('product_code')
                id_surveyor  = request.POST.get('id_surveyor')

                checkDup = product_code + id_surveyor

                if SellingOfficial.objects.filter(check_duplicated=checkDup).exists():
                            return JsonResponse({'message': f'{checkDup} : already exists.'}, status=422)
    
                # Simpan data baru
                SellingOfficial.objects.create(
                    type_selling = request.POST.get('type_selling'),
                    product_code = product_code,
                    start_date   = request.POST.get('start_date'),
                    end_date     = request.POST.get('end_date'),
                    id_surveyor  = id_surveyor,
                    so_number    = request.POST.get('so_number'),
                    id_factory   = request.POST.get('id_factory'),
                    official     = request.POST.get('official'),
                    tonnage      = request.POST.get('tonnage'),
                    ni           = request.POST.get('ni'),
                    fe           = request.POST.get('fe'),
                    co           = request.POST.get('co'),
                    mgo          = request.POST.get('mgo'),
                    al2o3        = request.POST.get('al2o3'),
                    sio2         = request.POST.get('sio2'),
                    cao          = request.POST.get('cao'),
                    cr2o3        = request.POST.get('cr2o3'),
                    mno          = request.POST.get('mno'),
                    mc           = request.POST.get('mc'),
                    description  = request.POST.get('description'),
                    # # id_user  =auth()->id(),
                    check_duplicated=checkDup
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
def getIdOfficial(request, id):
    if request.method == 'GET':
        try:
            items = SellingOfficial.objects.get(id=id)
            code_name     = None
            if items.product_code:
                product = SellingCode.objects.filter(id=items.product_code).first()
                if product:
                    code_name = product.product_code
            data = {
                'id'          : items.id,
                'id_surveyor' : items.id_surveyor,
                'official'    : items.official,
                'type_selling': items.type_selling,
                'tonnage'     : items.tonnage,
                'id_factory'  : items.id_factory,
                'so_number'   : items.so_number,
                'product_code'  : items.product_code,
                'code_name'     : clean_string(code_name),
                'official_code': items.official_code,
                'ni'          : items.ni,
                'co'          : items.co,
                'al2o3'       : items.al2o3,
                'cao'         : items.cao,
                'cr2o3'       : items.cr2o3,
                'fe'          : items.fe,
                'mgo'         : items.mgo,
                'sio2'        : items.sio2,
                'mno'         : items.mno,
                'mc'          : items.mc,
                'start_date'  : items.start_date.strftime('%Y-%m-%d'),
                'end_date'    : items.end_date.strftime('%Y-%m-%d'),
                'description' : items.description,
        
            }
            return JsonResponse(data)
        except SellingOfficial.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
@require_http_methods(["POST"])
def update_official(request, id):
    try:
        # Aturan validasi
        rules = {
                'type_selling' : ['required'],
                'product_code' : ['required'],
                'id_surveyor'  : ['required'],
                'id_factory'   : ['required'],
                'official'     : ['required'],
                'tonnage'      : ['required'],
                'ni'           : ['required'],
                'fe'           : ['required'],
                'co'           : ['required'],
                'mgo'          : ['required'],
                'al2o3'        : ['required'],
                'sio2'         : ['required'],
                'cao'          : ['required'],
                'cr2o3'        : ['required'],
                'mno'          : ['required'],
                'mc'           : ['required'],
        }

        # Pesan kesalahan validasi yang disesuaikan
        custom_messages = {
                'type_selling.required'  : 'Type* !!',
                'product_code.required'  : 'Code Lot* !!',
                'id_surveyor.required'   : 'Surveyor* !!',
                'id_factory.required'    : 'Discharging* !!',
                'official.required'      : 'Official* !!',
                'tonnage.required'       : 'Tonagge* ',
                'ni.required'            : 'Ni* ',
                'fe.required'            : 'Fe* ',
                'co.required'            : 'Co* ',
                'mgo.required'           : 'Mgo* ',
                'al2o3.required'         : 'Al2O3* ',
                'sio2.required'          : 'SiO2* ',
                'cao.required'           : 'CaO* ',
                'cr2o3.required'         : 'Cr2O3* ',
                'mno.required'           : 'MnO* ',
                'mc.required'            : 'MC* '
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

        product_code = request.POST.get('product_code')
        id_surveyor  = request.POST.get('id_surveyor')
        # Validasi duplikat

        checkDup   = f"{product_code}{id_surveyor}"
        if SellingOfficial.objects.exclude(id=id).filter(check_duplicated=checkDup).exists(): 
            return JsonResponse({'message': f'{checkDup} : already exists.'}, status=422)
        
        # Dapatkan data yang akan diupdate berdasarkan ID
        data = SellingOfficial.objects.get(id=id)

        # Lakukan update data dengan nilai baru
        data.type_selling  = request.POST.get('type_selling')
        data.product_code  = product_code
        data.start_date    = request.POST.get('start_date')
        data.end_date      = request.POST.get('end_date')
        data.id_surveyor   = id_surveyor
        data.so_number     = request.POST.get('so_number')
        data.id_factory    = request.POST.get('id_factory')
        data.official      = request.POST.get('official')
        data.official_code = request.POST.get('official_code')
        data.tonnage       = request.POST.get('tonnage')
        data.ni            = request.POST.get('ni')
        data.fe            = request.POST.get('fe')
        data.co            = request.POST.get('co')
        data.mgo           = request.POST.get('mgo')
        data.al2o3         = request.POST.get('al2o3')
        data.sio2          = request.POST.get('sio2')
        data.cao           = request.POST.get('cao')
        data.cr2o3         = request.POST.get('cr2o3')
        data.mno           = request.POST.get('mno')
        data.mc            = request.POST.get('mc')
        data.description   = request.POST.get('description')
       # data.id_user  =auth()->id(),
        data.check_duplicated=checkDup

        # Simpan perubahan ke dalam database
        data.save()

        # Kembalikan respons JSON sukses
        return JsonResponse({'success': True, 'message': 'Data berhasil diupdate.'})

    except SellingOfficial.DoesNotExist:
        return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    except IntegrityError as e:
        return JsonResponse({'error': 'Terjadi kesalahan integritas database', 'message': str(e)}, status=400)

    except ValidationError as e:
        return JsonResponse({'error': 'Validasi gagal', 'message': str(e)}, status=400)

    except Exception as e:
        return JsonResponse({'error': 'Terjadi kesalahan', 'message': str(e)}, status=500)

@login_required
def delete_sale_official(request):
    if request.method == 'DELETE':
        job_id = request.GET.get('id')
        if job_id:
            data = SellingOfficial.objects.get(id=int(job_id))
            data.delete()
            return JsonResponse({'status': 'deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

