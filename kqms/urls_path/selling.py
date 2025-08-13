from django.urls import path
from ..views.geology.samples.samples_create_sale import *
from ..views.selling.selling_details import *
from ..views.selling.selling_plan import *
from ..views.selling.selling_official import *
from ..views.selling.split_sample.selling_split_range import *
from ..views.selling.blending.source_inventoy import *
from ..views.selling.blending.target_blending import *
from ..views.selling.blending.create_data import *
from ..views.selling.entry.selling_data import *


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
    # Plan
    path('plan-page/', sale_plan_page, name='sale-plan-page'),
    path('plan/list/', sellingDataPlan.as_view(), name='selling-plan-list'),
    # CRUD
    path('plan/create/', create_plan_sale, name='create-plan-sale'),
    path('plan/get-id/<uuid:id>/', getIdPlanSale, name='get-id-sale-plan'), 
    path('plan/update/<uuid:id>/', update_sale_plan, name='update-sale-plan'),
    path('plan/delete/', delete_sale_plan, name='delete-sale-plan'),

    # Official
    path('official-page/', sale_official_page, name='sale-official-page'),
    path('official/list/', sellingDataOfficial.as_view(), name='sale-official-list'),
    path('official/create/', create_official_sale, name='create-official-sale'),
    path('official/get-id/<int:id>/', getIdOfficial, name='get-sale-official'),
    path('official/update/<int:id>/', update_official, name='update-sale-official'),
    path('official/delete/', delete_sale_official, name='delete-official-sale'),
    # Split  Selling
    path('split/sample/page/', splitSamplePage, name='sale-split-sample-page'),
    path('split/sample/list/', samplesSplit, name='sale-split-sample-list'),
    # Official COA
    path('split/coa/page/', splitOfficialPage, name='sale-split-coa-page'),
    path('split/coa/list/', splitOfficial, name='sale-split-coa-list'),

    # Blending
    path('blending/data/source/', get_data_source, name='blending-get-sorce'),
    path('blending/page/', blending_manual_page, name='blending-form-page'),
    path('blending/manual/calculate/', calculate_blending_auto, name='blending-manual-calculate'),
    path('blending/auto/calculate/', calculate_blending_auto_all, name='blending-auto-calculate'),
    
    # Create Simulasi
    path('blending/get-next-code/', get_next_blend_code, name='get-blend-code'),
    path('blending/create/', create_blending_sale, name='create-blending-sale'),

    # Create Quick
    path('entry/page/quick/', sale_entry_page, name='selling-entry-quick-page'),
    path('quick/list/', SellingTemp.as_view(), name='selling-quik-list'),
    path('form/page/quick/', form_entry_page, name='selling-form-quick-page'),
    path('quick/create/', create_quick_selling, name='create-quik-sale'),
    path('export/daily/quick/', export_sale_data_quick, name='export-selling-data-quick'), 
]