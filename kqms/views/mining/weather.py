from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ...models.mine_weather import Weather
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from ...utils.utils import clean_string
from datetime import datetime
from django.views.decorators.http import require_http_methods


@login_required
def weather_page(request):
    today = datetime.today()
    context = {
        'day_date' : today.strftime('%Y-%m-%d'),
    }
    return render(request, 'admin-mine/list-weather.html', context)

class dataWeather(View):
    def post(self, request):
        data_list = self._datatables(request)
        return JsonResponse(data_list, safe=False)

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
        data = Weather.objects.all()

        if search:
            data = data.filter(
                Q(shift__icontains=search) |
                Q(date__icontains=search)
            )
       

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
                "id"         : item.id,
                "date"       : item.date,
                "shift"      : item.shift,
                "start_time" : item.start_time,
                "end_time"   : item.end_time,
                "duration"   : item.duration,
                "remarks"    : item.remarks
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
def create_weather(request):
    allowed_groups = ['superadmin','admin-mgoqa','admin-mining','data-control','entry-vendors']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
        )
    if request.method == 'POST':
        try:
            # Aturan validasi
            rules = {
                'date[]'      : ['required'],
                'shift[]'     : ['required'],
                'category[]'  : ['required'],
                'start_time[]': ['required'],
                'end_time[]'  : ['required'],
            }

            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'date[].required'       : 'Date is required.',
                'shift[].required'      : 'Shift is required.',
                'category[].required'   : 'Category is required.',
                'start_time[].required' : 'Start Time is required.',
                'end_time[].required'   : 'End Time is required.',
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
                date_list       = request.POST.getlist('date[]')
                shift_list      = request.POST.getlist('shift[]')
                category_list   = request.POST.getlist('category[]')
                start_time_list = request.POST.getlist('start_time[]')
                end_time_list   = request.POST.getlist('end_time[]')
                duration_list   = request.POST.getlist('duration[]')
                # remark_list     = request.POST.getlist('remark[]')


                # Loop untuk menyimpan setiap data sample
                for idx in range(len(date_list)):
                    # Cek duplikat
                    exists = Weather.objects.filter(
                        date=date_list[idx],
                        shift=shift_list[idx],
                        category=category_list[idx],
                        start_time=start_time_list[idx],
                        end_time=end_time_list[idx],
                    ).exists()

                    if exists:
                        return JsonResponse(
                            {
                                'status': 'error',
                                'message': (
                                    f"❌ Data duplikat ditemukan pada baris {idx + 1}: "
                                    f"{date_list[idx]}, {shift_list[idx]}, "
                                    f"{category_list[idx]}, "
                                    f"{start_time_list[idx]} - {end_time_list[idx]}"
                                )
                            },
                            status=422
                        )
    
                    # Simpan data baru
                    Weather.objects.create(
                        date        = date_list[idx],
                        shift       = shift_list[idx],
                        category    = category_list[idx],
                        start_time  = start_time_list[idx],
                        end_time    = end_time_list[idx],
                        duration    = duration_list[idx],
                        # remark      =remark_list[idx],
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
def getIdWeather(request):
    allowed_groups = ['superadmin','admin-mgoqa','admin-mining','data-control','entry-vendors']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
        )
    if request.method == 'GET':
        try:
            get_id   = request.GET.get('id')
            items     = Weather.objects.get(id=get_id)
            data = {
                'id'        : items.id,
                'date'      : items.date,
                'shift'     : clean_string(items.shift),
                'category'  : clean_string(items.category),
                'start_time': items.start_time,
                'end_time'  : items.end_time,
                'duration'  : items.duration,
                'remark'    : items.remark
        
            }
            return JsonResponse(data)
        except Weather.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
@require_http_methods(["POST"])
def update_weather(request, id):
    allowed_groups = ['superadmin','admin-mgoqa','admin-mining','data-control','entry-vendors']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
        )
    try:
        # Aturan validasi
        rules = {
            'date'      : ['required'],
            'shift'     : ['required'],
            'category'  : ['required'],
            'start_time': ['required'],
            'end_time'  : ['required']
        }

        # Pesan kesalahan validasi yang disesuaikan
        custom_messages = {
            'date.required'       : 'Date is required.',
            'shift.required'      : 'Shift is required.',
            'category.required'   : 'Category is required.',
            'start_time.required' : 'Start time is required.',
            'end_time.required'   : 'End time is required.'
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

        date        = request.POST.get('date')
        shift       = request.POST.get('shift')
        category    = request.POST.get('category')
        start_time  = request.POST.get('start_time')
        end_time    = request.POST.get('end_time')
        duration    = request.POST.get('duration')
        remark      = request.POST.get('remark')

        # Validasi duplikat (exclude data yang sedang diupdate)
        exists = Weather.objects.exclude(id=id).filter(
            date=date,
            shift=shift,
            category=category,
            start_time=start_time,
            end_time=end_time,
        ).exists()

        if exists:
            return JsonResponse(
                {
                    'status': 'error',
                    'message': (
                        '❌ Data duplikat ditemukan dengan kombinasi: '
                        f'{date}, {shift}, {category}, '
                        f'{start_time} - {end_time}'
                    )
                },
                status=422
            )
        # Dapatkan data yang akan diupdate berdasarkan ID
        data = Weather.objects.get(id=id)

        # Lakukan update data dengan nilai baru
        data.date       = date
        data.shift      = shift
        data.category   = category
        data.start_time = start_time
        data.end_time   = end_time
        data.duration   = duration
        data.remark     = remark

        # Simpan perubahan ke dalam database
        data.save()

        # Kembalikan respons JSON sukses
        return JsonResponse({'success': True, 'message': 'Data berhasil diupdate.'})

    except Weather.DoesNotExist:
        return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    except IntegrityError as e:
        return JsonResponse({'error': 'Terjadi kesalahan integritas database', 'message': str(e)}, status=400)

    except ValidationError as e:
        return JsonResponse({'error': 'Validasi gagal', 'message': str(e)}, status=400)

    except Exception as e:
        return JsonResponse({'error': 'Terjadi kesalahan', 'message': str(e)}, status=500)

@login_required
def delete_weather(request):
    allowed_groups = ['superadmin','admin-mgoqa','admin-mining','data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
        )
    if request.method == 'DELETE':
        job_id = request.GET.get('id')
        if job_id:
            data = Weather.objects.get(id=int(job_id))
            data.delete()
            return JsonResponse({'status': 'deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

