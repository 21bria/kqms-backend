from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.shortcuts import render, redirect, get_object_or_404
from ...forms.forms_user import CustomGroupForm
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse


@login_required
def group_page(request):
    allowed_groups = ['superadmin']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        # Jika tidak memiliki izin, arahkan ke halaman error
        context = {
            'error_message': 'You do not have permission to access this page.',
        }
        return render(request, '403.html', context, status=403)

    return render(request, 'users/list-group.html')

class group_List(View):
    def post(self, request):
        # Ambil semua data invoice yang valid
        groups = self._datatables(request)
        return JsonResponse(groups, safe=False)

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
        records_total = Group.objects.all().count()
        # Set records filtered
        records_filtered = records_total
        # Ambil semua yang valid
        data = Group.objects.all()

        if search:
            data = Group.objects.filter(
                Q(name__icontains=search) 
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
                "id": item.id,
                "name": item.name
            } for item in object_list
        ]

        return {
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        }

@login_required
def group_create(request, pk=None):
    allowed_groups = ['superadmin']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )
    # If pk is provided, we are editing an existing group
    if pk:
        group = get_object_or_404(Group, pk=pk)
        form = CustomGroupForm(request.POST or None, instance=group)
    else:
        form = CustomGroupForm(request.POST or None)

    # Check if the form is valid
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('group-page')  # Redirect to the group list page after saving

    # Render the form template
    return render(request, 'users/group_form.html', {'form': form, 'is_edit': bool(pk)})

@login_required
def group_edit(request, pk):
    allowed_groups = ['superadmin']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        form = CustomGroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            return redirect('group-page')  # Redirect ke 'group-page' setelah berhasil menyimpan
    else:
        form = CustomGroupForm(instance=group)
    return render(request, 'users/group_form.html', {'form': form})

@login_required
def delete_group(request):
    allowed_groups = ['superadmin']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'You do not have permission'}, 
            status=403
    )
    if request.method == 'DELETE':
        job_id = request.GET.get('id')
        if job_id:
            # Lakukan penghapusan berdasarkan ID di sini
            data = Group.objects.get(id=int(job_id))
            data.delete()
            return JsonResponse({'status': 'deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No ID provided'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

