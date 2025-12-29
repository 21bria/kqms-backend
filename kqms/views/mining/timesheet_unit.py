from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.db.models import Sum
from datetime import datetime
from decimal import Decimal
from django.views.decorators.http import require_http_methods
from kqms.models import  MineUnits,HmUnit, HmUnitDetail


@login_required
def timesheet_page(request):
    today = datetime.today()
    context = {
        'day_date' : today.strftime('%Y-%m-%d'),
    }
    return render(request, 'admin-mine/list-timesheet.html', context)

@login_required
def ajax_hm_unit_by_date_shift(request):
    date   = request.GET.get('date')
    shift  = request.GET.get('shift')
    search = request.GET.get('search', '').strip()

    if not date or not shift:
        return JsonResponse({
            "success": False,
            "message": "Date and shift required"
        }, status=400)

    qs = (
        HmUnit.objects
        .select_related('unit')
        .filter(date=date, shift=shift)
    )

    # apply search jika tidak kosong
    if search:
        qs = qs.filter(unit__unit_code__icontains=search)

    data = []
    for hm in qs:
        total_min = hm.details.aggregate(total=Sum('duration_min'))['total'] or 0

        data.append({
            "hm_unit_id" : str(hm.id),
            "unit_code"  : hm.unit.unit_code,
            "hm_start"   : float(hm.hm_start),
            "hm_end"     : float(hm.hm_end),
            "total_hours": round(total_min / 60, 2),
            "status"     : hm.status,
        })

    return JsonResponse({
        "success" : True,
        "data"    : data
    })

@login_required
@require_POST
def append_all_fleet(request):
    date  = request.POST.get('date')
    shift = request.POST.get('shift')

    if not date or not shift:
        return JsonResponse({
            'success': False,
            'message': 'Date dan Shift wajib diisi'
        }, status=400)

    created = 0
    skipped = 0

    with transaction.atomic():
        units = MineUnits.objects.filter(status=1)  # atau filter active

        for unit in units:
            obj, is_created = HmUnit.objects.get_or_create(
                unit=unit,
                date=date,
                shift=shift,
                defaults={
                    'hm_start': 0,
                    'hm_end'  : 0,
                    'status'  : 'DRAFT'
                }
            )

            if is_created:
                created += 1
            else:
                skipped += 1

    return JsonResponse({
        'success': True,
        'created': created,
        'skipped': skipped,
        'message': f'{created} unit ditambahkan, {skipped} sudah ada'
    })

@login_required
def getIdHmUnit(request, id):
    allowed_groups = ['superadmin','admin-mgoqa','admin-mining','data-control','entry-vendors']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse({"success": False, "message": "You do not have permission"}, status=403)

    try:
        d = (
            HmUnit.objects
            .select_related("unit")
            .get(id=id)
        )

        data = {
            "id"        : str(d.id),
            "hm_start"  : float(d.hm_start or 0),
            "hm_end"    : float(d.hm_end or 0),
            "unit_id"   : d.unit.id,
            "unit_code" : d.unit.unit_code,
            "date"      : d.date.strftime("%Y-%m-%d"),
            "shift"     : d.shift,
            "status"    : d.status,
        }

        return JsonResponse({"success": True, "data": data})

    except HmUnit.DoesNotExist:
        return JsonResponse({"success": False, "message": "Data tidak ditemukan"}, status=404)

