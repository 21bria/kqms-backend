from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from datetime import datetime,timedelta
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.db.models import F, Func, Value
from ....models.ore_productions import OreProductions
from ....models.ore_truck_factor import OreTruckFactor
from ....models.ore_production_view import OreProductionsView
from ....models.materials import Material
from ....models.ore_class import OreClass
from ....models.source_model import SourceMinesDome
from ....utils.utils import generate_ore_number
from ....utils.utils import clean_string



class Trim(Func):
    function = 'TRIM'

def safe_strip(value):
    return value.strip() if isinstance(value, str) else None

class orePdsCreate(View):

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
        data = OreProductionsView.objects.all()

        if search:
            data = data.filter(
                Q(shift__icontains=search) |
                Q(prospect_area__icontains=search) |
                Q(mine_block__icontains=search) |
                Q(nama_material__icontains=search) |
                Q(ore_class__icontains=search) |
                Q(grade_control__icontains=search) |
                Q(unit_truck__icontains=search) |
                Q(stockpile__icontains=search) |
                Q(pile_id__icontains=search) |
                Q(batch_code__icontains=search) |
                Q(batch_status__icontains=search) |
                Q(truck_factor__icontains=search) 
            )
       

        # Filter berdasarkan parameter dari request
        no_production   = request.POST.get('no_production')

        data = data.filter(no_production=no_production)
        # NOT IN
        # data = data.exclude(type_sample__in=['HOS', 'ROS','HOS_SPC','ROS_SPC','ROS_CKS','ROS_SPC','ROS_PSI','HOS_CKS','HOS_SPC'])

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
                "tgl_production": item.tgl_production,
                "category"      : item.category,
                "shift"         : item.shift,
                "prospect_area" : item.prospect_area,
                "mine_block"    : item.mine_block,
                "from_rl"       : item.from_rl,
                "to_rl"         : item.to_rl,
                "nama_material" : item.nama_material,
                "ore_class"     : item.ore_class,
                "ni_grade"      : item.ni_grade,
                "grade_control" : item.grade_control,
                "unit_truck"    : item.unit_truck,
                "stockpile"     : item.stockpile,
                "pile_id"       : item.pile_id,
                "batch_code"    : item.batch_code,
                "increment"     : item.increment,
                "batch_status"  : item.batch_status,
                "ritase"        : item.ritase,
                "tonnage"       : item.tonnage,
                "pile_status"   : item.pile_status,
                "truck_factor"  : item.truck_factor,
                "remarks"       : item.remarks,
                "sample_number" : item.sample_number,
                "username"      : item.username,
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
def create_ore(request):
    # allowed_groups = ['superadmin','data-control','admin-mgoqa']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    
    if request.method == 'POST':
        try:
            # Aturan validasi
            rules = {
                'tgl_production[]'   : ['required'],
                'category[]'            : ['required'],
                'shift[]'            : ['required'],
                'id_prospect_area[]' : ['required'],
                'id_block[]'         : ['required'],
                'id_material[]'      : ['required'],
                # 'id_stockpile[]'     : ['required'],
                'id_pile[]'          : ['required'],
                'batch_code[]'       : ['required'],
                'increment[]'        : ['required'],
                'batch_status[]'     : ['required'],
                'ritase[]'           : ['required'],
                'tonnage[]'          : ['required'],
                'ore_class[]'        : ['required'],
            }

            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'tgl_production[].required'  : 'Date harus diisi.',
                'category[].required'        : 'Category harus diisi.',
                'shift[].required'           : 'Shift harus diisi.',
                'id_prospect_area[].required': 'Source harus diisi.',
                'id_block[].required'        : 'Block harus diisi.',
                'id_material[].required'     : 'Material harus diisi.',
                # 'id_stockpile[].required'    : 'Stockpile harus diisi.',
                'id_pile[].required'         : 'Dome harus diisi.',
                'batch_code[].required'      : 'Batch harus diisi.',
                'increment[].required'       : 'increment harus diisi.',
                'batch_status[].required'    : 'Bacth status harus diisi.',
                'ritase[].required'          : 'Ritase harus diisi.',
                'tonnage[].required'         : 'Tonnage harus diisi.',
                'ore_class[].required'       : 'Ore Class harus diisi.',
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

           # Dapatkan id_stockpile berdasarkan id_pile
            id_stockpile = {}
            pile_id_list = request.POST.getlist('id_pile[]')

            for pile_id in pile_id_list:
                try:
                    # Menemukan objek berdasarkan id (primary key)
                    dome = SourceMinesDome.objects.get(id=pile_id)
                    # Pastikan id_dumping tidak None
                    if dome.id_dumping is not None:
                        id_stockpile[pile_id] = dome.id_dumping
                    else:
                        print(f"Pile ID {pile_id} tidak memiliki id_dumping.")
                except SourceMinesDome.DoesNotExist:
                    print(f"Tidak ditemukan data untuk pile_id: {pile_id}")

            # Gunakan transaksi database untuk memastikan integritas data
            with transaction.atomic():
                # Dapatkan data dari request
                tgl_production      = request.POST.getlist('tgl_production[]')
                category            = request.POST.getlist('category[]')
                shift               = request.POST.getlist('shift[]')
                id_prospect_area    = request.POST.getlist('id_prospect_area[]')
                id_block            = request.POST.getlist('id_block[]')
                from_rl             = request.POST.getlist('from_rl[]')
                to_rl               = request.POST.getlist('to_rl[]')
                id_material         = request.POST.getlist('id_material[]')
                grade_expect        = request.POST.getlist('grade_expect[]')
                grade_control       = request.POST.getlist('grade_control[]')
                # id_stockpile        = request.POST.getlist('id_stockpile[]')
                id_pile             = request.POST.getlist('id_pile[]')
                batch_code          = request.POST.getlist('batch_code[]')
                increment           = request.POST.getlist('increment[]')
                batch_status        = request.POST.getlist('batch_status[]')
                ritase              = request.POST.getlist('ritase[]')
                tonnage             = request.POST.getlist('tonnage[]')
                # pile_status         = request.POST.getlist('pile_status[]')
                unit_truck          = request.POST.getlist('unit_truck[]')
                truck_factor        = request.POST.getlist('truck_factor[]')
                ore_class           = request.POST.getlist('ore_class[]')
                remarks             = request.POST.getlist('remarks[]')
                sale_adjust         = request.POST.getlist('sale_adjust[]')
                no_production       = request.POST.get('no_production')

                # Loop untuk menyimpan setiap data sample
                for idx in range(len(tgl_production)):
                    # Gabungkan nilai-nilai kolom menjadi kode batch
                    # kodeBatch = 'PDS' + id_material[idx] + unit_truck[idx] + id_stockpile[idx] + id_pile[idx] + batch_code[idx]
                    kodeBatch = 'PDS' + id_material[idx] + unit_truck[idx] + str(id_stockpile.get(id_pile[idx], '')) + id_pile[idx] + batch_code[idx]
                    kodeBatch = kodeBatch.replace(" ", "")  # Menghapus spasi

                    if tgl_production[idx]:  # Akses elemen list menggunakan indeks `idx`
                        date_obj = datetime.strptime(tgl_production[idx], '%Y-%m-%d')
                        left_date = date_obj.day
                    else:
                        left_date = None
                  
                    # Simpan data sample baru
                    OreProductions.objects.create(
                        tgl_production   = tgl_production[idx],
                        category         = category[idx],
                        shift            = shift[idx],
                        id_prospect_area = id_prospect_area[idx],
                        id_block         = id_block[idx],
                        from_rl          = from_rl[idx],
                        to_rl            = to_rl[idx],
                        id_material      = id_material[idx],
                        grade_expect     = grade_expect[idx],
                        grade_control    = grade_control[idx],
                        # id_stockpile     = id_stockpile[idx],
                        id_pile          = id_pile[idx],
                        batch_code       = batch_code[idx],
                        increment        = increment[idx],
                        batch_status     = batch_status[idx],
                        ritase           = ritase[idx],
                        tonnage          = tonnage[idx],
                        pile_status      = 'Continue',
                        unit_truck       = unit_truck[idx],
                        truck_factor     = truck_factor[idx],
                        ore_class        = ore_class[idx],
                        kode_batch       = kodeBatch,
                        status_dome      = 'Continue',
                        sale_adjust      = sale_adjust[idx],
                        no_production    = no_production,
                        left_date        = left_date,
                        remarks          = remarks[idx],
                        id_user          = request.user.id  # Sesuaikan dengan cara Anda mendapatkan user ID
                    )

                    # Jika batch_status adalah 'Complete', lakukan pembaruan
                    if batch_status[idx].strip() == 'Complete':
                        OreProductions.objects.filter(
                            # id_stockpile=id_stockpile[idx],
                            id_pile=id_pile[idx],
                            batch_code=batch_code[idx]
                        ).update(batch_status=batch_status[idx].strip())

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
def update_ore(request, id):
    # allowed_groups = ['superadmin','data-control','admin-mgoqa']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    try:
        # Aturan validasi
        rules = {
            'tgl_production'    : ['required'],
            'category'          : ['required'],
            'shift'             : ['required'],
            'id_prospect_area'  : ['required'],
            'id_block'          : ['required'],
            'id_material'       : ['required'],
            'id_stockpile'      : ['required'],
            'id_pile'           : ['required'],
            'ritase'            : ['required'],
            'tonnage'           : ['required'],
            'batch_code'        : ['required'],
            'increment'         : ['required'],
            'batch_status'      : ['required'],
            'pile_status'       : ['required'],
            'ore_class'         : ['required'],
            'truck_factor'      : ['required']
        }

        # Pesan kesalahan validasi yang disesuaikan
        custom_messages = {
            'tgl_production.required'     : 'Date harus diisi.',
            'category.required'           : 'Category harus diisi.',
            'shift.required'              : 'Shift harus diisi.',
            'id_prospect_area.required'   : 'Source harus diisi.',
            'id_block.required'           : 'Block harus diisi.',
            'id_material.required'        : 'Material harus diisi.',
            'id_stockpile.required'       : 'Stockpile harus diisi.',
            'id_pile.required'            : 'Dome harus diisi.',
            'ritase.required'             : 'Ritase harus diisi.',
            'tonnage.required'            : 'Tonnage harus diisi.',
            'batch_code.required'         : 'Batch harus diisi.',
            'increment.required'          : 'increment harus diisi.',
            'batch_status.required'       : 'Bacth status harus diisi.',
            'pile_status.required'        : 'Status Dome harus diisi.',
            'ore_class.required'          : 'Ore Class harus diisi.',
            'truck_factor.required'       : 'Truck factor harus diisi.',
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

        # Gabungkan nilai-nilai kolom menjadi kode batch
        type          = 'PDS'
        id_material   = request.POST.get('id_material')
        unit_truck    = request.POST.get('unit_truck').strip()
        id_stockpile  = request.POST.get('id_stockpile')
        id_pile       = request.POST.get('id_pile')
        batch_code    = request.POST.get('batch_code').strip()
        # KodeBatch = f"{type}{id_material}{unit_truck}{id_stockpile}{id_pile}{batch_code}"
        kodeBatch  = f"{type}{id_material}{unit_truck}{id_stockpile}{id_pile}{batch_code}"
        kodeBatch  = kodeBatch .replace(" ", "")  # Menghapus spasi

        
        tgl_production  = request.POST.get('tgl_production')
        if tgl_production:
            # Ubah string tanggal menjadi objek datetime
            date_obj = datetime.strptime(tgl_production, '%Y-%m-%d')  # Sesuaikan format sesuai dengan input
            
            # Ambil hari (day) dari objek tanggal
            left_date = date_obj.day
        else:
            # Penanganan jika tgl_production tidak ada atau tidak valid
            left_date = None  # Atau berikan nilai default 

        
        # Dapatkan data yang akan diupdate berdasarkan ID
        data = OreProductions.objects.get(id=id)

        # Lakukan update data dengan nilai baru
        data.tgl_production   = tgl_production
        data.category         = request.POST.get('category').strip()
        data.shift            = request.POST.get('shift').strip()
        data.id_prospect_area = request.POST.get('id_prospect_area')
        data.id_block         = request.POST.get('id_block')
        data.from_rl          = request.POST.get('from_rl')
        data.to_rl            = request.POST.get('to_rl')
        data.id_material      = id_material 
        data.grade_control    = request.POST.get('grade_control').strip()
        data.grade_expect     = request.POST.get('grade_expect')
        # data.id_stockpile     = id_stockpile
        data.id_pile          = id_pile
        data.batch_code       = batch_code
        data.increment       = request.POST.get('increment')
        data.batch_status     = request.POST.get('batch_status').strip()
        data.unit_truck       = unit_truck
        data.ritase           = request.POST.get('ritase')
        data.tonnage          = request.POST.get('tonnage')
        data.pile_status      = request.POST.get('pile_status')
        data.truck_factor     = request.POST.get('truck_factor')
        data.kode_batch       = kodeBatch 
        data.ore_class        = request.POST.get('ore_class')
        data.no_production    = request.POST.get('no_production')
        data.left_date        = left_date
        data.remarks          = request.POST.get('remarks')
        data.status_dome      = 'Continue'
        data.sale_adjust      = request.POST.get('sale_adjust')
        data.id_user          = request.user.id  # Pastikan user sudah login sebelumnya

        # Lakukan pembaruan jika batch_status adalah 'Complete'
        if data.batch_status == 'Complete':
            OreProductions.objects.filter(
                # id_stockpile=id_stockpile,
                id_pile=id_pile,
                batch_code=batch_code
            ).update(batch_status='Complete')

        # Simpan perubahan ke dalam database
        data.save()

        # Kembalikan respons JSON sukses
        return JsonResponse({'success': True, 'message': 'Data successfully updated.'})

    except OreProductions.DoesNotExist:
        return JsonResponse({'error': 'Data not found'}, status=404)

    except IntegrityError as e:
        return JsonResponse({'error': 'A database integrity error occurred', 'message': str(e)}, status=400)

    except ValidationError as e:
        return JsonResponse({'error': 'Validation failed', 'message': str(e)}, status=400)

    except Exception as e:
        return JsonResponse({'error': 'There is an error', 'message': str(e)}, status=500)

@login_required
def delete_ore_temp(request):
    allowed_groups = ['superadmin','admin-mgoqa']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )

    if request.method == 'DELETE':
        job_id = request.GET.get('id')
        if job_id:
            # Lakukan penghapusan berdasarkan ID di sini
            data = OreProductions.objects.get(id=int(job_id))
            data.delete()
            return JsonResponse({'status': 'deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def getOreTonnage(request, id):
    if request.method == 'GET':
        try:
            # Bersihkan ID sebelum query
            cleaned_id = clean_string(id)
            print(f"Cleaned ID: {cleaned_id}")

            # Query ke database dengan ID yang sudah dibersihkan
            dataGet = get_object_or_404(OreTruckFactor, reference_tf=cleaned_id)
            # Bersihkan data hasil query
            data = {
                'ton': dataGet.ton,
                'type_tf': safe_strip(dataGet.type_tf)
            }
            
            return JsonResponse(data)
        
        except OreTruckFactor.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request'}, status=400)

def get_ore_classes(request):
    material_id = request.GET.get('material_id')

    # Periksa apakah material_id ada dan valid
    if not material_id:
        return JsonResponse({'error': 'Material ID is required'}, status=400)

    # Pastikan untuk mengkonversi material_id ke integer
    try:
        material_id = int(material_id)
    except ValueError:
        return JsonResponse({'error': 'Invalid Material ID'}, status=400)

    # Ambil ore_classes berdasarkan material_id dan trim nilai 'ore_class'
    ore_classes = OreClass.objects.filter(material_id=material_id).annotate(
        ore_class_trimmed=Trim(F('ore_class'))).values('id', 'ore_class_trimmed')

    if not ore_classes:
        return JsonResponse([], safe=False)  # Kembalikan list kosong jika tidak ada data

    # Rename key agar sesuai dengan output JSON yang diharapkan
    trimmed = [
        {'id': item['id'], 'ore_class': item['ore_class_trimmed']} for item in ore_classes
    ]

    return JsonResponse(trimmed, safe=False)
    
def get_truck_factors(request):
    material_id = request.GET.get('material_id')
    if not material_id:  # Jika material_id kosong
        return JsonResponse([], safe=False)

    # Pastikan material_id adalah angka
    try:
        material_id = int(material_id)
    except ValueError:
        return JsonResponse([], safe=False)

    ore_factors = OreTruckFactor.objects.filter(material=material_id).values('type_tf', 'type_tf')
    # Ambil data dan trim nilai type_tf
    ore_factors = OreTruckFactor.objects.filter(material=material_id).values_list('type_tf', flat=True)
    trimmed_factors = [{'type_tf': type_tf.strip()} for type_tf in ore_factors]

    return JsonResponse(trimmed_factors, safe=False)
    # return JsonResponse(list(ore_factors), safe=False)

@login_required
def ore_entry_page(request):
    ore_entry = generate_ore_number()
    material  = Material.objects.filter(nama_material__in=['LIM', 'SAP'])
    today     = datetime.today()

    # Kurangi satu hari
    yesterday = today - timedelta(days=1)
   
    context = {
        'ore_entry': ore_entry,
        'material' : material,
        'day_date' : yesterday.strftime('%Y-%m-%d'),
    }
    return render(request, 'admin-mgoqa/production-ore/ore-entry.html',context)