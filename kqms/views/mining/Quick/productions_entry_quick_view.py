# 
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from ....utils.utils import generate_quick_production
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime
from ....models.mine_productions import mineQuickProductions
from ....models.mine_productions_view import mineQuickProductionsView
from ....models.source_model import SourceMines,SourceMinesLoading,SourceMinesDumping,SourceMinesDome
from ....models.mine_units import MineUnits
from ....models.mine_addition_factor import mineAdditionFactor
from ....models.materials import Material
from ....utils.utils import clean_string

class viewproductionsQuickCreate(View):

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
        data = mineQuickProductionsView.objects.all()

        if search:
            data = data.filter(
                Q(shift__icontains=search) |
                Q(loader__icontains=search) |
                Q(hauler__icontains=search) |
                Q(sources_area__icontains=search) |
                Q(dumping_point__icontains=search) |
                Q(nama_material__icontains=search) |
                Q(category_mine__icontains=search) |
                Q(no_production__icontains=search)
            )
       

        # Filter berdasarkan parameter dari request
        code   = request.POST.get('code')

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
                "sources_area"      : item.sources_area,
                "loading_point"     : item.loading_point,
                "dumping_point"     : item.dumping_point,
                "dome_id"           : item.pile_id,
                "category_mine"     : item.category_mine,
                "time_loading"      : item.time_loading,
                "nama_material"     : item.nama_material,
                "ritase"            : item.ritase,
                "bcm"               : item.bcm,
                "bcm_total"         : item.bcm_total,
                "tonnage_total"     : item.tonnage_total,
                "mine_block"        : item.mine_block,
                "rl"                : item.rl,
                "vendors"           : item.vendors

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
def create_quick_production(request):
    if request.method == 'POST':
        try:
            # Aturan validasi
            rules = {
                'date_production[]' : ['required'],
                'shift[]'           : ['required'],
                'loader[]'          : ['required'],
                'hauler[]'          : ['required'],
                'sources_area[]'    : ['required'],
                'loading_point[]'   : ['required'],
                'dumping_point[]'   : ['required'],
                'category[]'        : ['required'],
                'id_material[]'     : ['required'],
                'time_loading[]'    : ['required'],
                'vendors'           : ['required'],
            }

            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'date_production[].required': 'Date harus diisi.',
                'shift[].required'          : 'Shift harus diisi.',
                'loader[].required'         : 'Loader harus diisi.',
                'hauler[].required'         : 'Hauler harus diisi.',
                'sources_area[].required'   : 'Source harus diisi.',
                'loading_point[].required'  : 'Loading point harus diisi.',
                'dumping_point[].required'  : 'Dumping point harus diisi.',
                'category[].required'       : 'Category harus diisi.',
                'id_material[].required'    : 'Material harus diisi.',
                'time_loading[].required'   : 'Loading Time harus diisi.',
                'vendors.required'   : 'vendors harus diisi.'

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

            # Cek unik data
            # sample_numbers = request.POST.getlist('sample_number[]')
            # for sample_number in sample_numbers:
            #     if SampleProductions.objects.filter(sample_number=sample_number).exists():
            #         return JsonResponse({'error': f'SampleID {sample_number} already exists.'}, status=400)
                
            # code  = request.POST.get('code')
           
            # Gunakan transaksi database untuk memastikan integritas data
            with transaction.atomic():
                # Dapatkan data dari request
                date_production = request.POST.getlist('date_production[]')
                shift           = request.POST.getlist('shift[]')
                loader          = request.POST.getlist('loader[]')
                hauler          = request.POST.getlist('hauler[]')
                sources_area    = request.POST.getlist('sources_area[]')
                loading_point   = request.POST.getlist('loading_point[]')
                dumping_point   = request.POST.getlist('dumping_point[]')
                dome_id         = request.POST.getlist('dome_id[]')
                category        = request.POST.getlist('category[]')
                id_material     = request.POST.getlist('id_material[]')
                time_loading    = request.POST.getlist('time_loading[]')
                # block_id        = request.POST.getlist('block_id[]')
                # from_rl         = request.POST.getlist('from_rl[]')
                # to_rl           = request.POST.getlist('to_rl[]')
                ritase          = request.POST.getlist('ritase[]')
                # bcm             = request.POST.getlist('bcm[]')
                # tonnage         = request.POST.getlist('tonnage[]')
                area            = request.POST.getlist('area[]')
                code            = request.POST.get('code')
                vendors         = request.POST.get('vendors')

                # Buat dictionary addition_factor untuk menampung bcm dan ton dari tabel yang sama
                addition_factor = {
                    f"{item['validation']}": {'bcm': item['tf_bcm'], 'ton': item['tf_ton']}
                    for item in mineAdditionFactor.objects.values('validation', 'tf_bcm', 'tf_ton')
                }   
                
                # Loop untuk menyimpan setiap data sample
                for idx in range(len(date_production)):
                    # Gabungkan nilai-nilai kolom menjadi Refresnsi Material
                    combinedCode = date_production[idx] + category[idx] + (area[idx] if area else '') + \
                                        (vendors if vendors else '') 
                    if date_production[idx]:  # Akses elemen list menggunakan indeks `idx`
                        date_obj = datetime.strptime(date_production[idx], '%Y-%m-%d')
                        left_date = date_obj.day
                    else:
                        left_date = None

                    # Ambil `unit_type` dari `MineUnits` berdasarkan `hauler` (unit_code)
                    hauler_unit  = get_object_or_404(MineUnits, unit_code=hauler[idx])
                    hauler_class = hauler_unit.unit_type if hauler_unit else None

                    # Ambil `nama_material` dari `Material` berdasarkan `id_material`
                    material      = get_object_or_404(Material, id=id_material[idx])
                    nama_material = material.nama_material if material else None

                    addition_key = f"{hauler_class.strip() if hauler_class else ''}{nama_material.strip() if nama_material else ''}"

                    # Dapatkan bcm_factor dan ton_factor dari addition_factor dictionary
                    bcm_factor = addition_factor.get(addition_key, {}).get('bcm', None)
                    ton_factor = addition_factor.get(addition_key, {}).get('ton', None)

                    hauler_class = str(hauler[idx]) if (hauler[idx]) else ''
                    # Modifikasi hauler_class
                    hauler_class = str(hauler[idx]) if hauler[idx] else ''  # Pastikan `hauler` menjadi string
                    if 'ADT' in hauler_class:
                        type_hauler = 'ADT'
                    elif 'DT' in hauler_class:
                        type_hauler = 'DT'
                    else:
                        type_hauler = None  # Hauler tidak valid atau tidak termasuk 'ADT' atau 'DT'  

                    # Simpan data sample baru
                    mineQuickProductions.objects.create(
                        date_production = date_production[idx],
                        shift           = shift[idx],
                        loader          = loader[idx],
                        hauler          = hauler[idx],
                        sources         = sources_area[idx],
                        loading_point   = loading_point[idx],
                        dumping_point   = dumping_point[idx],
                        dome_id         = dome_id[idx] if dome_id[idx] else None,  # Memastikan 'None' jika dome_id kosong
                        category_mine   = category[idx],
                        id_material     = id_material[idx],
                        time_loading    = time_loading[idx],
                        ritase          = ritase[idx], 
                        bcm             = bcm_factor,
                        tonnage         = ton_factor,
                        # block_id        = block_id[idx] if block_id[idx] else None,
                        # from_rl         = from_rl[idx],
                        # to_rl           = to_rl[idx],
                        hauler_class    = type_hauler,
                        hauler_type     = type_hauler,
                        ref_materials   = combinedCode,
                        no_production   = code, 
                        vendors         = vendors, 
                        left_date       = left_date, 
                        id_user         = request.user.id
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
@require_http_methods(["POST"])
def update_quickProduction(request,id):
    try:
        # Aturan validasi
        rules = {
            'date_production': ['required'],
            'shift'          : ['required'],
            'digger'         : ['required'],
            'hauler'         : ['required'],
            'sources'        : ['required'],
            'loading_point'  : ['required'],
            'dumping_point'  : ['required'],
            'category_mine'  : ['required'],
            'id_material'    : ['required'],
            'time_loading'   : ['required'],
            'ritase'         : ['required'],
        }

        # Pesan kesalahan validasi yang disesuaikan
        custom_messages = {
            'date_production.required': 'Date harus diisi.',
            'shift.required'          : 'Shift harus diisi.',
            'digger.required'         : 'Digger harus diisi.',
            'hauler.required'         : 'Hauler harus diisi.',
            'sources.required'        : 'Sources harus diisi.',
            'loading_point.required'  : 'Loading point harus diisi.',
            'dumping_point.required'  : 'Dumping point harus diisi.',
            'category_mine.required'  : 'Category harus diisi.',
            'id_material.required'    : 'Material harus diisi.',
            'time_loading.required'   : 'Time harus diisi.',
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
        refCodes     = f"{date}{category}{area}{vendor}"

        dome_id      = request.POST.get('dome_id')
        dome_id      = int(dome_id) if dome_id and dome_id != 'None' else None

        id_material  = request.POST.get('id_material')
        hauler       = request.POST.get('hauler')
        hauler_class = str(hauler) if (hauler) else ''

         # Ambil `unit_type` dari `MineUnits` berdasarkan `unit_code`
        hauler_unit  = get_object_or_404(MineUnits, unit_code=hauler)
        hauler_class = hauler_unit.unit_type if hauler_unit else None

        # Ambil `nama_material` dari `Material` berdasarkan `id_material`
        material      = get_object_or_404(Material, id=id_material)
        nama_material = material.nama_material if material else None

        addition_key = f"{hauler_class.strip() if hauler_class else ''}{nama_material.strip() if nama_material else ''}"

        # Dapatkan bcm_factor dan ton_factor dari addition_factor dictionary
        bcm_factor = addition_factor.get(addition_key, {}).get('bcm', None)
        ton_factor = addition_factor.get(addition_key, {}).get('ton', None)

        # Modifikasi hauler_class
        hauler_class = str(hauler) if hauler else ''  # Pastikan `hauler` menjadi string
        if 'ADT' in hauler_class:
            type_hauler = 'ADT'
        elif 'DT' in hauler_class:
            type_hauler = 'DT'
        else:
            type_hauler = None  # Hauler tidak valid atau tidak termasuk 'ADT' atau 'DT'  

        if date:
            # Ubah string tanggal menjadi objek datetime
            date_obj = datetime.strptime(date, '%Y-%m-%d')  # Sesuaikan format sesuai dengan input
            
            # Ambil hari (day) dari objek tanggal
            left_date = date_obj.day
        else:
            # Penanganan jika tgl_production tidak ada atau tidak valid
            left_date = None  # Atau berikan nilai default 

        # Dapatkan data yang akan diupdate berdasarkan ID
        data = mineQuickProductions.objects.get(id=id)

        # Lakukan update data dengan nilai baru
        data.date_production = date
        data.vendors         = vendor
        data.shift           = request.POST.get('shift')
        data.loader          = request.POST.get('digger')
        data.hauler          = request.POST.get('hauler')
        data.sources         = request.POST.get('sources')
        data.loading_point   = request.POST.get('loading_point')
        data.dumping_point   = request.POST.get('dumping_point')
        data.dome_id         = dome_id
        data.category_mine   = category
        data.id_material     = request.POST.get('id_material')
        data.time_loading    = request.POST.get('time_loading')
        data.ritase          = request.POST.get('ritase')
        data.bcm             = bcm_factor
        data.tonnage         = ton_factor
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

    # except mineQuickProductions.DoesNotExist:
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    except IntegrityError as e:
        return JsonResponse({'error': 'Terjadi kesalahan integritas database', 'message': str(e)}, status=400)

    except ValidationError as e:
        return JsonResponse({'error': 'Validasi gagal', 'message': str(e)}, status=400)

    except Exception as e:
        return JsonResponse({'error': 'Terjadi kesalahan', 'message': str(e)}, status=500)

@login_required
def delete_quick_production(request):
    if request.method == 'DELETE':
        get_id = request.GET.get('id')
        if get_id:
            data = mineQuickProductions.objects.get(id=int(get_id))
            data.delete()
            return JsonResponse({'status': 'deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def getIdQuickProduction(request):
    if request.method == 'GET':
        try:
            get_id = request.GET.get('id')
            items = mineQuickProductions.objects.get(id=get_id)
            sources_area  = None
            loadingPoint  = None
            dumpingPoint  = None
            domePoint     = None
            diggerName    = None
            haulerName    = None

            if items.sources:
                source = SourceMines.objects.filter(id=items.sources).first()
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

            if items.dumping_point:
                dome = SourceMinesDome.objects.filter(id=items.dumping_point).first()
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

            data = {
                'id': items.id,
                'date_production': items.date_production,
                'shift'          : clean_string(items.shift),
                'loader'         : clean_string(items.loader),
                'diggerName'     : clean_string(diggerName),
                'hauler'         : clean_string(items.hauler),
                'haulerName'     : clean_string(haulerName),
                'hauler_class'   : clean_string(items.hauler_class),
                'sources'        : items.sources,
                'sources_area'   : clean_string(sources_area),
                'loading_point'  : items.loading_point,
                'loadingPoint'   : clean_string(loadingPoint),
                'dumping_point'  : items.dumping_point,
                'dumpingPoint'   : clean_string(dumpingPoint),
                'dome_id'        : items.dome_id,
                'domePoint'      : clean_string(domePoint),
                'distance'       : items.distance,
                'category_mine'  : clean_string(items.category_mine),
                'block_id'       : items.block_id,
                'from_rl'        : items.from_rl,
                'to_rl'          : items.to_rl,
                'id_material'    : items.id_material,
                'ritase'         : items.ritase,
                'bcm'            : items.bcm,
                'tonnage'        : items.tonnage,
                'time_loading'   : clean_string(items.time_loading),
                'hauler_type'    : clean_string(items.hauler_type),
                'vendors'        : clean_string(items.vendors),
                'remarks'        : clean_string(items.remarks)
            }

            return JsonResponse(data)
        except mineQuickProductions.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)    

@login_required
def productions_quick_entry_page(request):
    production_entry = generate_quick_production()
    today = datetime.today()
    context = {
        'production_entry' : production_entry,
        'day_date'         : today.strftime('%Y-%m-%d'),
    }
    return render(request, 'admin-mine/production-entry-quick.html',context)