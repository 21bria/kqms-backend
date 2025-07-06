from django.urls import path
from ..views.settings.data_control.ore_truck_factor_view import *
from ..views.settings.data_control.ore_class_view import *
from ..views.settings.data_control.ore_factor_adjustment_view import *
from ..views.settings.data_control.merge_dome_view import *
from ..views.settings.data_control.merge_stockpile_view import *
from ..views.settings.data_control.dome_status_view import *
from ..views.settings.data_control.dome_status_finish_view import *
from ..views.settings.remove.remove_waybill_view import *
from ..views.settings.remove.remove_mral_view import *
from ..views.settings.remove.remove_roa_view import *


urlpatterns = [
    # Table Ore Class
    path('ore-class/', OreClass_page, name='ore-class-page'), 
    path('ore-class-list/', OreClass_List.as_view(), name='ore-class-list'),
    path('ore-class/insert/', insert_OreClass, name='insert-ore-class'), 
    path('ore-class/delete/', delete_OreClass, name='delete-ore-class'), 
    path('ore-class/get-id/<int:id>/', get_OreClass, name='get-ore-class'),
    path('ore-class/update/<int:id>/', update_OreClass, name='update-ore-class'),

    # Table Ore Truck Factors
    path('ore-factors/', ore_factors_page, name='ore-factors-page'), 
    path('ore-factors-list/', OreFactorsList.as_view(), name='ore-factors-list'), 
    path('ore-factors/insert/', insert_ore_factors, name='insert-ore-factors'), 
    path('ore-truck-factors/get-id/<int:id>/', get_ore_factors, name='get-ore-truck-factors'),
    path('ore-factors/update/<int:id>/', update_ore_factors, name='update-ore-factors'),
    path('ore-factors/delete/', delete_ore_factors, name='delete-ore-factors'),

    # Table Ore Factor Ajustment
    path('ore-adjustment-factor/', ore_adjustment_page, name='ore-adjustment-page'), 
    path('ore-adjustment-factor-list/', OreFactorsAdjustList.as_view(), name='ore-adjustment-factor-list'),
    path('ore-adjustment-factor/insert/', insert_ore_adjustment, name='insert-ore-adjustment'), 
    path('ore-adjustment-factor/get-id/<int:id>/', get_ore_adjustment, name='get-ore-adjustment'),
    path('ore-adjustment-factor/update/<int:id>/', update_ore_adjustment, name='update-ore-adjustment'),
    path('ore-adjustment-factor/delete/', delete_ore_adjustment, name='delete-ore-adjustment'), 

    # Table Composting Dome
    path('merge-dome/', dome_merge_page, name='merge-dome-page'), 
    path('merge-dome-list/', domeMergeList.as_view(), name='merge-dome-factor-list'),
    path('merge-dome/insert/', insert_dome_merge, name='insert-merge-dome'), 
    path('merge-dome/get-id/<int:id>/', get_dome_merge, name='get-merge-dome'),
    path('merge-dome/update/<int:id>/', update_dome_merge, name='update-merge-dome'),
    path('merge-dome/delete/', delete_dome_merge, name='delete-merge-dome'), 
    path('merge-dome-get/stock/<int:id>/', get_oreDomeStock, name='merge-dome-get-stock'), 

    # Table Composting Stockpile
    path('merge-stockpile/', stockpile_merge_page, name='merge-stockpile-page'), 
    path('merge-stockpile-list/', stockpileMergeList.as_view(), name='merge-stockpile-list'),
    path('merge-stockpile/insert/', insert_stockpile_merge, name='insert-merge-stockpile'), 
    path('merge-stockpile/get-id/<int:id>/', get_stockpile_merge, name='get-merge-stockpile'),
    path('merge-stockpile/update/<int:id>/', update_stockpile_merge, name='update-merge-stockpile'),
    path('merge-stockpile/delete/', delete_stockpile_merge, name='delete-merge-stockpile'), 
    path('merge-stockpile-get/stock/<int:id>/', get_oreStockpile, name='merge-stockpile-get-stock'), 

    # Table Status Dome Close
    path('dome-close-status/', dome_close_page, name='dome-close-status-page'), 
    path('dome-close-status-list/', domeCloseList.as_view(), name='dome-close-status-list'),
    path('dome-close-status/insert/', insert_dome_close, name='insert-dome-close-status'), 
    path('dome-close-status/get-id/<int:id>/', get_dome_close, name='get-dome-close-status'),
    path('dome-close-status/update/<int:id>/', update_dome_close, name='update-dome-close-status'),
    path('dome-close-status/delete/', delete_dome_close, name='delete-dome-close-status'), 
    path('dome-close-status-get/stock/<int:id>/', get_oreDomeStock, name='dome-close-status-get-stock'), 

    # Table Status Dome Finished
    path('dome-finish-status/', dome_finish_page, name='dome-finish-status-page'), 
    path('dome-finish-status-list/', domeFinishList.as_view(), name='dome-finish-status-list'),
    path('dome-finish-status/insert/', insert_dome_finish, name='insert-dome-finish-status'), 
    path('dome-finish-status/get-id/<int:id>/', get_dome_finish, name='get-dome-finish-status'),
    path('dome-finish-status/update/<int:id>/', update_dome_finish, name='update-dome-finish-status'),
    path('dome-finish-status/delete/', delete_dome_finish, name='delete-dome-finish-status'), 

    # Table Remove Group Data
    path('remove-waybills/', remove_waybills_page, name='remove-waybills-page'), 
    path('remove-waybills-list/', waybillsDataView.as_view(), name='remove-waybills-list'),
    path('remove-waybills/delete/', delete_waybills_number, name='delete-group-waybills'), 

    path('remove-mral/', remove_mral_page, name='remove-mral-page'), 
    path('remove-mral-list/', mralDataView.as_view(), name='remove-mral-list'),
    path('remove-mral/delete/', delete_mral_number, name='delete-group-mral'), 

    path('remove-roa/', remove_roa_page, name='remove-roa-page'), 
    path('remove-roa-list/', roaDataView.as_view(), name='remove-roa-list'),
    path('remove-roa/delete/', delete_roa_number, name='delete-group-roa'), 
]
    