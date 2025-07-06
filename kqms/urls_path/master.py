from django.urls import path
# Master Tables
from ..views.master.materials import *
from ..views.master.source_view import *
from ..views.master.block_view import *
from ..views.master.source_loading_point_view import *
from ..views.master.source_dumping_point_view import *
from ..views.master.source_dome_points_view import *
from ..views.master.sampling_type_view import *
from ..views.master.sample_method_view import *
from ..views.master.mine_geologies_view import *
from ..views.master.selling_code_view import *
from ..views.master.mine_units_view import *
from ..views.settings.data_control.ore_class_view import *

urlpatterns = [
    # Table Blok
    path('block/', block_page, name='block-page'),  
    path('block/insert_block/', insert_block, name='insert-block'), 
    path('block/delete_block/', delete_block, name='delete-block'),
    path('block/get-id/<int:id>/', get_block, name='get-block'),
    path('block/update_block/<int:id>/', update_block, name='update-block'),
    path('block-list/', AjaxBlockList.as_view(), name='block-list'),

    # Table - Material
    path('material/', material_page, name='material-page'), 
    path('material-list/', Materials_List.as_view(), name='material-list'), 
    path('material/insert_material/', insert_material, name='insert-material'), 
    path('material/delete_material/', delete_material, name='delete-material'),
    path('material/get_id/<int:id>/', get_material, name='get-material'),
    path('material/update_material/<int:id>/', update_material, name='update-material'),

    # Table Source Area
    path('source/', source_page, name='source-page'), 
    path('source-list/', Source_List.as_view(), name='source-list'), 
    path('source/insert_source/', insert_source, name='insert-source'), 
    path('source/delete_source/', delete_source, name='delete-source'),
    path('source/get_id/<int:id>/', get_source, name='get-source'),
    path('source/update_source/<int:id>/', update_source, name='update-source'),

    # Table Mine Loading Point
    path('mine-source/loading-point/', minesLoading_page, name='source-loading-point-page'), 
    path('mine-source/loading-point/list/', sourceMinesLoading_List.as_view(), name='source-loading-point-list'), 
    path('mine-source/loading-point/insert/', insert_minesLoading, name='insert-source-loading-point'), 
    path('mine-source/loading-point/delete/', delete_minesLoading, name='delete-source-loading-point'),
    path('mine-source/loading-point/get/<int:id>/', get_minesLoading, name='get-source-loading-point'),
    path('mine-source/loading-point/update/<int:id>/', update_minesLoading, name='update-source-loading-point'),
    path('export/loading-point',export_loading_point, name='export-loading-point'),

    # Table Mine Dumping Point
    path('mine-source/dumping-point/', minesDumping_page, name='source-dumping-point-page'), 
    path('mine-source/dumping-point/list/', sourceMinesDumping_List.as_view(), name='source-dumping-point-list'), 
    path('mine-source/dumping-point/insert/', insert_minesDumping, name='insert-source-dumping-point'), 
    path('mine-source/dumping-point/delete/', delete_minesDumping, name='delete-source-dumping-point'),
    path('mine-source/dumping-point/get/<int:id>/', get_minesDumping, name='get-source-dumping-point'),
    path('mine-source/dumping-point/update/<int:id>/', update_minesDumping, name='update-source-dumping-point'),
    path('export/dumping-point',export_dumping_point, name='export-dumping-point'),

    # Table Mine source Dome Point
    path('mine-source/dome-point/', sourceDomePoint_page, name='source-dome-point-page'), 
    path('mine-source/dome-point/list/', sourceDomePoint_List.as_view(), name='source-dome-point-list'), 
    path('mine-source/dome-point/insert/', insert_sourceDomePoint, name='insert-source-dome-point'), 
    path('mine-source/dome-point/delete/', delete_sourceDomePoint, name='delete-source-dome-point'),
    path('mine-source/dome-point/get/<int:id>/', get_sourceDomePoint, name='get-source-dome-point'),
    path('mine-source/dome-point/update/<int:id>/', update_sourceDomePoint, name='update-source-dome-point'),
    path('export/dome-point',export_dome_point, name='export-dome-point'),

    # Table Sample type
    path('sample-type/', sampleType_page, name='sample-type-page'), 
    path('sample-type-list/', SampleType_List.as_view(), name='sample-type-list'), 
    path('sample-type/insert/', insert_sampleType, name='insert-sample-type'), 
    path('sample-type/get_id/<int:id>/', get_sampleType, name='get-sample-type'),
    path('sample-type/update/<int:id>/', update_sampleType, name='update-sample-type'),
    path('sample-type/delete/', delete_sampleType, name='delete-sample-type'),

    # Table Sample method
    path('sample-method/', sample_method_page, name='sample-method-page'), 
    path('sample-method-list/', SampleMethod_List.as_view(), name='sample-method-list'), 
    path('sample-method/insert/', insert_method, name='insert-sample-method'), 
    path('sample-method/get_id/<int:id>/', get_method, name='get-sample-method'),
    path('sample-method/update/<int:id>/', update_method, name='update-sample-method'),
    path('sample-method/delete/', delete_method, name='delete-sample-method'),
    
    # Table Mine Geologies
    path('mine-geologies/', geologies_page, name='mine-geologies-page'), 
    path('mine-geologies/list', MineGeologiesList.as_view(), name='mine-geologies-list'), 
    path('mine-geologies/insert/', insert_geologies, name='insert-mine-geologies'), 
    path('mine-geologies/get_id/<int:id>/', get_geologies, name='get-mine-geologies'),
    path('mine-geologies/update/<int:id>/', update_geologies, name='update-mine-geologies'),
    path('mine-geologies/delete/', delete_geologies, name='delete-mine-geologies'),

    # Table Mine Units
    path('mine-units/', MineUnits_page, name='mine-units-page'), 
    path('mine-units-list/', MineUnits_List.as_view(), name='mine-units-list'),
    path('mine-units/insert/', insert_MineUnits, name='insert-mine-units'), 
    path('mine-units/delete/', delete_MineUnits, name='delete-mine-units'), 
    path('mine-units/get-id/<int:id>/', get_MineUnits, name='get-mine-units'),
    path('mine-units/update/<int:id>/', update_MineUnits, name='update-mine-units'),

    # Table Sale Code
    path('sale-code/', code_page, name='sale-code-page'), 
    path('sale-code/list', SaleCodeList.as_view(), name='sale-code-list'), 
    path('sale-code/insert/', insert_code, name='insert-sale-code'), 
    path('sale-code/get_id/<int:id>/', get_code, name='get-sale-code'),
    path('sale-code/update/<int:id>/', update_code, name='update-sale-code'),
    path('sale-code/delete/', delete_code, name='delete-sale-code'),

    # Table Sale Stock Temp

    # Table Sale Dome Temp


]