from django.urls import path
from ..views.report.services.generate_excel import *
from ..views.report.services.export_excel import *
from ..views.report.services.generate_excel_coa import *

urlpatterns = [
    # Task list
    path('generate/summary/', excel_unified_summary, name='excel_unified_summary'),
    path('export/data/', export_module_excel, name='export_module_excel'),
    path('export/data/coa/', excel_unified_coa, name='excel_unified_coa'),
    
]

