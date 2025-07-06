from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import tempfile
import traceback
from importlib import import_module
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.views.generic import View
from django.db.models import Q
from kqms.models import taskImports,TaskList
import importlib  # Import importlib secara langsung
# def load_function_from_path(path):
#     try:
#         module_path, func_name = path.rsplit('.', 1)
#         module = import_module(module_path)
#         print(f"[DEBUG] Successfully imported module: {module_path}")
#         return getattr(module, func_name)
#     except Exception as e:
#         print(f"[ERROR] Failed to import {path}: {e}")
#         raise

def load_function_from_path(task_path):
    print(f"[DEBUG] Loading function from path: {task_path}")
    
    try:
        module_path, function_name = task_path.rsplit('.', 1)
        print(f"[DEBUG] Module path: {module_path}, Function: {function_name}")
        
        module = importlib.import_module(module_path)
        print(f"[DEBUG] Successfully imported module: {module_path}")
        
        task_func = getattr(module, function_name)
        print(f"[DEBUG] Task function: {task_func}")
        print(f"[DEBUG] Task function type: {type(task_func)}")
        
        # Periksa apakah ini adalah Celery task
        if hasattr(task_func, 'delay'):
            print(f"[DEBUG] Task has 'delay' method - OK")
        else:
            print(f"[DEBUG] WARNING: Task doesn't have 'delay' method")
            
        return task_func
        
    except Exception as e:
        print(f"[ERROR] Failed to load function: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise

@login_required
def imports_page(request):
    return render(request, 'task/template-import.html')

class TaskImportsList(View):
    def post(self, request):
        # Ambil semua data invoice yang valid
        material = self._datatables(request)
        return JsonResponse(material, safe=False)

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
        records_total = taskImports.objects.all().count()
        # Set records filtered
        records_filtered = records_total
        # Ambil semua yang valid
        data = taskImports.objects.all()
        

        if search:
            data = taskImports.objects.filter(
                Q(created_at__icontains=search) |
                Q(file_name__icontains=search)
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
                "id"                : item.id,
                "task_id"           : item.task_id,
                "successful_imports": item.successful_imports,
                "failed_imports"    : item.failed_imports,
                "duplicate_imports" : item.duplicate_imports,
                "duplicate_file_path" : item.duplicate_file_path,
                "errors"            : item.errors,
                "duplicates"        : item.duplicates,
                "file_name"         : item.file_name,
                "destination"       : item.destination,
                "created_at"        : item.created_at.strftime("%a, %d %b %Y %H:%M:%S")
            } for item in object_list
        ]

        return {
            'draw'           : draw,
            'recordsTotal'   : records_total,
            'recordsFiltered': records_filtered,
            'data'           : data
        }
    
@csrf_exempt
def upload_file(request):
    if request.method == 'POST':
        print("[DEBUG] Upload file triggered")

        file = request.FILES.get('file')
        import_type = request.POST.get('import_type')
        print(f"[DEBUG] Received import_type: {import_type}")

        if file and import_type:
            original_file_name = file.name
            print(f"[DEBUG] Received file: {original_file_name}")

            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
                file_path = temp_file.name

            print(f"[DEBUG] File temporarily saved to: {file_path}")

            try:
                task_entry = TaskList.objects.get(id=import_type, status=1)
                print(f"[DEBUG] Task entry found: {task_entry}")

                task_path = task_entry.task_path
                print(f"[DEBUG] Task path: {task_path}")

                task_func = load_function_from_path(task_path)
                task = task_func.delay(file_path, original_file_name)
                print(f"[DEBUG] Task submitted with ID: {task.id}")

                return JsonResponse({'message': 'Import started', 'task_id': task.id})

            except TaskList.DoesNotExist:
                print("[ERROR] Import type not found in TaskList DB")
                return JsonResponse({'message': 'Import type not found in DB'}, status=400)

            except Exception as e:
                print("[EXCEPTION] Unexpected error occurred:")
                print(traceback.format_exc())
                return JsonResponse({'message': f'Error: {str(e)}'}, status=500)

    print("[ERROR] Invalid request method")
    return JsonResponse({'message': 'Invalid request method'}, status=405)

# def upload_file(request):
    # if request.method == 'POST':
    #     file = request.FILES.get('file')
    #     column_mapping = json.loads(request.POST.get('column_mapping', '{}'))
    #     if file:
    #         # file_path = os.path.join(settings.MEDIA_ROOT, file.name)
    #         # file_path =os.path.join(settings.BASE_DIR, "sqms_apps/static/import", file.name)
    #         # with open(file_path, 'wb+') as destination:
    #         #     for chunk in file.chunks():
    #         #         destination.write(chunk)

    #         # Simpan file ke disk sementara
    #         with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
    #             for chunk in file.chunks():
    #                 temp_file.write(chunk)
    #             file_path = temp_file.name

    #         if column_mapping:
    #             result = import_mahasiswa.delay(file_path, column_mapping)
    #             return JsonResponse(result)
    #         else:
    #             df = pd.read_excel(file_path)
    #             columns_in_file = df.columns.tolist()
    #             return JsonResponse({'columns': columns_in_file})

    # return JsonResponse({'message': 'Invalid request method'}, status=405)