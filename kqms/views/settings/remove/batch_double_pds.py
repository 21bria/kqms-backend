from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.db.models import Count
import uuid
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from kqms.models.samples_data_view import SamplesView
from kqms.models.sample_production import SampleProductions

class batchSamplesDoubleList(View):
    def post(self, request):
        data_view = self._datatables(request)
        return JsonResponse(data_view, safe=False)


    def _datatables(self, request):
        datatables = request.POST
        draw = int(datatables.get('draw', 1))
        start = int(datatables.get('start', 0))
        length = int(datatables.get('length', 10))
        search = datatables.get('search[value]', '')
        order_column = int(datatables.get('order[0][column]', 0))
        order_dir = datatables.get('order[0][dir]', 'asc')

        columns = [
            'id',
            'tgl_sample',
            'type_sample',
            'nama_material',
            'sampling_area',
            'sampling_point',
            'batch_code',
            'kode_batch',
            'increments',
            'sample_number',
            'remark',
            'created_at',
        ]

        # sorting
        if order_column >= len(columns):
            order_by = 'created_at'
        else:
            order_by = columns[order_column]

        if order_dir == 'desc':
            order_by = '-' + order_by

        # ==========================================
        # DETEKSI DUPLIKAT BERDASARKAN KODE_BATCH
        # ==========================================
        duplicate_batches = (
            SamplesView.objects
            .filter(type_sample='PDS')
            .values('kode_batch')
            .annotate(total=Count('kode_batch'))
            .filter(total__gt=1)
            .values_list('kode_batch', flat=True)
        )

        # ambil semua record yang termasuk batch duplikat dan type PDS
        data = SamplesView.objects.filter(kode_batch__in=duplicate_batches, type_sample='PDS')

        # search
        if search:
            data = data.filter(
                Q(sampling_area__icontains=search) |
                Q(sampling_point__icontains=search) |
                Q(sample_number__icontains=search) |
                Q(remark__icontains=search) |
                Q(kode_batch__icontains=search)
            )

        # total records (hanya duplikat dan type PDS)
        records_total = SamplesView.objects.filter(kode_batch__in=duplicate_batches, type_sample='PDS').count()
        records_filtered = data.count()

        # ordering
        data = data.order_by(order_by)

        # pagination
        paginator = Paginator(data, length)
        try:
            object_list = paginator.page(start // length + 1).object_list
        except PageNotAnInteger:
            object_list = paginator.page(1).object_list
        except EmptyPage:
            object_list = paginator.page(paginator.num_pages).object_list

        # result
        result = [
            {
                "id"            : item.id,
                "tgl_sample"    : item.tgl_sample,
                "type_sample"   : item.type_sample,
                "nama_material" : item.nama_material,
                "sampling_area" : item.sampling_area,
                "sampling_point": item.sampling_point,
                "batch_code"    : item.batch_code,
                "kode_batch"    : item.kode_batch,
                "increments"    : item.increments,
                "sample_number" : item.sample_number,
                "remark"        : item.remark,
                "created_at"    : item.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                "is_duplicate"  : item.kode_batch in duplicate_batches,
            }
            for item in object_list
        ]

        return {
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': result,
        }


@csrf_exempt
def update_double_batch(request):
    allowed_groups = ['superadmin','data-control','admin-mgoqa']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse({'status': 'error', 'message': 'You do not have permission'}, status=403)

    sample_uuid = request.GET.get('id')
    if not sample_uuid:
        return JsonResponse({'status': 'error', 'message': 'UUID not provided'}, status=400)

    try:
        sample_obj = SampleProductions.objects.get(id=uuid.UUID(sample_uuid))

        # Update batch_code, kode_batch, dan remark
        if not sample_obj.batch_code.endswith('*Double'):
            sample_obj.batch_code = f"{sample_obj.batch_code}*Double"

        if not sample_obj.kode_batch.endswith('*Double'):
            sample_obj.kode_batch = f"{sample_obj.kode_batch}*Double"

        if sample_obj.remark:
            if '*Double' not in sample_obj.remark:
                sample_obj.remark = f"{sample_obj.remark} *Double"
        else:
            sample_obj.remark = '*Double'

        sample_obj.save()
        return JsonResponse({'status': 'success', 'message': 'Batch, kode_batch, and remark updated'})

    except SampleProductions.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Sample not found'}, status=404)
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'Invalid UUID'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

