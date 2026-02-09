from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ...models.mine_status_units import UnitLocation
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views import View

    
@login_required
def location_activity_page(request):
    return render(request, 'admin-mine/list-activity-location.html')

class viewUnitLocation(View):

    def post(self, request):
        return JsonResponse(self._datatables(request), safe=False)

    def _datatables(self, request):
        datatables = request.POST

        draw = int(datatables.get('draw', 1))
        start = int(datatables.get('start', 0))
        length = int(datatables.get('length', 10))
        search = datatables.get('search[value]', '')

        order_column = int(datatables.get('order[0][column]', 0))
        order_dir = datatables.get('order[0][dir]', 'asc')

        data = UnitLocation.objects.all()

        if search:
            data = data.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) 
            )
        columns = [
            'id',
            'code',
            'name'
        ]

        order_field = columns[order_column] if order_column < len(columns) else 'id'
        if order_dir == 'desc':
            order_field = f'-{order_field}'

        data = data.order_by(order_field)

 
        records_total = data.count()
        paginator = Paginator(data, length)

        try:
            page_data = paginator.page(start // length + 1)
        except:
            page_data = paginator.page(1)


        result = [
            {
                "id"        : item.id,
                "code"      : item.code,
                "name"      : item.name
            }
            for item in page_data
        ]

        return {
            "draw": draw,
            "recordsTotal": records_total,
            "recordsFiltered": records_total,
            "data": result,
        }

@login_required
def insert_activity_location(request):
    allowed_groups = ['superadmin', 'admin-mgoqa', 'data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'},
            status=403
        )

    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

    location  = request.POST.get('location', '').strip()

    if not location:
        return JsonResponse({'status': 'error', 'message': 'Location is required'}, status=400)

    # cek duplikat berdasarkan lokasi
    if UnitLocation.objects.filter(name__iexact=location).exists():
        return JsonResponse({'status': 'error', 'message': 'Location already exists'}, status=400)

    # buat code otomatis dari nama
    code = location.replace(" ", "_").upper()

    try:
        new = UnitLocation.objects.create(
            name=location,
            code=code
        )

        return JsonResponse({
            'status': 'success',
            'message': 'Data berhasil disimpan',
            'data': {
                'id': new.id,
                'code': new.code,
                'name': new.name,
                'status': getattr(new, 'status', None) and new.status.name
            }
        })

    except IntegrityError:
        return JsonResponse({
            'status': 'error',
            'message': 'Duplicate code detected'
        }, status=400)

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
    
@login_required
def get_id_activity_location(request):
    allowed_groups = ['superadmin','admin-mgoqa','admin-mining','data-control']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse({'status': 'error', 'message': 'No permission'}, status=403)

    if request.method != 'GET':
        return JsonResponse({'error': 'Invalid method'}, status=400)

    try:
        item = UnitLocation.objects.get(id=request.GET.get('id'))

        data = {
            'id': item.id,
            'code': item.code,
            'name': item.name
        }

        return JsonResponse(data)

    except UnitLocation.DoesNotExist:
        return JsonResponse({'error': 'Data not found'}, status=404)

@login_required
@require_http_methods(["POST"])
def update_activity_location(request, id):
    allowed_groups = ['superadmin','admin-mgoqa','admin-mining','data-control','entry-vendors']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
        )
    try:
        # Aturan validasi
        rules = {
            'location'  : ['required']
        }

        # Pesan kesalahan validasi yang disesuaikan
        custom_messages = {
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

        location = request.POST.get('location')

        # Validasi duplikat (exclude data yang sedang diupdate)
        exists = UnitLocation.objects.exclude(id=id).filter(name=location).exists()

        if exists:
            return JsonResponse(
                {
                    'status': 'error',
                    'message': (
                        'Data already exists : 'f'{location}'
                    )
                },
                status=422
            )
        # Dapatkan data yang akan diupdate berdasarkan ID
        data = UnitLocation.objects.get(id=id)

        # buat code otomatis dari nama
        code = location.replace(" ", "_").upper()

        # Lakukan update data dengan nilai baru
        data.code       = code  
        data.name       = location

        # Simpan perubahan ke dalam database
        data.save()

        # Kembalikan respons JSON sukses
        return JsonResponse({'success': True, 'message': 'Data berhasil diupdate.'})

    except UnitLocation.DoesNotExist:
        return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    except IntegrityError as e:
        return JsonResponse({'error': 'Terjadi kesalahan integritas database', 'message': str(e)}, status=400)

    except ValidationError as e:
        return JsonResponse({'error': 'Validasi gagal', 'message': str(e)}, status=400)

    except Exception as e:
        return JsonResponse({'error': 'Terjadi kesalahan', 'message': str(e)}, status=500)


@login_required
@csrf_exempt
def delete_activity_location(request):
    allowed_groups = ['superadmin','data-control','admin-mining','admin-mgoqa']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
        )

    if request.method == 'DELETE':
        job_id = request.GET.get('id')
        if job_id:
            data = UnitLocation.objects.get(id=int(job_id))
            data.delete()
            return JsonResponse({'status': 'deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})