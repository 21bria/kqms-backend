from django.urls import path
from ..views.report.xlsxwriter.productions_xlsx import *
from ..views.imports.template import *
from ..views.imports.import_views import *
from ..views.schedule_task import *

urlpatterns = [
    # Task list
    path('ore-summary/', excel_ore_summary, name='excel_ore_summary'),
    
]
    