@login_required
@require_http_methods(["POST"])
def update_hm_unit(request, id):
    allowed_groups = ['superadmin','admin-mgoqa','admin-mining','data-control','entry-vendors']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
        )
    try:
        # Aturan validasi
        rules = {
            'hm_start': ['required'],
            'hm_end'  : ['required'],
        }

        # Pesan kesalahan validasi yang disesuaikan
        custom_messages = {
            'hm_start.required' : 'Start HM is required.',
            'hm_end.required'   : 'End HM is required.'
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

        hm_start = request.POST.get('hm_start')
        hm_end   = request.POST.get('hm_end')

        # Dapatkan data yang akan diupdate berdasarkan ID
        data = HmUnit.objects.get(id=id)

        # Lakukan update data dengan nilai baru
        data.hm_start = hm_start
        data.hm_end   = hm_end
        # Simpan perubahan ke dalam database
        data.save()

        # Kembalikan respons JSON sukses
        return JsonResponse({'success'  : True,'message' : 'Data berhasil diupdate.' })

    except HmUnitDetail.DoesNotExist:
        return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    except IntegrityError as e:
        return JsonResponse({'error': 'Terjadi kesalahan integritas database', 'message': str(e)}, status=400)

    except ValidationError as e:
        return JsonResponse({'error': 'Validasi gagal', 'message': str(e)}, status=400)

    except Exception as e:
        return JsonResponse({'error': 'Terjadi kesalahan', 'message': str(e)}, status=500)
    
@login_required
def ajax_hm_unit_detail(request, hm_unit_id):
    try:
        # status di HmUnit bukan FK → hapus dari select_related
        hm = (
            HmUnit.objects
            .select_related('unit')
            .get(id=hm_unit_id)
        )
    except HmUnit.DoesNotExist:
        return JsonResponse(
            {"success": False, "message": "HM unit not found"},
            status=404
        )

    # Ambil details + relasi
    # details_qs = (
    #     hm.details
    #     .select_related("status", "activity", "location")
    #     .all()
    # )
    details_qs = (
        hm.details
          .select_related("status", "activity", "location")
          .order_by("start_time")
    )

    # Hitung total durasi
    total_minutes = details_qs.aggregate(total=Sum("duration_min"))["total"] or 0

    # Build rows
    detail_rows = []
    for d in details_qs:
        detail_rows.append({
            "id": str(d.id),
            "start_time": d.start_time.strftime("%H:%M") if d.start_time else None,
            "end_time"  : d.end_time.strftime("%H:%M") if d.end_time else None,
            "duration"  : d.duration_min,
            "status"    : d.status.name if d.status else None,
            "activity"  : d.activity.name if d.activity else None,
            "location"  : d.location.name if d.location else None,
            "remark"    : d.remark,
        })


    return JsonResponse({
        "success": True,
        "hm_unit_id" : str(hm.id),
        "unit_id"    : str(hm.unit.id),
        "unit_code"  : hm.unit.unit_code,
        "hm_start"   : float(hm.hm_start or 0),
        "hm_end"     : float(hm.hm_end or 0),
        "total_hours": total_minutes,
        # status HmUnit kalau CharField akses langsung
        "status"     : hm.status,
        "details"    : detail_rows,
    })

@login_required
def ajax_hm_unit_kpi(request, hm_unit_id):
    try:
        hm = HmUnit.objects.get(id=hm_unit_id)
    except HmUnit.DoesNotExist:
        return JsonResponse({"success": False, "message": "HM unit not found"}, status=404)

    details = hm.details.select_related("status")

    STATUS_MAP = {
        "OPR": "OP",
        "STB": "ST",
        "PM":  "MT",
        "BD":  "BD",
        "SUPPORT": "ST",
        "WX": "ST",
        "SLP": "ST",
    }

    summary = {
        "OP": 0,
        "ST": 0,
        "MT": 0,
        "BD": 0,
    }

    for d in details:
        code = d.status.code
        group = STATUS_MAP.get(code)
        if group:
            summary[group] += d.duration_min or 0

    OP = summary["OP"]
    ST = summary["ST"]
    MT = summary["MT"]
    BD = summary["BD"]

    MR = MT + BD  # Maintenance + Breakdown

    TOTAL_TIME = 24 * 60  # 1 hari

    MA = (OP / (OP + MT + BD) * 100) if (OP + MT + BD) else 0
    PA = ((OP + ST) / TOTAL_TIME * 100) if TOTAL_TIME else 0
    UA = (OP / (OP + ST) * 100) if (OP + ST) else 0
    EU = (OP / TOTAL_TIME * 100) if TOTAL_TIME else 0

    return JsonResponse({
        "success": True,
        "kpi": {
            "working": OP,
            "standby": ST,
            "maintenance": MR,
            "pa": round(PA, 2),
            "ma": round(MA, 2),
            "ua": round(UA, 2),
            "eu": round(EU, 2),
        }
    })

@login_required
@csrf_exempt
def create_timesheet(request):
    allowed_groups = ['superadmin','admin-mgoqa','admin-mining','data-control','entry-vendors']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
        )
    if request.method == 'POST':
        try:
            unit_code = request.POST.get('unit_code')
            hm_start  = request.POST.get('hm_start')
            hm_end    = request.POST.get('hm_end')

            if not unit_code:
                return JsonResponse({'error': 'Unit Code harus diisi!'}, status=400)
             # Ambil HmUnit berdasarkan unit_code
            hm_unit = HmUnit.objects.filter(unit__unit_code=unit_code).first()
            if not hm_unit:
                return JsonResponse({'error': f'HmUnit dengan code {unit_code} tidak ditemukan!'}, status=400)

            # Update langsung tanpa membuat row baru
            hm_unit.hm_start = hm_start
            hm_unit.hm_end   = hm_end
            hm_unit.save(update_fields=['hm_start','hm_end'])


            # Aturan validasi
            rules = {
                'start_time[]' : ['required'],
                'end_time[]'   : ['required'],
                'status[]'     : ['required'],
                'activity[]'   : ['required'],
                'location[]'   : ['required'],
            }

            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'start_time[].required' : 'Start time is required.',
                'end_time[].required'   : 'End time is required.',  
                'status[].required'     : 'Status is required.',
                'activity[].required'   : 'Activity is required.',
                'location[].required'   : 'Location is required.',
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

                start_time_list = request.POST.getlist('start_time[]')
                end_time_list   = request.POST.getlist('end_time[]')
                duration_list   = request.POST.getlist('duration[]')
                status_list     = request.POST.getlist('status[]')
                activity_list   = request.POST.getlist('activity[]')
                location_list   = request.POST.getlist('location[]')


                for idx in range(len(start_time_list)):
                    HmUnitDetail.objects.create(
                        hm_unit      = hm_unit,
                        start_time   = start_time_list[idx],
                        end_time     = end_time_list[idx],
                        duration_min = Decimal(duration_list[idx]),  # convert ke Decimal
                        status_id    = status_list[idx],
                        activity_id  = activity_list[idx],
                        location_id  = location_list[idx],
                    )
            # Setelah menyimpan semua HmUnitDetail Kembalikan respons JSON sukses
            return JsonResponse({
                'success': True,
                'message': 'Data berhasil disimpan.',
                'hm_unit_id': str(hm_unit.id),  # <-- ini penting
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
def getIdDetailHm(request, id):
    allowed_groups = ['superadmin','admin-mgoqa','admin-mining','data-control','entry-vendors']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse({"success": False, "message": "You do not have permission"}, status=403)

    try:
        d = (
            HmUnitDetail.objects
            .select_related("hm_unit__unit", "status", "activity", "location")
            .get(id=id)
        )

        data = {
            "id": str(d.id),
            "hm_unit_id": str(d.hm_unit_id),

            "unit_id": d.hm_unit.unit.id,
            "unit_code": d.hm_unit.unit.unit_code,

            "start_time": d.start_time.strftime("%H:%M"),
            "end_time": d.end_time.strftime("%H:%M"),
            "duration": d.duration_min,

            # ForeignKey objects → send ID + display name
            "status_id": d.status.id,
            "status_name": d.status.name,

            "activity_id": d.activity.id,
            "activity_name": d.activity.name,

            "location_id": d.location.id,
            "location_name": d.location.name,

            "remark": d.remark or "",
        }

        return JsonResponse({"success": True, "data": data})

    except HmUnitDetail.DoesNotExist:
        return JsonResponse({"success": False, "message": "Data tidak ditemukan"}, status=404)

@login_required
@require_http_methods(["POST"])
def update_detail_hm(request, id):
    allowed_groups = ['superadmin','admin-mgoqa','admin-mining','data-control','entry-vendors']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
        )
    try:
        # Aturan validasi
        rules = {
            'start_time': ['required'],
            'end_time'  : ['required'],
            'status'     : ['required'],
            'activity'   : ['required'],
            'location'   : ['required'],
        }

        # Pesan kesalahan validasi yang disesuaikan
        custom_messages = {
            'start_time.required' : 'Start time is required.',
            'end_time.required'   : 'End time is required.',
            'status.required'     : 'Status is required.',
            'activity.required'   : 'Activity is required.',
            'location.required'   : 'Location is required.',
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

        start_time = request.POST.get('start_time')
        end_time   = request.POST.get('end_time')
        duration   = request.POST.get('duration')
        status     = request.POST.get('status')
        activity   = request.POST.get('activity')
        location   = request.POST.get('location')
        unit_id    = request.POST.get('unit_id')

        if not unit_id:
            return JsonResponse({'error': 'Unit ID harus diisi!'}, status=400)
        # Ambil HmUnit berdasarkan unit_id
        hm_unit = HmUnit.objects.filter(unit__id=unit_id).first()

        if not hm_unit:
            return JsonResponse({'error': f'HmUnit dengan code {unit_id} tidak ditemukan!'}, status=400)

        # Dapatkan data yang akan diupdate berdasarkan ID
        data = HmUnitDetail.objects.get(id=id)

        # Lakukan update data dengan nilai baru
        data.start_time = start_time
        data.end_time   = end_time
        data.duration   = duration
        data.status_id  = status
        data.activity_id= activity
        data.location_id= location
  
        # Simpan perubahan ke dalam database
        data.save()

        

        # Kembalikan respons JSON sukses
        return JsonResponse({'success'  : True,
                              'message' : 'Data berhasil diupdate.',
                              'hm_unit_id': str(hm_unit.id),  # <-- ini penting
                              })

    except HmUnitDetail.DoesNotExist:
        return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    except IntegrityError as e:
        return JsonResponse({'error': 'Terjadi kesalahan integritas database', 'message': str(e)}, status=400)

    except ValidationError as e:
        return JsonResponse({'error': 'Validasi gagal', 'message': str(e)}, status=400)

    except Exception as e:
        return JsonResponse({'error': 'Terjadi kesalahan', 'message': str(e)}, status=500)

@csrf_exempt
@login_required
def delete_hm_detail(request):
    allowed_groups = ['superadmin','data-control','admin-mining']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse({'status': 'error', 'message': 'You do not have permission'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

    job_id = request.POST.get('id')
    if not job_id:
        return JsonResponse({'status': 'error', 'message': 'No ID provided'}, status=400)

    from uuid import UUID
    try:
        job_uuid = UUID(job_id)
        detail = HmUnitDetail.objects.get(id=job_uuid)
        detail.delete()
        return JsonResponse({'status': 'deleted'})
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'Invalid UUID format'}, status=400)
    except HmUnitDetail.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Data not found'}, status=404)
