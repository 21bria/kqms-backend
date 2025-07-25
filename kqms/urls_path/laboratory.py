from django.urls import path


# Laboratory
from ..views.laboratory.laboratory_create import *


urlpatterns = [
    path('generate-number/<str:team>/', get_lab_number, name='generate_lab_number'),
    path('laboratory-create/', laboratory_entry_page, name='laboratory-create-page'), 
    path('laboratory/list-temporary', laboratoryListTemporary.as_view(), name='laboratory-list-temporary'), 
    # path('waybill/add-item', addItem, name='waybill-add-item'), 
    # path('waybill/add-multi', add_multi, name='waybill-add-multi'), 
    # path('waybill/insert', insert_waybill, name='insert-waybill'), 



]