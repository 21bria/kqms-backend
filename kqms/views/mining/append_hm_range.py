import json
from django.shortcuts import render
from datetime import datetime, timedelta, date as dt_date
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from kqms.models import MineUnits, HmUnit

@login_required
def append_hm_range_page(request):
    today = datetime.today()
    context = {
        'day_date' : today.strftime('%Y-%m-%d'),
    }
    return render(request, 'admin-mine/append-range-hm.html', context)


class appendRangeHMView(View):
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
        data = HmUnit.objects.all()

        if search:
            data = data.filter(
                Q(shift__icontains=search)
            )
       
        # Filter berdasarkan parameter dari request
        date_start = request.POST.get('date_start')
        date_end   = request.POST.get('date_end')
 
        if date_start and date_end:
            data = data.filter(date__range=[date_start, date_end])


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
                "id"         : item.id,
                "date"       : item.date,
                "shift"      : item.shift,
                "hm_start"   : item.hm_start,
                "hm_end"     : item.hm_end,
                "unit_id"    : item.unit_id,
                "created_at" : item.created_at,
                
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
@require_POST
def append_hm_range(request):
    data = json.loads(request.body.decode())
    date_start = data.get('date_start')
    date_end   = data.get('date_end')

    if not date_start or not date_end:
        return JsonResponse({
            'success': False,
            'message': 'Tanggal wajib diisi'
        }, status=400)

    try:
        date_start = datetime.strptime(date_start, "%Y-%m-%d").date()
        date_end   = datetime.strptime(date_end, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({
            'success': False,
            'message': 'Format tanggal tidak valid'
        }, status=400)

    if date_start > date_end:
        return JsonResponse({
            'success': False,
            'message': 'Tanggal awal tidak boleh lebih besar'
        }, status=400)

    if date_end > dt_date.today():
        return JsonResponse({
            'success': False,
            'message': 'Tanggal tidak boleh lebih besar dari hari ini'
        }, status=400)

    SHIFTS = ['Day', 'Night']

    units = MineUnits.objects.filter(status=1)
    created = 0
    skipped = 0

    with transaction.atomic():
        current = date_start
        while current <= date_end:
            for shift in SHIFTS:
                for unit in units:
                    _, is_created = HmUnit.objects.get_or_create(
                        unit=unit,
                        date=current,
                        shift=shift,
                        defaults={
                            'hm_start': 0,
                            'hm_end': 0,
                            'status': 'DRAFT'
                        }
                    )
                    if is_created:
                        created += 1
                    else:
                        skipped += 1

            current += timedelta(days=1)

    return JsonResponse({
        'success': True,
        'created': created,
        'skipped': skipped,
        'message': f'{created} data dibuat, {skipped} dilewati'
    })

# def append_hm_range(request):
@login_required
@csrf_exempt
def delete_bulk_hm_range(request):
    allowed_groups = ['superadmin','admin-mining']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
        )

    if request.method == 'DELETE':
        try:
            body = json.loads(request.body)
            start_date = body.get('date_start')
            end_date   = body.get('date_end')

            if not start_date or not end_date:
                return JsonResponse(
                    {'status': 'error', 'message': 'Start and End date required'},
                    status=400
                )

            # pastikan format tanggal sesuai
            try:
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_date   = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Invalid date format'}, status=400)

            # filter data di rentang tanggal
            data = HmUnit.objects.filter(date__range=[start_date, end_date])

            if data.exists():
                deleted_count = data.count()
                data.delete()
                return JsonResponse({
                    'status': 'deleted',
                    'message': f'{deleted_count} records between {start_date} - {end_date} deleted'
                })
            else:
                return JsonResponse({'status': 'error', 'message': 'No records found in this range'}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
