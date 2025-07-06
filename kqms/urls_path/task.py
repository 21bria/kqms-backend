from django.urls import path
from ..views.imports.task_list import *
from ..views.imports.template import *
from ..views.imports.import_views import *
from ..views.schedule_task import *

urlpatterns = [
    # Task list
    path('task/table/', task_list_page, name='task-table-page'),
    path('task-table/list/', task_List.as_view(), name='task-list-table'),
    path('task/table/add/', add_task, name='task-table-add'),
    path('task/table/<int:pk>/edit/', edit_task, name='task-table-edit'),
    path('task/table/delete/', delete_task, name='task-table-delete'),

    # tempalte format import
    path('format-excel/', format_downloads, name='format-excel'),
    # path('send-email/', send_test_email, name='send_test_email'),

    #Data Import Excel 
    path('import-excel-page/', imports_page, name='import-excel-page'),
    path('upload-file/', upload_file, name='upload-file'),
    path('task-import/list/', TaskImportsList.as_view(), name='task-list-imports'), 
    
    # Jadwal
    path("api/scheduled-tasks/", PeriodicTaskListView.as_view(), name="scheduled_tasks_list"),
    path("api/scheduled-tasks/add/",schedule_task, name="scheduled_tasks_add"),
    
]
    