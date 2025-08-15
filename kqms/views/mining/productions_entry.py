# 
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.views import View
from ...utils.utils import generate_production_number
from django.views.decorators.http import require_http_methods
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from datetime import datetime
from uuid import UUID
from ...models.mine_productions import mineProductions
from ...models.mine_productions_view import mineProductionsView
from ...models.source_model import SourceMines,SourceMinesLoading,SourceMinesDumping,SourceMinesDome
from ...models.mine_units import MineUnits
from ...models.mine_addition_factor import mineAdditionFactor
from ...models.materials import Material

def clean_post_value(val):
    if val in (None, '', 'None', 'null'):
        return None
    return val

class viewproductionsCreate(View):

    def post(self, request):
        # Ambil semua data invoice yang valid
        data_pds = self._datatables(request)
        return JsonResponse(data_pds, safe=False)

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
        data = mineProductionsView.objects.all()

        if search:
            data = data.filter(
                Q(shift__icontains=search) |
                Q(sources_area__icontains=search) |
                Q(dumping_point__icontains=search) |
                Q(nama_material__icontains=search) |
                Q(no_production__icontains=search)
            )
       

        # Filter berdasarkan parameter dari request
        code   = request.POST.get('no_production')

        data = data.filter(no_production=code)

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
            object_list = paginator.page(paginator.num_pages).object_lis

        data = [
         
            {
                "id"                : item.id,
                "date_production"   : item.date_production,
                "shift"             : item.shift,
                "loader"            : item.loader,
                "hauler"            : item.hauler,
                "hauler_class"      : item.hauler_class,
                "sources_area"       : item.sources_area,
                "loading_point"     : item.loading_point,
                "dumping_point"     : item.dumping_point,
                "dome_id"           : item.dome_id,
                "category_mine"     : item.category_mine,
                "time_loading"      : item.time_loading,
                "nama_material"     : item.nama_material,
                "ritase"            : item.ritase,
                "tonnage"           : item.tonnage 
                
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
def create_production(request):
    if request.method == 'POST':
        try:
            # Aturan validasi (tetap)
            rules = {
                'date_production[]' : ['required'],
                'shift[]'           : ['required'],
                'time_loading[]'    : ['required'],
                'loader[]'          : ['required'],
                'hauler[]'          : ['required'],
                'hauler_class[]'    : ['required'],
                'loading_point[]'   : ['required'],
                'dumping_point[]'   : ['required'],
                'category[]'        : ['required'],
                'id_material[]'     : ['required'],
                'time_loading[]'    : ['required'],
            }

            custom_messages = {
                'date_production[].required': 'Date harus diisi.',
                'shift[].required'          : 'Shift harus diisi.',
                'time_loading[].required'   : 'Time harus diisi.',
                'loader[].required'         : 'Loader harus diisi.',
                'hauler[].required'         : 'Hauler harus diisi.',
                'hauler_class[].required'   : 'Hauler Class harus diisi.',
                'loading_point[].required'  : 'Loading point harus diisi.',
                'dumping_point[].required'  : 'Dumping point harus diisi.',
                'category[].required'       : 'Category harus diisi.',
                'id_material[].required'    : 'Material harus diisi.',
                'time_loading[].required'   : 'Loading Time harus diisi.',
            }

            # VALIDASI: pakai getlist utk field []
            for field, field_rules in rules.items():
                for rule in field_rules:
                    if rule == 'required':
                        if not request.POST.getlist(field):
                            return JsonResponse({'error': custom_messages[f'{field}.required']}, status=400)

            with transaction.atomic():
                date_production = request.POST.getlist('date_production[]')
                shift           = request.POST.getlist('shift[]')
                time_loading    = request.POST.getlist('time_loading[]')
                loader          = request.POST.getlist('loader[]')
                hauler          = request.POST.getlist('hauler[]')
                hauler_class    = request.POST.getlist('hauler_class[]')
                loading_point   = request.POST.getlist('loading_point[]')
                dumping_point   = request.POST.getlist('dumping_point[]')
                dome_id         = request.POST.getlist('dome_id[]')
                category        = request.POST.getlist('category[]')
                id_material     = request.POST.getlist('id_material[]')
                ritase          = request.POST.getlist('ritase[]')
                tonnage         = request.POST.getlist('tonnage[]')
                vendors         = request.POST.get('vendors')
                # area            = request.POST.get('area')
                no_production   = request.POST.get('no_production')

                for idx in range(len(date_production)):
                    # combinedCode = (date_production[idx] + category[idx] + (area or '') + (vendors or '')).replace(' ', '')

                    date_obj  = datetime.strptime(date_production[idx], '%Y-%m-%d') if date_production[idx] else None
                    left_date = date_obj.day if date_obj else None

                    # hauler_type
                    haulerClass = str(hauler[idx]) if hauler[idx] else ''
                    if 'ADT' in haulerClass:
                        type_hauler = 'ADT'
                    elif 'DT' in haulerClass:
                        type_hauler = 'DT'
                    else:
                        type_hauler = None

                    # Ambil ID numerik per index
                    lp_id       = int(loading_point[idx]) if loading_point[idx] else None
                    dp_id       = int(dumping_point[idx]) if dumping_point[idx] else None
                    material_id = int(id_material[idx])   if id_material[idx]   else None
                    dome_val    = int(dome_id[idx])       if (dome_id and dome_id[idx]) else None

                    # Turunkan sources_area (ID) dari loading_point
                    sources_area_val = None
                    area_name = ''
                    if lp_id is not None:
                        try:
                            loading_obj = SourceMinesLoading.objects.select_related('id_sources').get(id=lp_id)
                            sources_area_val = loading_obj.id_sources_id or None   # ID untuk simpan ke FK
                            area_name = loading_obj.id_sources.sources_area or ''  # NAMA untuk combinedCode
                        except SourceMinesLoading.DoesNotExist:
                            sources_area_val = None
                            area_name = ''

                    # REF CODE: pakai nama source dari loading_point
                    combinedCode = f"{date_production[idx]}{category[idx]}{area_name}{vendors or ''}".replace(' ', '')


                    # CREATE: pakai nama field asli (tanpa _id), tapi nilai harus integer
                    mineProductions.objects.create(
                        date_production = date_production[idx],
                        shift           = shift[idx],
                        time_loading    = time_loading[idx],
                        loader          = loader[idx],
                        hauler          = hauler[idx],
                        hauler_class    = hauler_class[idx],

                        sources_area    = sources_area_val,  # <-- integer (ID), bukan teks
                        loading_point   = lp_id,             # <-- integer
                        dumping_point   = dp_id,             # <-- integer
                        id_material     = material_id,       # <-- integer
                        dome_id         = dome_val,          # <-- integer / None

                        category_mine   = category[idx],
                        hauler_type     = type_hauler,
                        ref_materials   = combinedCode,
                        ritase          = ritase[idx],
                        bcm             = 0,
                        tonnage         = tonnage[idx],
                        no_production   = no_production,
                        vendors         = vendors,
                        left_date       = left_date,
                        id_user         = request.user.id
                    )


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
@require_http_methods(["POST"])
def update_Production(request,id):
    try:
        # Aturan validasi
        rules = {
            'date_production': ['required'],
            'shift'          : ['required'],
            'time_loading'   : ['required'],
            'digger'         : ['required'],
            'hauler'         : ['required'],
            # 'sources'        : ['required'],
            'loading_point'  : ['required'],
            'dumping_point'  : ['required'],
            'category_mine'  : ['required'],
            'id_material'    : ['required'],
            'ritase'         : ['required'],
        }

        # Pesan kesalahan validasi yang disesuaikan
        custom_messages = {
            'date_production.required': 'Date harus diisi.',
            'shift.required'          : 'Shift harus diisi.',
            'time_loading.required'   : 'Time harus diisi.',
            'digger.required'         : 'Digger harus diisi.',
            'hauler.required'         : 'Hauler harus diisi.',
            # 'sources.required'        : 'Sources harus diisi.',
            'loading_point.required'  : 'Loading point harus diisi.',
            'dumping_point.required'  : 'Dumping point harus diisi.',
            'category_mine.required'  : 'Category harus diisi.',
            'id_material.required'    : 'Material harus diisi.',
            'ritase.required'         : 'Ritase harus diisi.'
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

        # Buat dictionary addition_factor untuk menampung bcm dan ton dari tabel yang sama
        addition_factor = {
            f"{item['validation']}": {'bcm': item['tf_bcm'], 'ton': item['tf_ton']}
            for item in mineAdditionFactor.objects.values('validation', 'tf_bcm', 'tf_ton')
        }   

       
        # Gabungkan nilai-nilai kolom menjadi refrensi
        date         = request.POST.get('date_production')
        category     = request.POST.get('category_mine')
        area         = request.POST.get('area')
        vendor       = request.POST.get('vendors')
  

        dome_id = request.POST.get('dome_id')

        if not dome_id or dome_id.lower() in ('none', 'null'):
            dome_id = None
        else:
            try:
                dome_id = int(dome_id)
            except ValueError:
                dome_id = None

                
        id_material  = request.POST.get('id_material')
        hauler       = request.POST.get('hauler')
        hauler_class = clean_post_value(request.POST.get('hauler_class'))


        # addition_key = f"{hauler_class.strip() if hauler_class else ''}{nama_material.strip() if nama_material else ''}"

        # # Dapatkan bcm_factor dan ton_factor dari addition_factor dictionary
        # bcm_factor = addition_factor.get(addition_key, {}).get('bcm', None)
        # ton_factor = addition_factor.get(addition_key, {}).get('ton', None)

       
        # Modifikasi hauler_class
        haulerClass = str(hauler) if hauler else ''  # Pastikan `hauler` menjadi string
        if 'ADT' in haulerClass:
            type_hauler = 'ADT'
        elif 'DT' in haulerClass:
            type_hauler = 'DT'
        else:
            type_hauler = None  # Hauler tidak valid atau tidak termasuk 'ADT' atau 'DT'  

        if date:
            # Ubah string tanggal menjadi objek datetime
            date_obj = datetime.strptime(date, '%Y-%m-%d') 
            
            # Ambil hari (day) dari objek tanggal
            left_date = date_obj.day
        else:
            left_date = None 

        # Dapatkan data yang akan diupdate berdasarkan ID
        data = mineProductions.objects.get(id=id)   
                    
        # Ambil sources_area otomatis dari loading_point
        loading_point   = request.POST.get('loading_point')
        # --- sources_area dari loading_point (FK) ---
        sources_area_id = None
        area_name = ''  # untuk nama sumber
        if loading_point:
            try:
                loading_obj = SourceMinesLoading.objects.select_related('id_sources').get(id=int(loading_point))
                sources_area_id = loading_obj.id_sources_id or None
                area_name = loading_obj.id_sources.sources_area or ''  # <-- Ambil nama
            except (ValueError, SourceMinesLoading.DoesNotExist):
                sources_area_id = None
                area_name = ''

        
           # refCodes     = f"{date}{category}{area}{vendor}"
        refCodes     = f"{date}{category}{area_name}{vendor}".replace(" ", "") #Hapus krakter spasi

        # Lakukan update data dengan nilai baru
        data.date_production = date
        data.vendors         = vendor
        data.shift           = request.POST.get('shift')
        data.loader          = request.POST.get('digger')
        data.hauler          = hauler
        data.sources_area    = sources_area_id   
        data.loading_point   = loading_point
        data.dumping_point   = request.POST.get('dumping_point')
        data.dome_id         = dome_id
        data.category_mine   = category
        data.id_material     = id_material
        data.time_loading    = request.POST.get('time_loading')
        data.ritase          = request.POST.get('ritase')
        data.bcm             = 0
        data.tonnage         = request.POST.get('tonnage')
        data.hauler_class    = hauler_class
        data.hauler_type     = type_hauler
        data.remarks         = request.POST.get('remarks')
        data.ref_materials   = refCodes
        data.left_date       = left_date
        data.id_user         = request.user.id

        # Simpan perubahan ke dalam database
        data.save()

        # Kembalikan respons JSON sukses
        return JsonResponse({'success': True, 'message': 'Data berhasil diupdate.'})

    # except mineProductions.DoesNotExist:
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    except IntegrityError as e:
        return JsonResponse({'error': 'Terjadi kesalahan integritas database', 'message': str(e)}, status=400)

    except ValidationError as e:
        return JsonResponse({'error': 'Validasi gagal', 'message': str(e)}, status=400)

    except Exception as e:
        return JsonResponse({'error': 'Terjadi kesalahan', 'message': str(e)}, status=500)

@login_required
def delete_mine_production(request):
    allowed_groups = ['superadmin','data-control','admin-mining']
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
            job_uuid = UUID(job_id)  # validasi UUID
            data = mineProductions.objects.get(id=job_uuid)
            data.delete()
            return JsonResponse({'status': 'deleted'})
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid UUID format'}, status=400)
        except mineProductions.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Data not found'}, status=404)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@login_required
def getIdProduction(request):
    if request.method == 'GET':
        try:
            get_id = request.GET.get('id')
            items = mineProductions.objects.get(id=get_id)

            sources_area  = None
            loadingPoint  = None
            dumpingPoint  = None
            domePoint     = None
            diggerName    = None
            haulerName    = None

            if items.sources_area:
                source = SourceMines.objects.filter(id=items.sources_area).first()
                if source:
                    sources_area = source.sources_area

            if items.loading_point:
                loading = SourceMinesLoading.objects.filter(id=items.loading_point).first()
                if loading:
                    loadingPoint = loading.loading_point

            if items.dumping_point:
                dumping = SourceMinesDumping.objects.filter(id=items.dumping_point).first()
                if dumping:
                    dumpingPoint = dumping.dumping_point

            if items.dome_id:
                dome = SourceMinesDome.objects.filter(id=items.dome_id).first()
                if dome:
                    domePoint = dome.pile_id

            if items.loader:
                digger = MineUnits.objects.filter(unit_code=items.loader).first()
                if digger:
                    diggerName = digger.unit_code

            if items.hauler:
                hauler = MineUnits.objects.filter(unit_code=items.hauler).first()
                if hauler:
                    haulerName = hauler.unit_code

            # Ambil jam dari time_loading yang formatnya datetime.time
            # time_loading_full = items.time_loading  # datetime.time(10, 20, 0)

            # if time_loading_full:
            #     time_loading_hour = time_loading_full.hour  # int, misal 8
            # else:
            #     time_loading_hour = None

            data = {
                'id'              : items.id,
                'date_production' : items.date_production, 
                'time_loading'    : items.time_loading, 
                'shift'           : items.shift,
                'loader'          : items.loader,
                'diggerName'      : diggerName,
                'hauler'          : items.hauler,
                'haulerName'      : haulerName,
                'hauler_class'    : items.hauler_class,
                'sources'         : items.sources_area,
                'sources_area'    : sources_area,
                'loading_point'   : items.loading_point,
                'loadingPoint'    : loadingPoint,
                'dumping_point'   : items.dumping_point,
                'dumpingPoint'    : dumpingPoint,
                'dome_id'         : items.dome_id,
                'domePoint'       : domePoint,
                'distance'        : items.distance,
                'category_mine'   : items.category_mine,
                'id_material'     : items.id_material,
                'ritase'          : items.ritase,
                'bcm'             : items.bcm,
                'tonnage'         : items.tonnage,
                # 'time_loading'    : f"{time_loading_hour:02d}" if time_loading_hour is not None else '',
                'hauler_type'     : items.hauler_type,
                'vendors'         : items.vendors,
                'remarks'         : items.remarks
            }
            return JsonResponse(data)
        
        except mineProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)    

@login_required
def productions_entry_page(request):
    production_no = generate_production_number()
    today = datetime.today()
    context = {
        'production_no' : production_no,
        'day_date'      : today.strftime('%Y-%m-%d'),
    }
    return render(request, 'admin-mine/production-entry.html',context)