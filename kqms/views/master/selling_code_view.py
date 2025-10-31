from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ...models.selling_code import SellingCode
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.shortcuts import render
from django.views.generic import View
from django.db.models import Q
from ...utils.utils import clean_string


@login_required
def code_page(request):
    return render(request, 'master/list-selling-code.html') 

class SaleCodeList(View):

    def post(self, request):
        # Ambil semua data invoice yang valid
        data = self._datatables(request)
        return JsonResponse(data, safe=False)
        
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
        records_total = SellingCode.objects.all().count()
        # Set records filtered
        records_filtered = records_total
        # Ambil semua yang valid
        code = SellingCode.objects.all()

        if search:
            code = SellingCode.objects.filter(
                Q(product_code__icontains=search) |
                Q(type__icontains=search)
            )
            records_total = code.count()
            records_filtered = records_total

        # Atur sorting
        if order_dir == 'desc':
            order_by = f'-{code.model._meta.fields[order_column].name}'
        else:
            order_by = f'{code.model._meta.fields[order_column].name}'

        code = code.order_by(order_by)

        # Atur paginator
        paginator = Paginator(code, length)

        try:
            object_list = paginator.page(start // length + 1).object_list
        except PageNotAnInteger:
            object_list = paginator.page(1).object_list
        except EmptyPage:
            object_list = paginator.page(paginator.num_pages).object_list

        data = [
            {
                "id"            : item.id,
                "product_code"  : item.product_code,
                "description"   : item.description,
                "active"        : item.active,
                "type"          : item.type,
                "truck_factors" : item.truck_factors,
                "sublot_close"  : item.sublot_close,
                "group_close"   : item.group_close,
                "ritase_max"    : item.ritase_max,
                "ni"            : item.ni,
                "fe"            : item.fe,
                "mgo"           : item.mgo,
                "sio2"          : item.sio2,
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
def get_code(request, id):
    allowed_groups = ['superadmin','admin-mgoqa','data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )
    if request.method == 'GET':
        try:
            job = SellingCode.objects.get(id=id)
            data = {
                'id': job.id,
                'product_code' : clean_string(job.product_code), 
                'description'  : clean_string(job.description),
                'active'       : clean_string(job.active), 
                'type'         : clean_string(job.type), 
                'truck_factors': job.truck_factors, 
                'sublot_close' : clean_string(job.sublot_close), 
                'group_close'  : job.group_close, 
                'ritase_max'   : job.ritase_max, 
                'ni'           : job.ni, 
                'fe'           : job.fe,
                'mgo'          : job.mgo,
                'sio2'         : job.sio2,
                'created_at'   : job.created_at
            }
            return JsonResponse(data)
        except SellingCode.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def insert_code(request):
    allowed_groups = ['superadmin', 'admin-mgoqa', 'data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'},
            status=403
        )

    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Metode tidak diizinkan'}, status=405)

    # Aturan dan pesan validasi
    rules = {
        'product_code'  : ['required'],
        'type'          : ['required'],
        'truck_factors' : ['required'],
        'sublot_close'  : ['required'],
        'group_close'   : ['required'],
        'ritase_max'    : ['required']
    }

    custom_messages = {
        'product_code.required' : 'Code is required.',
        'type.required'         : 'Type is required.',
        'truck_factors.required': 'Truck Factors is required.',
        'sublot_close.required' : 'Sublot is required.',
        'group_close.required'  : 'Group is required.',
        'ritase_max.required'   : 'Ritase is required.',
    }

    # Validasi input
    cleaned_data = {}
    for field, field_rules in rules.items():
        value = request.POST.get(field, '').strip()
        if 'required' in field_rules and not value:
            return JsonResponse({'error': custom_messages[f'{field}.required']}, status=400)
        cleaned_data[field] = value

    product_code    = cleaned_data['product_code']
    type_code       = cleaned_data['type']
    truck_factors   = request.POST.get('truck_factors')
    sublot_close    = cleaned_data['sublot_close']
    group_close     = cleaned_data['group_close']
    ritase_max      = cleaned_data['ritase_max']
    ni              = request.POST.get('ni')
    fe              = request.POST.get('fe')
    mgo             = request.POST.get('mgo')
    sio2            = request.POST.get('sio2')
    description     = request.POST.get('description', '').strip()
    active = 1

    # Cek duplikat manual sebelum simpan
    if SellingCode.objects.filter(product_code=product_code).exists():
        return JsonResponse({'status': 'error', 'message': 'Product code already exists.'}, status=400)

    # Simpan ke database
    try:
        new_code = SellingCode.objects.create(
            product_code=product_code,
            type=type_code,
            description=description,
            truck_factors=truck_factors,
            sublot_close=sublot_close,
            group_close=group_close,
            ritase_max=ritase_max,
            ni=float(ni) if ni and ni.replace('.', '', 1).isdigit() else 0.0,
            fe=float(fe) if fe and fe.replace('.', '', 1).isdigit() else 0.0,
            mgo=float(mgo) if mgo and mgo.replace('.', '', 1).isdigit() else 0.0,
            sio2=float(sio2) if sio2 and sio2.replace('.', '', 1).isdigit() else 0.0,
            active=active
        )
        return JsonResponse({
            'status': 'success',
            'message': 'Data berhasil disimpan.',
            'data': {
                'id': new_code.id,
                'product_code': new_code.product_code,
                'description': new_code.description,
                'active': new_code.active,
                'type': new_code.type,
                'created_at': new_code.created_at
            }
        })
    except IntegrityError:
        # Fallback jika validasi manual gagal mendeteksi duplikat
        return JsonResponse({'status': 'error', 'message': 'Product code already exists (DB constraint).'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
@login_required
def update_code(request, id):
    allowed_groups = ['superadmin', 'admin-mgoqa', 'data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'},
            status=403
        )

    if request.method != 'POST':
        return JsonResponse({'error': 'Metode tidak diizinkan'}, status=405)

    try:
        rules = {
            'product_code'  : ['required'],
            'type'          : ['required'],
            'truck_factors' : ['required'],
            'sublot_close'  : ['required'],
            'group_close'   : ['required'],
            'ritase_max'    : ['required'],
            'active'        : ['required']
        }

        custom_messages = {
            'product_code.required' : 'Code is required.',
            'type.required'         : 'Type is required.',
            'truck_factors.required': 'Truck Factors is required.',
            'sublot_close.required' : 'Sublot is required.',
            'group_close.required'  : 'Group is required.',
            'ritase_max.required'   : 'Ritase is required.',
            'active.required'       : 'Active is required.',
        }


        cleaned_data = {}
        for field, field_rules in rules.items():
            value = request.POST.get(field, '').strip()
            if 'required' in field_rules and not value:
                return JsonResponse({'error': custom_messages[f'{field}.required']}, status=400)
            cleaned_data[field] = value

        # Ambil data yang akan diupdate
        job = SellingCode.objects.get(id=int(id))

        # Cek duplikat product_code untuk record lain
        if SellingCode.objects.filter(product_code=cleaned_data['product_code']).exclude(id=job.id).exists():
            return JsonResponse({'error': 'Product code already exists.'}, status=400)
        ni   = request.POST.get('ni')
        fe   = request.POST.get('fe')
        mgo  = request.POST.get('mgo')
        sio2 = request.POST.get('sio2')

        # Update field
        job.product_code  = cleaned_data['product_code']
        job.description   = request.POST.get('description', '').strip()
        job.type          = cleaned_data['type']
        job.truck_factors = request.POST.get('truck_factors')
        job.sublot_close  = request.POST.get('sublot_close')
        job.group_close   = request.POST.get('group_close')
        job.ritase_max    = request.POST.get('ritase_max')
        job.ni            = float(ni) if ni and ni.replace('.', '', 1).isdigit() else 0.0
        job.fe            = float(fe) if fe and fe.replace('.', '', 1).isdigit() else 0.0
        job.mgo           = float(mgo) if mgo and mgo.replace('.', '', 1).isdigit() else 0.0
        job.sio2          = float(sio2) if sio2 and sio2.replace('.', '', 1).isdigit() else 0.0
        active_value      = request.POST.get('active')
        job.active        = int(active_value) if active_value is not None else 1
      
        job.save()

        return JsonResponse({
            'id'            : job.id,
            'product_code'  : job.product_code,
            'description'   : job.description,
            'active'        : job.active,
            'type'          : job.type,
            'truck_factors' : job.truck_factors,
            'sublot_close'  : job.sublot_close,
            'group_close'   : job.group_close,
            'ritase_max'    : job.ritase_max,
            'created_at'    : job.created_at
        })

    except SellingCode.DoesNotExist:
        return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
    except IntegrityError:
        return JsonResponse({'error': 'Product code already exists (DB constraint)'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def delete_code(request):
    allowed_groups = ['superadmin','data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )
    if request.method == 'DELETE':
        job_id = request.GET.get('id')
        if job_id:
            # Lakukan penghapusan berdasarkan ID di sini
            data = SellingCode.objects.get(id=int(job_id))
            data.delete()
            return JsonResponse({'status': 'deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

