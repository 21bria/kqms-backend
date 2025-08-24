from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ....models.selling_barging import SellingBarging
from ....models.selling_details_barging_view import SellingDetailsBargingView
from ....models.materials import Material
from ....models.master_barge import BargeUnits
from ....models.source_model import SourceMines,SourceMinesLoading,SourceMinesDumping,SourceMinesDome
from ....models.selling_code import SellingCode
from django.db.models import Sum, Count
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from django.views import View
from datetime import datetime
from django.db.models import Case, When, Value, IntegerField
from uuid import UUID

@login_required
def barging_entry_page(request):
    today = datetime.today()
    context = {
        'today'     : today.strftime('%Y-%m-%d'),
        'no_entry'  : today.strftime('%Y%m%d'),
    }
    return render(request, 'admin-selling/entry/entry-barging-form.html',context)

class BargingTemp(View):
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

        # Gunakan fungsi get_joined_data
        data = SellingDetailsBargingView.objects.all()

        if search:
            data = data.filter(
                Q(shift__icontains=search) |
                Q(dome__icontains=search) |
                Q(material__icontains=search) |
                Q(code_lot__icontains=search) |
                Q(code_sub__icontains=search) |
                Q(batch__icontains=search) 
            )
       

        # Filter berdasarkan parameter dari request
        no_production   = request.POST.get('no_production')
        data = data.filter(no_input=no_production)
   
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
                "id"            : item.id,
                "date_hauling"  : item.date_hauling,
                "shift"         : item.shift,
                "time_hauling"  : item.time_hauling,
                "dome"          : item.dome,
                "material"      : item.material,
                "barge_code"    : item.barge_code,
                "code_lot"      : item.code_lot,
                "code_inc"      : item.code_inc,
                "code_sub"      : item.code_sub,
                "ritase"        : item.ritase,
                "tonnage"       : round(item.tonnage, 2),
                "sale_adjust"   : item.sale_adjust,
                "direct"        : item.direct,
                "created_at"    : item.created_at.strftime('%Y-%m-%d %H:%M:%S')
                            
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
def create_barging_data(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Metode HTTP tidak diizinkan'}, status=405)

    try:
        # Validasi input
        rules = {
            'date_hauling[]': ['required'],
            'shift[]'       : ['required'],
            'time_loading[]': ['required'],
            'id_pile[]'     : ['required'],
            'id_material[]' : ['required'],
            'barge_code[]'  : ['required'],
            'code_lot[]'    : ['required'],
            'code_inc[]'    : ['required'],
            'code_sub[]'    : ['required'],
            'sale_adjust[]' : ['required'],
            'direct[]'      : ['required'],
        }

        # Pesan kesalahan validasi
        custom_messages = {
            'date_hauling[].required' : 'Date is required.',
            'shift[].required'        : 'Shift is required.',
            'time_loading[].required' : 'Time is required.',
            'id_pile[].required'      : 'Dome is required.',
            'id_material[].required'  : 'Material is required.',
            'barge_code[].required'   : 'Barging is required.',
            'code_lot[].required'     : 'Code Lot is required.',
            'code_inc[].required'     : 'Truck is required.',
            'code_sub[].required'     : 'SubLot is required.',
            'sale_adjust[].required'  : 'Sale adjust is required.',
            'direct[].required'       : 'Direct is required.',
        }

        # Validasi input
        for field, field_rules in rules.items():
            for rule in field_rules:
                if rule == 'required' and not request.POST.get(field):
                    return JsonResponse({'error': custom_messages.get(f'{field}.required', f'{field} wajib diisi')}, status=400)


        # Simpan ke database
        with transaction.atomic():
            date_hauling = request.POST.getlist('date_hauling[]')
            shift        = request.POST.getlist('shift[]')
            time_hauling = request.POST.getlist('time_loading[]')
            id_pile      = request.POST.getlist('id_pile[]')
            id_material  = request.POST.getlist('id_material[]')
            barge_code   = request.POST.getlist('barge_code[]')
            code_lot     = request.POST.getlist('code_lot[]')
            code_inc     = request.POST.getlist('code_inc[]')
            code_sub     = request.POST.getlist('code_sub[]')
            sale_adjust  = request.POST.getlist('sale_adjust[]')
            direct       = request.POST.getlist('direct[]')
            no_input     = request.POST.get('no_production')

            for idx in range(len(date_hauling)):
                lot = code_lot[idx]
                sub = code_sub[idx]
                inc = code_inc[idx]

                # SellingCode
                try:
                    selling_code = SellingCode.objects.get(product_code=lot)
                except SellingCode.DoesNotExist:
                    return JsonResponse({'error': f'SellingCode {lot} tidak ditemukan'}, status=404)

                ritase_group = selling_code.ritase_max or 0
                tonnage      = (selling_code.ritase_max or 0) * (selling_code.truck_factors or 0)

                # Material
                material_obj = Material.objects.filter(id=id_material[idx]).first()
                if not material_obj:
                    return JsonResponse({'error': f'Material {id_material[idx]} tidak ditemukan'}, status=404)

                nama_material = material_obj.nama_material.upper()
                type_selling = 'LIS' if nama_material == 'LIM' else 'SAS' if nama_material == 'SAP' else None

                # Dome
                dome_obj = SourceMinesDome.objects.filter(id=id_pile[idx]).first()
                if not dome_obj:
                    return JsonResponse({'error': f'Dome {id_pile[idx]} tidak ditemukan'}, status=404)

                id_stockpile = dome_obj.id_dumping


                ex_kodeBatch     = (type_selling or '') + str(id_material[idx]) + 'Split_CAR' + \
                   (code_lot[idx] if code_lot else '') + (code_sub[idx] if code_sub else '')

                ex_kodeBatchPulp = (type_selling or '') + (code_lot[idx] if code_lot else '') + \
                                'Split_CAR' + (code_sub[idx] if code_sub else '')

                kodeBatch        = (type_selling or '') + str(id_material[idx]) + \
                                (code_lot[idx] if code_lot else '') + (code_sub[idx] if code_sub else '')


                # Create
                SellingBarging.objects.create(
                    date_hauling   = date_hauling[idx],
                    date_barging   = date_hauling[idx],
                    time_hauling   = time_hauling[idx],
                    shift          = shift[idx],
                    id_material    = id_material[idx],
                    id_pile        = id_pile[idx],
                    id_stockpile   = id_stockpile,
                    code_inc       = inc,
                    code_sub       = sub,
                    code_lot       = lot,
                    barge_code     = barge_code[idx],
                    tonnage        = tonnage,
                    ritase_group   = ritase_group,
                    type_selling   = type_selling,
                    sale_adjust    = sale_adjust[idx],
                    direct         = direct[idx],
                    id_user        = request.user.id,
                    date_barge_in  = date_hauling[idx],
                    date_barge_out = date_hauling[idx],
                    batch           = sub,
                    code_batch_ex   = ex_kodeBatch,
                    code_batch_pulp = ex_kodeBatchPulp,
                    code_batch_in   = kodeBatch,
                    sale_dome       = 'Continue',
                    status_barging  = 'Continue',
                    no_input        = no_input
                )


        return JsonResponse({'success': True, 'message': 'Data berhasil disimpan.'})

    except Exception as e:
        return JsonResponse({'error': 'Terjadi kesalahan', 'message': str(e)}, status=500)
        

@login_required
def delete_barging_temp(request):
    allowed_groups = ['superadmin','admin-mgoqa','data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )
    
    if request.method == 'DELETE':
        job_id = request.GET.get('id')
        if not job_id:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'}, status=400)
        try:
            job_uuid = UUID(job_id)  # validasi UUID format
            data = SellingBarging.objects.get(id=job_uuid)
            data.delete()
            return JsonResponse({'status': 'deleted'})
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid UUID format'}, status=400)
        except SellingBarging.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Data not found'}, status=404)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@login_required
def get_sale_quick(request, id):
    if request.method == 'GET':
        try:
            items = SellingBarging.objects.get(id=id)
            dumping_point = None
            dome_point    = None
            code_name     = None   

            if items.id_stockpile:
                dumping = SourceMinesDumping.objects.filter(id=items.id_stockpile).first()
                dumping_point = dumping.dumping_point if dumping else None

            if items.id_pile:
                dome = SourceMinesDome.objects.filter(id=items.id_pile).first()
                dome_point = dome.pile_id if dome else None

            product   = SellingCode.objects.filter(product_code=items.code_lot).first()
            code_name = product.product_code if product else None

            data = {
                'id'            : items.id,
                'code_lot'      : items.code_lot, 
                'code_name'     : code_name,
                'barge_code'    : items.barge_code,
                'date_hauling'  : items.date_hauling,
                'time_hauling'  : items.time_hauling,
                'shift'         : items.shift,
                'id_material'   : items.id_material,
                'stockpile'     : dumping_point,
                'dome'          : dome_point,
                'unit_code'     : items.unit_code,
                'tonnage'       : items.tonnage,
                'type_selling'  : items.type_selling,
                'code_inc'      : items.code_inc,
                'code_sub'      : items.code_sub,
                'code_sub_auto' : items.code_sub_auto,
                'sale_adjust'   : items.sale_adjust,
                'no_urut'       : items.no_urut,
                'remarks'       : items.remarks
            }
            return JsonResponse(data)

        except SellingBarging.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

