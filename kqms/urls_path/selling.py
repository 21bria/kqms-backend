from django.urls import path
from ..views.geology.samples.samples_create_sale import *
from ..views.selling.selling_details import *


urlpatterns = [
    # Samples Selling
    path('samples-entry/', samples_sale_page, name='samples-sale-entry-page'), 
    path('samples-entry/list/', viewEntrySale.as_view(), name='samples-sale-entry-list'),
    path('sample/create/', create_sample_sale, name='create-samples-sale'),
    # Data Selling
    path('ore-selling-totals/', total_selling, name='ore-selling-totals'),
    path('barge/page/', sale_details_page, name='selling-barge-page'), 
    
    path('barge/list/', SellingDetails.as_view(), name='selling-barge-list'),
    path('export/daily/', export_sale_data, name='export-selling-data'), 


]