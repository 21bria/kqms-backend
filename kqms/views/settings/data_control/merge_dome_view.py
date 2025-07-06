from django.contrib.auth.decorators import login_required
from django.db import connections
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from ....models.merge_stock import domeMerge
from ....models.merge_stock_view import domeMergeView
from ....models.ore_productions import OreProductions
from ....models.source_model import SourceMinesDome
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.shortcuts import render
from django.views.generic import View
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from ....utils.utils import clean_string
from ....utils.utils import generate_dome_merger


@login_required
def dome_merge_page(request):
    dome_merger = generate_dome_merger()
    context = {
        'dome_merger': dome_merger,

    }
    return render(request, 'master/list-merge-dome.html',context)

class domeMergeList(View):
    def post(self, request):
            # Ambil semua data yang valid
            OreClass = self._datatables(request)
            return JsonResponse(OreClass, safe=False)

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
        records_total = domeMergeView.objects.all().count()
        # Set records filtered
        records_filtered = records_total
        # Ambil semua yang valid
        data = domeMergeView.objects.all()

        if search:
            data = data.filter(
                Q(dome_primary__icontains=search) |
                Q(dome_new__icontains=search) 
            )
            
            records_total = data.count()
            records_filtered = records_total

        # Atur sorting
        if order_dir == 'desc':
            order_by = f'-{data.model._meta.fields[order_column].name}'
        else:
            order_by = f'{data.model._meta.fields[order_column].name}'

        data = data.order_by(order_by)

        # Atur paginator
        paginator = Paginator(data, length)

        try:
            object_list = paginator.page(start // length + 1).object_list
        except PageNotAnInteger:
            object_list = paginator.page(1).object_list
        except EmptyPage:
            object_list = paginator.page(paginator.num_pages).object_list

        data = [
            {
                "id"            :item.id,
                "dome"          :item.dome_primary,
                "tonnage"       :item.tonnage_primary,
                "dome_new"      :item.dome_new,
                "tonnage_new"   :item.tonnage_second,
                "totals"        :item.sum_tonnage,
                "status"        :item.status,
                "ref_id"        :item.ref_id
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
def get_dome_merge(request, id):
    allowed_groups = ['superadmin','data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )
    if request.method == 'GET':
        try:
            item = domeMergeView.objects.get(id=id)
            data = {
                'id':item.id,
                'dome_primary'    :clean_string(item.dome_primary),
                'original_dome'   :item.original_dome,
                'tonnage_primary' :item.tonnage_primary,
                'dome_new'        :clean_string(item.dome_new),
                'dome_second'     :item.dome_second,
                'tonnage_second'  :item.tonnage_second,
                'sum_tonnage'     :item.sum_tonnage,
                'ref_id'          :clean_string(item.ref_id),
                'status'          :clean_string(item.status),
                'remarks'         :clean_string(item.remarks)
            }
            return JsonResponse(data)
        except domeMergeView.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def insert_dome_merge(request):
    # allowed_groups = ['superadmin','data-control']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'POST':
        try:
            # Aturan validasi
            rules = {
                'original_dome'    : ['required'],
                # 'stockpile_ori'    : ['required'],
                'dome_second'      : ['required'],
                # 'stockpile_second' : ['required']
            }

            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'original_dome.required'    : 'Dome Originial is required.',
                # 'stockpile_ori.required'    : 'Stockpile is required.',
                'dome_second.required'      : 'Dome New is required.',
                # 'stockpile_second.required' : 'Stockpile New is required.',
            }

            # Validasi request
            for field, field_rules in rules.items():
                for rule in field_rules:
                    if rule == 'required':
                        if not request.POST.get(field):
                            return JsonResponse({'error': custom_messages[f'{field}.required']}, status=400)

            # Dapatkan data dari request dengan default nilai
            original_dome    = request.POST.get('original_dome')
            # stockpile_ori    = request.POST.get('stockpile_ori')
            tonnage_primary  = request.POST.get('tonnage_primary')
            dome_second      = request.POST.get('dome_second')
            # stockpile_second = request.POST.get('stockpile_second')
            tonnage_second   = request.POST.get('tonnage_second')
            ref_id           = request.POST.get('ref_id')
            remarks          = request.POST.get('remarks')

            # Pastikan semua nilai yang diperlukan ada sebelum diubah
            if any(v is None for v in [original_dome,  tonnage_primary, dome_second, tonnage_second]):
                return JsonResponse({'error': 'Semua field harus diisi.'}, status=400)

            # Gunakan transaksi database untuk memastikan integritas data
            with transaction.atomic():

                # Simpan data baru
                domeMerge.objects.create(
                    original_dome    = int(original_dome),
                    tonnage_primary  = float(tonnage_primary),
                    dome_second      = int(dome_second),
                    tonnage_second   = float(tonnage_second),
                    status           = 'Merger',
                    ref_id           = ref_id,
                    remarks          = remarks,
                    id_user          = request.user.id  # Sesuaikan dengan cara Anda mendapatkan user ID
                )

                # Update OreProduction
                OreProductions.objects.filter(
                    id_pile = original_dome
                ).update(
                    id_pile          = dome_second,
                    pile_original    = original_dome,
                    dome_compositing = ref_id
                )

                # Update SourceMinesDome
                SourceMinesDome.objects.filter(id=original_dome).update(compositing='Yes')

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
def update_dome_merge(request, id):
    # allowed_groups = ['superadmin','data-control']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'POST':
        try:
            rules = {
                'dome_second'     : ['required'],
                'original_dome'   : ['required'],
            }
            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'dome_second.required'      : 'Dome New is required.',
                'original_dome.required'    : 'Dome Originial is required.',
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
    
            # Ambil data dari request
            dome_second      = int(request.POST['dome_second'])
            ref_id           = request.POST['ref_id']
            original_dome    = int(request.POST['original_dome'])
            remarks          = request.POST['remarks']

            if domeMerge.objects.filter(ref_id=ref_id,status='Restore').exists():
                return JsonResponse({'error': f'Data {ref_id} already exists.'}, status=400)

            # Dapatkan objek yang akan diupdate
            data = get_object_or_404(domeMerge, id=id)

            # Update data
            data.remarks = remarks
            data.status = 'Restore'
            data.save()

            # Update OreProductions
            OreProductions.objects.filter(
                    id_pile=dome_second
                    ,dome_compositing=ref_id
                ).update(
                    id_pile=original_dome
                )
            
            # Update SourceMinesDome
            SourceMinesDome.objects.filter(id=original_dome).update(compositing='No')

            return JsonResponse({'success': True, 'message': 'Data berhasil diupdate.'})

        except IntegrityError as e:
            return JsonResponse({'error': 'Terjadi kesalahan integritas database', 'message': str(e)}, status=400)
        except ValidationError as e:
            return JsonResponse({'error': 'Validasi gagal', 'message': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'Terjadi kesalahan', 'message': str(e)}, status=500)

    return JsonResponse({'error': 'Metode tidak diizinkan'}, status=405)

@login_required
def delete_dome_merge(request):
    # allowed_groups = ['superadmin','data-control']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'DELETE':
        job_id = request.GET.get('id')
        if job_id:
            # Lakukan penghapusan berdasarkan ID di sini
            data = domeMerge.objects.get(id=int(job_id))
            data.delete()
            return JsonResponse({'status': 'deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

