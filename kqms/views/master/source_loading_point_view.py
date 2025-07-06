from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.http import HttpResponse
from ...models.source_model import SourceMinesLoading,SourceMines
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from ...utils.utils import clean_string
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

@login_required
def minesLoading_page(request):
    return render(request, 'master/list-source-loading-point.html')


class sourceMinesLoading_List(View):

    def post(self, request):
        # Ambil semua data invoice yang valid
        MinesLoading = self._datatables(request)
        return JsonResponse(MinesLoading, safe=False)

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
        records_total = SourceMinesLoading.objects.all().count()
        # Set records filtered
        records_filtered = records_total
        # Ambil semua yang valid
        # data = SourceMinesLoading.objects.all()
        # Ambil semua yang valid dengan select_related untuk join dengan SourceMines
        data = SourceMinesLoading.objects.select_related('id_sources').all()

        if search:
            data = SourceMinesLoading.objects.filter(
                Q(loading_point__icontains=search) |
                Q(remarks__icontains=search)|
                Q(category__icontains=search)
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
                "id"            : item.id,
                "loading_point" : item.loading_point,
                "remarks"       : item.remarks,
                "category"      : item.category,
                "sources_area"  : item.id_sources.sources_area if item.id_sources else None,  # Mengambil sources_area
                "status"        : item.status,
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
def get_minesLoading(request, id):
    # allowed_groups = ['superadmin', 'admin-mining','admin-mgoqa','data-control']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'GET':
        try:
            job = SourceMinesLoading.objects.get(id=id)
            
            # Jika job.id_sources ada, ambil sumber yang relevan
            sources_data = {
                'id': job.id_sources.id if job.id_sources else None,  # ID sumber
                'sources_area': job.id_sources.sources_area if job.id_sources else None  # Ambil kolom sources_area dari SourceMines
            } if job.id_sources else None  # Jika tidak ada id_sources, set None

            data = {
                'id'            : job.id,
                'loading_point' : clean_string(job.loading_point), 
                'remarks'       : clean_string(job.remarks),
                'category'      : clean_string(job.category),
                'sources'       : clean_string(sources_data),  # Masukkan data sumber
                'status'        : clean_string(job.status),
                'created_at'    : job.created_at
            }
            return JsonResponse(data)
        
        except SourceMinesLoading.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def insert_minesLoading(request):
    # allowed_groups = ['superadmin', 'admin-mining','admin-mgoqa','data-control']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'POST':

        try:
            # Ambil data dari request POST
            loading_point = request.POST.get('loading_point')
            remarks       = request.POST.get('remarks')
            sources       = request.POST.get('sources')  # Ini mengasumsikan 'sources' adalah ID dari SourceMines
            status        = 1

          # Aturan validasi
            rules = {
                'loading_point': ['required'],
                'sources'      : ['required']
            }

            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'loading_point.required': 'Loading point is required.',
                'sources.required'      : 'Source is required.'
            }

            # Validasi request
            for field, field_rules in rules.items():
                for rule in field_rules:
                    if rule == 'required':
                        if not request.POST.get(field):
                            return JsonResponse({'error': custom_messages[f'{field}.required']}, status=400)
                                                
            # Pastikan ID yang diberikan ada dan valid
            if sources:
                # Cari objek SourceMines berdasarkan ID
                source_instance = SourceMines.objects.get(id=sources)
            else:
                # Jika tidak ada sources, bisa set None atau tangani sesuai kebutuhan
                source_instance = None

            if SourceMinesLoading.objects.filter(loading_point=loading_point).exists():
                return JsonResponse({'error': f'Data {loading_point} already exists.'}, status=400)

            # Membuat objek baru SourceMinesLoading dengan instance SourceMines
            new_job = SourceMinesLoading.objects.create(
                loading_point = loading_point,
                remarks       = remarks,
                id_sources    = source_instance,  # Gunakan instance SourceMines
                status        = status
            )

            return JsonResponse({
                'status': 'success',
                'message': 'Data berhasil disimpan.',
                'data': {
                    'id'            : new_job.id,
                    'loading_point' : new_job.loading_point,
                    'remarks'       : new_job.remarks,
                    'sources'       : new_job.id_sources.id if new_job.id_sources else None,  # Kembalikan ID sumber
                    'status'        : new_job.status,
                    'created_at'    : new_job.created_at
                }
            })
        except IntegrityError as e:
            return JsonResponse({'error': 'Terjadi kesalahan integritas database', 'message': str(e)}, status=400)
        except ValidationError as e:
            return JsonResponse({'error': 'Validasi gagal', 'message': str(e)}, status=400)

        except Exception as e:
            return JsonResponse({'error': 'Terjadi kesalahan', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Metode HTTP tidak diizinkan'}, status=405)

@login_required
def update_minesLoading(request, id):
    # allowed_groups = ['superadmin', 'admin-mining','admin-mgoqa','data-control']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'POST':
        try:
            # Ambil data job yang ada berdasarkan id
            job = SourceMinesLoading.objects.get(id=id)

            # Aturan validasi
            rules = {
                'loading_point': ['required'],
                'sources'      : ['required']
            }

            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'loading_point.required': 'Loading point is required.',
                'sources.required'      : 'Source is required.'
            }

            # Validasi request
            for field, field_rules in rules.items():
                for rule in field_rules:
                    if rule == 'required':
                        if not request.POST.get(field):
                            return JsonResponse({'error': custom_messages[f'{field}.required']}, status=400)
                                                
            
            # Ambil data dari request POST
            job.loading_point = request.POST.get('loading_point')
            job.remarks       = request.POST.get('remarks')
            
            # Ambil id_sources dari POST dan temukan instance SourceMines yang sesuai
            sources_id = request.POST.get('sources')  # Ini mengasumsikan bahwa 'sources' adalah ID dari SourceMines
            if sources_id:
                job.id_sources = SourceMines.objects.get(id=sources_id)  # Ambil objek SourceMines dengan ID tersebut

            # exclude(id=job.id): Mengecualikan data dengan ID yang sedang di-update agar validasi tidak menganggap data tersebut sebagai duplikat.
            if SourceMinesLoading.objects.filter(loading_point=job.loading_point).exclude(id=job.id).exists():
                return JsonResponse({'error': f'Data {job.loading_point} already exists.'}, status=400)


            # Simpan perubahan
            job.save()

            # Kembalikan response JSON
            return JsonResponse({
                'id'            : job.id,
                'loading_point' : job.loading_point,
                'remarks'       : job.remarks,
                'sources'       : job.id_sources.id,  # Kembalikan ID sumber yang diperbarui
                'created_at'    : job.created_at,
                'updated_at'    : job.updated_at
            })
        
        except SourceMinesLoading.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
        
        except SourceMines.DoesNotExist:
            return JsonResponse({'error': 'SourceMines dengan ID yang diberikan tidak ditemukan'}, status=400)
        
        except IntegrityError as e:
            return JsonResponse({'error': 'Terjadi kesalahan integritas database', 'message': str(e)}, status=400)

        except ValidationError as e:
            return JsonResponse({'error': 'Validasi gagal', 'message': str(e)}, status=400)

        except Exception as e:
            return JsonResponse({'error': 'Terjadi kesalahan', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Metode HTTP tidak diizinkan'}, status=405)

@login_required
def delete_minesLoading(request):
    # allowed_groups = ['superadmin']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'DELETE':
        job_id = request.GET.get('id')
        if job_id:
            data = SourceMinesLoading.objects.get(id=int(job_id))
            data.delete()
            return JsonResponse({'status': 'deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@csrf_exempt
def export_loading_point(request):

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = 'Loading Point'

    # Write header row
    header = [
        'No', 
        'Name', 
        'Remarks', 
    ]

    for col_num, column_title in enumerate(header, 1):
        cell = worksheet.cell(row=1, column=col_num)
        cell.value = column_title
        cell.font = Font(bold=True)  # Mengatur teks menjadi bold

    # List kolom yang ingin diambil
    columns = [
       'loading_point', 
       'remarks'
    ]

    # Iterator ini mengambil data dalam beberapa bagian, sehingga hemat memori untuk kumpulan data besar.
    queryset = SourceMinesLoading.objects.all().values_list(*columns)

    # Membersihkan setiap nilai string dalam hasil queryset
    cleaned_data = [
        [clean_string(value) for value in row]  # Terapkan clean_string ke setiap nilai dalam baris
        for row in queryset
    ]
    
    for row_num, (row_count, row) in enumerate(enumerate(cleaned_data, 1), 1):
        worksheet.cell(row=row_num + 1, column=1, value=row_count)
        for col_num, cell_value in enumerate(row, 2):
            cell = worksheet.cell(row=row_num + 1, column=col_num)
            
            if isinstance(cell_value, str):  
                try:
                    cell_value = float(cell_value.replace(',', '').replace(' ', '').replace('.', '', 1))
                except ValueError:
                    pass  # Biarkan tetap string jika bukan angka

            cell.value = cell_value

    # Sesuaikan lebar kolom berdasarkan panjang teks di header
    for col_num, column_title in enumerate(header, 1):
        col_letter = get_column_letter(col_num)
        max_length = len(column_title)  # Panjang teks di header
        for row in worksheet.iter_rows(min_col=col_num, max_col=col_num):
            for cell in row:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
        adjusted_width = (max_length + 2)
        worksheet.column_dimensions[col_letter].width = adjusted_width

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="loading_point.xlsx"'
    workbook.save(response)

    return response
