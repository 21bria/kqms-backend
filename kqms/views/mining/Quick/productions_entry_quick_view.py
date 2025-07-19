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
    if request.method != 'POST':
        return JsonResponse({'error': 'Metode HTTP tidak diizinkan'}, status=405)

    try:
        # Aturan validasi
        rules = {
            'date_production' : ['required'],
            'shift'           : ['required'],
            'time_loading'    : ['required'],
            'category_mine'   : ['required'],
            'id_material'     : ['required'],
            'digger'          : ['required'],
            'hauler_class'    : ['required'],
            'loading_point'   : ['required'],
            'dumping_point'   : ['required'],
            'ritase'          : ['required'],
        }

        # Pesan kesalahan validasi
        custom_messages = {
            'date_production.required': 'Date harus diisi.',
            'shift.required': 'Shift harus diisi.',
            'digger.required': 'Loader harus diisi.',
            'hauler_class.required': 'Hauler harus diisi.',
            'sources_area.required': 'Source harus diisi.',
            'loading_point.required': 'Loading point harus diisi.',
            'dumping_point.required': 'Dumping point harus diisi.',
            'category_mine.required': 'Category harus diisi.',
            'id_material.required': 'Material harus diisi.',
            'time_loading.required': 'Loading Time harus diisi.',
            'ritase.required': 'Ritase harus diisi.',
        }

        # Validasi input
        for field, field_rules in rules.items():
            for rule in field_rules:
                if rule == 'required' and not request.POST.get(field):
                    return JsonResponse({'error': custom_messages.get(f'{field}.required', f'{field} wajib diisi')}, status=400)

        # Ambil data dari request
        date_production = request.POST.get('date_production')
        shift           = request.POST.get('shift')
        loader          = request.POST.get('digger')
        hauler          = request.POST.get('hauler')
        hauler_class    = request.POST.get('hauler_class')
        sources_area    = request.POST.get('sources_area')
        loading_point   = request.POST.get('loading_point')
        dumping_point   = request.POST.get('dumping_point')
        dome_id         = request.POST.get('dome_id')
        category        = request.POST.get('category_mine')
        id_material     = request.POST.get('id_material')
        time_loading    = request.POST.get('time_loading')
        ritase          = request.POST.get('ritase')
        tonnage         = request.POST.get('tonnage')
        area            = request.POST.get('area')
        code            = request.POST.get('code')
        vendors         = request.POST.get('vendors')
        remarks         = request.POST.get('remarks')

        # Siapkan kode gabungan unik
        combinedCode = (
            (date_production[:10] if date_production else '') +
            (category or '') +
            (area or '') +
            (vendors or '')
        )

        # Ambil tanggal untuk left_date
        left_date = None
        if date_production:
            try:
                date_obj = datetime.strptime(date_production, '%Y-%m-%d')
                left_date = date_obj.day
            except ValueError:
                return JsonResponse({'error': 'Format tanggal tidak valid'}, status=400)

      
        # Simpan ke database dalam transaksi
        with transaction.atomic():
            mineQuickProductions.objects.create(
                date_production = date_production,
                shift           = shift,
                loader          = loader,
                # hauler          = hauler,
                sources         = sources_area,
                loading_point   = loading_point,
                dumping_point   = dumping_point,
                dome_id         = dome_id or None,
                category_mine   = category,
                id_material     = id_material,
                time_loading    = time_loading,
                ritase          = ritase,
                bcm             = 0,
                tonnage         = tonnage,
                hauler_class    = hauler_class,
                # hauler_type     = type_hauler,
                ref_materials   = combinedCode,
                no_production   = code,
                vendors         = vendors,
                left_date       = left_date,
                remarks         = remarks,
                id_user         = request.user.id
            )

        return JsonResponse({'success': True, 'message': 'Data berhasil disimpan.'})

    except IntegrityError as e:
        return JsonResponse({'error': 'Terjadi kesalahan integritas database', 'message': str(e)}, status=400)

    except Exception as e:
        return JsonResponse({'error': 'Terjadi kesalahan', 'message': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def update_quickProduction(request,id):
    try:
        # Aturan validasi
        rules = {
            'date_production': ['required'],
            'shift'          : ['required'],
            'digger'         : ['required'],
            'hauler_class'   : ['required'],
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
            'time_loading.required'   : 'Time harus diisi.',
            'category_mine.required'  : 'Category harus diisi.',
            'id_material.required'    : 'Material harus diisi.',
            'digger.required'         : 'Digger harus diisi.',
            'hauler_class.required'   : 'Hauler harus diisi.',
            'loading_point.required'  : 'Loading point harus diisi.',
            'dumping_point.required'  : 'Dumping point harus diisi.',
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
        # data.sources         = request.POST.get('sources')
        data.loading_point   = request.POST.get('loading_point')
        data.dumping_point   = request.POST.get('dumping_point')
        data.dome_id         = dome_id
        data.category_mine   = category
        data.id_material     = request.POST.get('id_material')
        data.time_loading    = request.POST.get('time_loading')
        data.ritase          = request.POST.get('ritase')
        data.tonnage         = request.POST.get('tonnage')
        data.hauler_class    = request.POST.get('hauler_class')
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
                # 'hauler'         : clean_string(items.hauler),
                # 'haulerName'     : clean_string(haulerName),
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