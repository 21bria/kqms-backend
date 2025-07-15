from django.urls import path
# Ore Production Mine Geology
from ..views.geology.ore.ore_create_view import *
from ..views.geology.ore.ore_productions_view import *
from ..views.geology.ore.ore_details_view import *
from ..views.geology.ore.ore_batch_status_view import *

from ..views.geology.samples.samples_details_view import *
from ..views.geology.samples.samples_create_view import *
# from ..views.geology.samples.samples_create_sale import *
# from ..views.geology.samples.samples_pending_view import*
from ..views.geology.samples.samples_relation_view import*

# Waybill
from ..views.geology.waybills.waybill_view import *
from ..views.geology.waybills.waybill_create_view import *
from ..views.geology.waybills.assay_mral_release_over import *
from ..views.geology.waybills.assay_roa_release_over import *

# Assay 
from ..views.geology.assay.assay_mral_view import *
from ..views.geology.assay.assay_roa_view import *

urlpatterns = [
    
    # Table Ore Production & CRUD
    path('ore-productions/', ore_production_page, name='ore-productions-page'), 
    path('ore-productions-list/', OreProduction.as_view(), name='ore-productions-list'),
    path('ore-totals/', total_ore, name='ore-totals'),
    path('details-mral-totals/', total_details_mral, name='details-mral-totals'),
    path('details-roa-totals/', total_details_roa, name='details-roa-totals'),
    path('export-ore-data/',export_ore_data, name='export-ore-data'),

    path('ore-productions/get-id/<uuid:id>/', getIdOre, name='get-id-ore'), 
    path('ore-productions/delete/', delete_ore, name='delete-data-ore'),
    path('ore-details/', ore_details_page, name='ore-details-page'), 
    path('ore-details/list/', OreDetailsView.as_view(), name='ore-details-list'),
    path('export-ore/mral/',export_detail_mral, name='export-ore-mral'),
    path('export-ore/roa/',export_detail_roa, name='export-ore-roa'),

    path('ore-entry/', ore_entry_page, name='ore-entry-page'), 
    path('ore-entry/list/', orePdsCreate.as_view(), name='ore-entry-list'),
    path('ore/create/', create_ore, name='create-ore'),
    # path('ore/update/<int:id>/', update_ore, name='ore-samples'),
    path('ore/update/<uuid:id>/', update_ore, name='ore-samples'),
    path('ore-productions/delete/temp', delete_ore_temp, name='delete-data-ore-temp'),

    # Batch status incomlete ore PDS
    path('ore-pds/batch/', ore_batch_status_page, name='ore-batch-page'), 
    path('ore-pds/batch-list/', OrePdsBatch.as_view(), name='ore-pds-batch-list'),
    path('ore-pds-totals/', total_ore_batch, name='ore-pds-totals'),
    path('lim-batch-totals/', total_lim_batch, name='lim-batch-totals'),
    path('sap-batch-totals/', total_sap_batch, name='sap-batch-totals'),
    path('ore-pds/update-batch-status/', update_batch_status, name='update-batch-status'),
    path('ore-pds/update-batch-multi/', update_batch_multi, name='update-batch-multi'),


    # Table Samples Production & Sale
    path('samples-productions/', samples_data_page, name='samples-productions-page'), 
    path('samples-productions-list/', SamplesDetails.as_view(), name='samples-productions-list'),
    path('sample-productions/get-id/<uuid:id>/', getIdSample, name='get-id-sample'), 
    path('sample-productions/delete/', deleteSample, name='delete-sample-productions'),
    path('sample-productions/delete/create/', deleteSampleCreate, name='delete-sample-create'),
    path('export-samples-data/',export_samples_data, name='export-samples-data'),
    path('samples-entry/', samples_entry_page, name='samples-entry-page'), 
    path('samples-entry/list/', SamplesCreate.as_view(), name='samples-entry-list'),
    path('sample/create/', create_sample, name='create-samples'),
    path('sample/update/<uuid:id>/', update_sample, name='update-samples'),
    path('method/id-get/', get_methodSample, name='get-method-id'),

    #Sample relation pds - na
    path('samples-relation/', samples_relation_page, name='samples-relation-page'), 
    path('samples-relation/list/', samplesRelation.as_view(), name='samples-relation-list'),
    path('export-samples-relation/',export_samples_relation, name='export-samples-relation'),


      # Table Waybills
    path('waybill-list-page/', waybill_page, name='waybill-list-page'), 
    path('waybill-list/', Waybill_data.as_view(), name='waybill-list'), 
    path('export-waybill-data/',export_data_waybill, name='export-waybill-data'),
    path('waybill/get-id/<uuid:id>/', getIdWaybill, name='get-id-waybill'), 
    path('waybill/delete/', delete_waybill, name='delete-data-waybill'),
    path('waybill/update/<uuid:id>/', update_waybill, name='update-waybill'),

    path('generate-number/<str:team>/', get_waybill_number, name='generate_waybill_number'),
    path('waybill-create/', waybill_entry_page, name='waybill-create-page'), 
    path('waybill/list-temporary', waybillsListTemporary.as_view(), name='waybill-list-temporary'), 
    path('waybill/add-item', addItem, name='waybill-add-item'), 
    path('waybill/add-multi', add_multi, name='waybill-add-multi'), 
    path('waybill/insert', insert_waybill, name='insert-waybill'), 
    path('waybill/update-status', update_waybill_status, name='update-status'), 
    path('waybill/delete-temporary', deleteTmpWaybill, name='delete-temporary'), 

    # Over release Assay
    path('waybill/page/over-mral', mral_over_page, name='over-mral-page'), 
    path('waybill/over-mral', mralOverData.as_view(), name='list-release-mral'), 
    path('waybill/page/over-roa', roa_over_page, name='over-roa-page'), 
    path('waybill/over-roa', roaOverData.as_view(), name='list-release-roa'), 

    # Table Assay 
    path('assay-mral/', assay_mral_page, name='assay-mral-page'), 
    path('assay-mral-list/', Assay_Mral.as_view(), name='assay-mral-list'),
    path('export-assay-mral/',export_data_mral, name='export-assay-mral'),

    path('assay-roa/', assay_roa_page, name='assay-roa-page'), 
    path('assay-roa-list/', Assay_Roa.as_view(), name='assay-roa-list'),
    path('export-assay-roa/',export_data_roa, name='export-assay-roa'),


]