from django.urls import path


# Laboratory
from ..views.laboratory.laboratory_create import *
from ..views.laboratory.laboratory_view import *


urlpatterns = [
    path('lab/get-number/', get_lab_number, name='get_lab_number'),  # <-- AJAX endpoint
    path('laboratory-create/', laboratory_entry_page, name='laboratory-create-page'), 
    path('laboratory/list-temporary', laboratoryListTemporary.as_view(), name='laboratory-list-temporary'), 
    path('laboratory/insert', insert_lab_prep, name='insert-samples-prep'), 
    path('laboratory/get-id/<uuid:id>/', get_lab_prep, name='get-id-laboratory'), 
    path('delete/', delete_lab_prep, name='delete-data-lab-prep'),
    path('update/<uuid:id>/', update_lab_prep, name='update-lab-prep'),
    path('update-value/<uuid:id>/', update_prep_value, name='update-prep-value'),
    # 
    path('page-prep/', lab_prep_page, name='laboratory-list-page'), 
    path('list-data', lab_prep_data.as_view(), name='laboratory-list-prep'), 

]