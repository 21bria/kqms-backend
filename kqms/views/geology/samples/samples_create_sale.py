# 
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from ....models.sample_production import SampleProductions
from ....models.samples_data_view import SamplesView
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from ....utils.utils import generate_sample_number
from django.http import JsonResponse
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from datetime import datetime

class viewEntrySale(View):
    def post(self, request):
        # Ambil semua data invoice yang valid
        data_sample = self._datatables(request)
        return JsonResponse(data_sample, safe=False)

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
        data = SamplesView.objects.all()

        if search:
            data = data.filter(
                Q(shift__icontains=search) |
                Q(factory_stock__icontains=search) |
                Q(product_code__icontains=search) |
                Q(nama_material__icontains=search) |
                Q(batch_code__icontains=search) |
                Q(sample_number__icontains=search) |
                Q(no_sample__icontains=search)
            )
       

        # Filter berdasarkan parameter dari request
        no_sample   = request.POST.get('no_sample')

        data = data.filter(no_sample=no_sample)
        # NOT IN
        data = data.filter(type_sample__in=['HOS', 'ROS','HOS_SPC','ROS_SPC','ROS_CKS','ROS_SPC','ROS_PSI','HOS_CKS','HOS_SPC'])

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
                "tgl_sample"        : item.tgl_sample,
                "shift"             : item.shift,
                "type_sample"       : item.type_sample,
                "sample_method"     : item.sample_method,
                "factory_stock"     : item.factory_stock,
                "product_code"      : item.product_code,
                "nama_material"     : item.nama_material,
                "batch_code"        : item.batch_code,
                "increments"        : item.increments,
                "size"              : item.size,
                "sample_weight"     : item.sample_weight,
                "sample_number"     : item.sample_number,
                "remark"            : item.remark,
                "primer_raw"        : item.primer_raw,
                "sampling_deskripsi": item.sampling_deskripsi,
                "no_sample"         : item.no_sample,
                "created_at"        : item.created_at.strftime('%Y-%m-%d %H:%M:%S')
                            
                
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
def create_sample_sale(request):
    allowed_groups = ['superadmin','data-control','admin-mgoqa']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )
    
    if request.method == 'POST':
        try:
            # Aturan validasi
            rules = {
                'tgl_sample[]'    : ['required'],
                'shift[]'         : ['required'],
                'id_type_sample[]': ['required'],
                'id_method[]'     : ['required'],
                'id_material[]'   : ['required'],
                'sample_number[]' : ['required', 'min_length:9', 'max_length:10', 'regex:^[a-zA-Z0-9]*$']
            }

            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'tgl_sample[].required'       : 'Tanggal sample harus diisi.',
                'shift[].required'            : 'Shift harus diisi.',
                'id_type_sample[].required'   : 'Tipe sample harus diisi.',
                'id_method[].required'        : 'Metode sample harus diisi.',
                'id_material[].required'      : 'Material harus diisi.',
                'sample_number[].required'    : 'SampleID harus diisi.',
                'sample_number[].min_length'  : 'SampleID minimal 9 karakter.',
                'sample_number[].max_length'  : 'SampleID maksimal 10 karakter.',
                'sample_number[].regex'       : 'SampleID hanya boleh terdiri dari huruf dan angka.'
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

            # Cek keunikan sample_number
            sample_numbers = request.POST.getlist('sample_number[]')
            for sample_number in sample_numbers:
                if SampleProductions.objects.filter(sample_number=sample_number).exists():
                    return JsonResponse({'error': f'SampleID {sample_number} already exists.'}, status=400)
                
           
            # Gunakan transaksi database untuk memastikan integritas data
            with transaction.atomic():
                # Dapatkan data dari request
                tgl_sample          = request.POST.getlist('tgl_sample[]')
                shift               = request.POST.getlist('shift[]')
                id_type_sample      = request.POST.getlist('id_type_sample[]')
                id_method           = request.POST.getlist('id_method[]')
                id_material         = request.POST.getlist('id_material[]')
                sample_number       = request.POST.getlist('sample_number[]')
                dischargeArea       = request.POST.getlist('discharge_area[]')
                product_code        = request.POST.getlist('product_code[]')
                sampling_deskripsi  = request.POST.getlist('sampling_deskripsi[]')
                batch_code          = request.POST.getlist('batch_code[]')
                increments          = request.POST.getlist('increments[]')
                sample_weight       = request.POST.getlist('sample_weight[]')
                primer_raw          = request.POST.getlist('primer_raw[]')
                method              = request.POST.getlist('method[]')
                type                = request.POST.getlist('type[]')
                productCode         = request.POST.getlist('codeProduct[]')
                no_sample           = request.POST.get('no_sample')
                
                # Loop untuk menyimpan setiap data sample
                for idx in range(len(tgl_sample)):
                    # Gabungkan nilai-nilai kolom menjadi kode batch
                    combinedKodeBatch = type[idx] + id_material[idx] + (method[idx] if method else '')  + productCode[idx] + batch_code[idx]
                    pulpKodeBatch     = type[idx] + (method[idx] if method else '')  + productCode[idx] + batch_code[idx]

                    combinedKodeBatch = combinedKodeBatch.replace(" ", "")  # Menghapus spasi
                    pulpKodeBatch     = pulpKodeBatch.replace(" ", "")  # Menghapus spasi

                    # Definisikan tipe-tipe yang ingin cek
                    valid_types = ['HOS', 'ROS']

                    # Cek apakah kode batch sudah ada dalam database
                    if type[idx] in valid_types:
                        if SampleProductions.objects.filter(kode_batch=combinedKodeBatch).exists():
                            return JsonResponse({'message': f'{batch_code[idx]} : batch code already exists.'}, status=422)

                    # Simpan data sample baru
                    SampleProductions.objects.create(
                        tgl_sample          = tgl_sample[idx],
                        shift               = shift[idx],
                        id_type_sample      = int(id_type_sample[idx]) if id_type_sample and id_type_sample[idx].isdigit() else None,
                        id_method           = int(id_method[idx]) if id_method and id_method[idx].isdigit() else None,
                        id_material         = int(id_material[idx]) if id_material and id_material[idx].isdigit() else None,
                        sample_number       = sample_number[idx],
                        discharge_area      = dischargeArea[idx],
                        product_code        = product_code[idx],
                        sampling_deskripsi  = sampling_deskripsi[idx] if sampling_deskripsi else "",
                        batch_code          = batch_code[idx] if batch_code else "",
                        increments           = int(increments[idx]) if increments and increments[idx].isdigit() else 0,
                        sample_weight       = float(sample_weight[idx]) if sample_weight and sample_weight[idx].replace('.', '', 1).isdigit() else 0.0,
                        primer_raw          = primer_raw[idx]  if primer_raw and primer_raw[idx].replace('.', '', 1).isdigit() else 0.0,
                        gc_expect           = 'No',
                        type                = type[idx],
                        kode_batch          = combinedKodeBatch,
                        selling_pulp        = pulpKodeBatch,
                        no_sample           = no_sample, 
                        id_user             = request.user.id  # Sesuaikan dengan cara Anda mendapatkan user ID
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
def samples_sale_page(request):
    sample_entry = generate_sample_number()
    today = datetime.today()
    context = {
        'sample_entry': sample_entry,
        'day_date'    : today.strftime('%Y-%m-%d'),
    }
    return render(request, 'admin-mgoqa/production-samples/sample-entry-sale.html',context)