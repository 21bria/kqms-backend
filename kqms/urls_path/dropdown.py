from django.urls import path
# Ore Production Mine Geology
from ..views.geology.ore.ore_create_view import *
from ..views.geology.ore.ore_productions_view import *
from ..views.geology.ore.ore_details_view import *
from ..views.geology.ore.ore_batch_status_view import *
from ..views.settings.dropdown_view import *

urlpatterns = [
    
    # Get Dropdown dinamyc
    path('method_dropdown/', method_dropdown, name='method-dropdown'), 
    path('material_dropdown/', material_dropdown, name='material-dropdown'), 
    path('get-details-point/', get_details_point, name='get-details-point'), 
    path('get-details-source/', get_details_sources, name='get-details-source'), 
    path('get-details-truck/', get_details_truck, name='get-details-truck'), 
    path('get-year-ore/', get_year_ore, name='get-year-ore'), 
    path('get-year-sale/', get_year_sale, name='get-year-sale'), 
    path('get-year-sample/', get_year_sample, name='get-year-sample'), 
    path('get-sale-stockpile/', get_sale_stockpile, name='get-sale-stockpile'), 
    path('get-sale-dome/', get_sale_dome, name='get-sale-dome'), 
    path('get-sale-discharge/', get_sale_discharge, name='get-sale-discharge'), 
    path('get-sale-product/', get_sale_product, name='get-sale-product'), 
    path('get-materials-factors/', getMaterialsFactors, name='get-materials-factors'), 

    # For Insert & edit Ore
    path('block-id-dropdown/', dropdownBlockId, name='block-id-dropdown'), 
    path('material-id-dropdown/', dropdownMaterialId, name='material-id-dropdown'), 
    path('stockpile-id-dropdown/', dropdownStockpileId, name='stockpile-id-dropdown'), 
    path('dome-id-dropdown/', dropdownDomeId, name='dome-id-dropdown'), 
    path('mine-geos-dropdown/', dropdownMineGoes, name='mine-geos-dropdown'), 
    path('ore-class-dropdown/<int:id>/', dropdownOreClass, name='ore-class-dropdown'), 
    path('ore-class-get/', dropdownOreClassGet, name='ore-class-get'), 
    path('get-ore-classes/', get_ore_classes, name='get-ore-classes'),
    path('get-ore-factors/', get_truck_factors, name='get-ore-factors'),
    path('ore-ton/get-id/<str:id>/', getOreTonnage, name='get-ton-ore'),
   
    #  For Samples Production
    path('samples-material/',  get_sample_material, name='samples-material'), 
    path('samples-product/',  get_product_code, name='samples-product'), 
    path('samples-discharge/',  get_discharge, name='samples-discharge'), 
    path('samples-type/',  sample_type_dropdown, name='samples-type'), 
    path('samples-type/pds/',  sampleTypeId, name='samples-type-pds'), 
    path('samples-type/sale/',  sampleTypeSaleId, name='samples-type-sale'), 
    path('method/get-id/<int:id>/', method_detail, name='get-method-detail'),
    # path('method/id-get/', get_methodSample, name='get-method-id'),
    path('sample/get-material/', sampleMaterialId, name='get-sample-material'),
    path('sample/get-area/', sampleAreaId, name='get-sample-area'),
    path('sample/get-point/', samplePointId, name='get-sample-point'),
    path('sample/get-product/', codeProductId, name='get-sample-product'),
    path('sample/get-factory/', stockFactoryId, name='get-sample-factory'),
    path('sample/get-material-sale/', material_sale, name='get-material-sale'),
    path('sale/get-surveyor/', saleSurveyor, name='get-surveyor'),
    
    path('sample/get-crm/', get_sample_crm, name='get-crm'),
    path('sample/get-dome-pds-active/', get_dome_pds_active, name='get-dome-pds-active'),

    path('get-units-categories/', get_units_categories, name='get-units-categories'),
    path('get-units-vendor/', get_units_vendors, name='get-units-vendor'),
    path('get-dome-merge-dropdown/', get_merge_dome, name='get-dome-merge-dropdown'),
    path('get-stockpile-merge-dropdown/', get_merge_stockpile, name='get-stockpile-merge-dropdown'),

    # For Production Dropdown
    path('get-mine/source/', get_mine_sources, name='get-mine-source'),
    path('get-mine/block/', get_blockMine, name='get-block-mine'),
    path('get-mine/materials/', get_materials, name='get-mine-materials'),
    path('get-mine/loading-point/', get_mine_loading_points, name='get-mine-loading-point'),
    path('get-mine/dumping-point/', get_mine_dumping_points, name='get-mine-dumping-point'),
    path('get-mine/dome/', get_mine_dome, name='get-mine-dome'),
    path('get-mine/units/', get_mine_units, name='get-mine-units-entry'),
    path('get-mine/vendors/', get_mine_vendors, name='get-mine-vendors'),
    path('get-mine/plan-category/', get_category_mine, name='get-mine-plan-category'),
    path('get-mine/materials/all/', get_mineMaterials, name='get-materials-mine'),
    path('get-mine/geos/', get_mine_geos, name='get-mine-geos'),
    
    # Get All
    path('get-mine/category/', get_mine_category, name='get-mine-category'),
    path('get-mine/source/all', get_sources_mine, name='get-mine-source-all'),

    # Samples
    path('get-mine/sample/type/', get_sample_type, name='get-mine-sample-type'),
    path('get-mine/sample/type/sale/', get_sampleTypeSale, name='get-sale-sample-type'),
    path('get-mine/stock/factories/sale/', get_stockFactories, name='get-sale-stock-factories'),
    path('get-mine/code/product/sale/', get_codeProduct, name='get-sale-code-product'),

    # for task
    path('get-task-import/', get_task_import, name='get-task-import'), # type: ignore

    # For Quick Mines productions
    path('get-hauler-class/', get_haluer_class, name='get-hauler-class'), 
    path('get-hauler-factor/', get_factors, name='get-hauler-factor'), 
    # END Drop Down
    

]