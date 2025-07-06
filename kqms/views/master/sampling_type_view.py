from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ...models.sample_type import SampleType
from ...models.sample_type_details import SampleTypeDetails
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError, transaction
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404
from ...forms.forms_samples_type import SampleTypeForm


@login_required
def sampleType_page(request):

    return render(request, 'master/list-sample-type.html')

class SampleType_List(View):

    def post(self, request):
        # Ambil semua data invoice yang valid
        sampleType = self._datatables(request)
        return JsonResponse(sampleType, safe=False)

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
        records_total = SampleType.objects.all().count()
        # Set records filtered
        records_filtered = records_total
        # Ambil semua yang valid
        data = SampleType.objects.all()

        if search:
            data = SampleType.objects.filter(
                Q(type_sample__icontains=search) |
                Q(keterangan__icontains=search)|
                Q(pile_id__icontains=search)
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
                "id"             : item.id,
                "type_sample"    : item.type_sample,
                "keterangan"     : item.keterangan,
                "status"         : item.status,
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
def get_sampleType(request, id):
    # allowed_groups = ['superadmin','admin-mgoqa']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'GET':
        try:
            sample_type = get_object_or_404(SampleType, id=id)
            details = SampleTypeDetails.objects.filter(id_type=sample_type.id)

            # Serialize data to JSON format
            data = {
                'id': sample_type .id,
                'type_sample': sample_type .type_sample,
                'keterangan': sample_type .keterangan,
                'status': sample_type .status,
                'details': list(details.values('id_method')),
            }

            return JsonResponse(data)
        except SampleType.DoesNotExist:
            return JsonResponse({'error': 'Data not found'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def insert_sampleType(request):
    # allowed_groups = ['superadmin','admin-mgoqa']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'POST':
        type_sample = request.POST.get('type_sample')
        keterangan = request.POST.get('keterangan')
        status = 1
        method_ids = request.POST.getlist('method_id[]')
        # print("request.POST.getlist('method_id'):", method_ids)
        # print("request.POST:", request.POST)

        try:
            with transaction.atomic():
                # Simpan tipe sampel ke dalam tabel sample_types
                new_data = SampleType.objects.create(
                    type_sample=type_sample,
                    keterangan=keterangan,
                    status=status
                )

               # Nilai-nilai manual
                # type_id = 1
                # method_ids = [2, 3, 4]
                # details = [SampleTypeDetails(id_type=new_data.id, id_method=method_id) for method_id in method_ids]
                # SampleTypeDetails.objects.bulk_create(details)
                details = []
                for method_id in method_ids:
                    details.append(SampleTypeDetails(id_type=new_data.id, id_method=method_id))

                SampleTypeDetails.objects.bulk_create(details)

                print("new_data.id:", new_data.id)
                print("method_ids:", method_ids)

                return JsonResponse({
                    'status': 'success',
                    'message': 'Data berhasil disimpan.',
                    'data': {
                        'id'         : new_data.id,
                        'type_sample': new_data.type_sample,
                        'keterangan' : new_data.keterangan,
                        'status'     : new_data.status,
                        'created_at' : new_data.created_at
                    }
                })
            
        except IntegrityError as e:
            # Check if the error is a duplicate entry error
            if str(e):
                return JsonResponse({'status': 'error', 'message': 'The data already exists'}, status=400)
            else:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Metode tidak diizinkan'}, status=405)

@login_required    
def update_sampleType(request, id):
    # allowed_groups = ['superadmin','admin-mgoqa']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    #     )

    if request.method == 'POST':
        try:
            job = get_object_or_404(SampleType, id=int(id))
            type_sample = request.POST.get('type_sample')
            keterangan = request.POST.get('keterangan')
            method_ids = request.POST.getlist('method_id[]')
            form_data = {
                'type_sample': type_sample,
                'keterangan' : keterangan,
                'status'     : 1,
            }
            form = SampleTypeForm(form_data, instance=job)
            if form.is_valid():
                form.save()
                # SampleTypeDetails.objects.filter(id_type=job).delete()
                SampleTypeDetails.objects.filter(id_type=job).delete()
                deleted_count, _ = SampleTypeDetails.objects.filter(id_type=job).delete()
                print("Deleted:", deleted_count)
                details = [
                        SampleTypeDetails(id_type=job, id_method=method_id)
                        for method_id in method_ids
                    ]
                SampleTypeDetails.objects.bulk_create(details)
                return JsonResponse({
                    'status': 'success',
                    'id': job.id,
                    'type_sample': job.type_sample,
                    'keterangan': job.keterangan,
                    'created_at': job.created_at,
                    'updated_at': job.updated_at
                })
            else:
                errors = {field: error[0] for field, error in form.errors.items()}
                return JsonResponse({'status': 'error', 'message': errors}, status=400)

        except IntegrityError as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': 'Unexpected error: ' + str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Metode tidak diizinkan'}, status=405)


@login_required    
def delete_sampleType(request):
    # allowed_groups = ['superadmin']
    # if not request.user.groups.filter(name__in=allowed_groups).exists():
    #     return JsonResponse(
    #         {'status': 'error', 'message': 'You do not have permission'}, 
    #         status=403
    # )
    if request.method == 'DELETE':
        job_id = request.GET.get('id')
        if job_id:
            try:
                # Lakukan penghapusan berdasarkan ID di sini
                sample_type = SampleType.objects.get(id=int(job_id))
                
                # Hapus entri terkait dari tabel detail
                SampleTypeDetails.objects.filter(id_type=sample_type.id).delete()
                
                # Hapus entri dari tabel utama
                sample_type.delete()

                return JsonResponse({'status': 'success'})
            except SampleType.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Data not found'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

