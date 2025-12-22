from django.urls import path
# Mine Productions
from ..views.mining.mine_productions_view import *
from ..views.mining.Quick.mine_productions_quick_view import *
from ..views.mining.plan_productions import *
from ..views.mining.analyst_days_production import*
from ..views.mining.analyst_week_production_view import*
from ..views.mining.analyst_month_production_view import*
from ..views.mining.analyst_year_production_view import*
from ..views.mining.productions_entry import*
from ..views.mining.Quick.productions_entry_quick_view import *
from ..views.mining.mine_summary import *
from ..views.mining.truck_factors import *
from ..views.mining.volume_adjustment_view import *
from ..views.mining.weather import *
from ..views.mining.timesheet_unit import *


urlpatterns = [
    # Mine Production Data
    path('mine-production/page/', mine_production_page, name='mine-production-page'), 
    path('mine-production/list/', viewMineProduction.as_view(), name='mine-production-list'),
    path('export/daily/', export_mines_data, name='export-mines-data'), 
    path('mine-totals-pds/', total_mine_pds, name='mine-totals-pds'),
    path('mine-totals-pds/mining/', total_pds_mining, name='mine-totals-pds-mining'),
    path('mine-totals-pds/project/', total_pds_project, name='mine-totals-pds-projects'),

    # Entry Data / CRUD
    path('mine-production-entry/page/', productions_entry_page, name='mine-production-entry-page'), 
    path('mine-production-entry/list/', viewproductionsCreate.as_view(), name='mine-production-entry-list'),
    path('mine-production/create/', create_production, name='mine-production-create'),
    path('mine-production/delete/', delete_mine_production, name='mine-production-delete'),
    path('mine-production/get/', getIdProduction, name='mine-production-get'),
    path('mine-production/update/<uuid:id>/', update_Production, name='mine-production-update'),

    path('mine-production-quick/page/', mine_production_quick_page, name='mine-production-quick-page'), 
    path('mine-production-quick/list/', viewMineProductionQuick.as_view(), name='mine-production-quick-list'),

    # Mine Quick Production Data
    path('mine-production-entry/quick/page/', productions_quick_entry_page, name='mine-production-entry-quick-page'), 
    path('mine-production-entry/quick/list/', viewproductionsQuickCreate.as_view(), name='mine-production-entry-quick-list'),
    path('mine-production/quick/create/', create_quick_production, name='mine-quick-production-create'),
    path('mine-production/quick/delete/', delete_quick_production, name='mine-quick-production-delete'),
    path('mine-production/quick/get/', getIdQuickProduction, name='mine-quick-production-get'),
    path('mine-production/quick/update/<uuid:id>/', update_quickProduction, name='mine-quick-production-update'),

    path('mine-totals-quick/', total_mine_quick, name='mine-totals-quick'),
    path('mine-totals-quick/mining/', total_mining_quick, name='mine-totals-quick-mining'),
    path('mine-totals-quick/project/', total_project_quick, name='mine-totals-quick-projects'),

    # Summary Daily
    path('summary/daily/page/', mine_summary_page, name='mine-summary-daily-page'), 
    path('summary/daily/', total_daily_summary, name='total-daily-summary'),
    path('summary/daily/material/', total_daily_material, name='total-daily-material'),
    path('summary/time/material/', total_time_material_by_hour, name='total-time-material'),
    path('summary/hour/material/', total_material_by_hour, name='total-hour-material'),
    # Daily Barging
    path('summary/daily/material/barging/', total_daily_summary_barging, name='total-daily-summary-barging'),
    path('summary/hour/material/barging/', total_time_barging_by_hour, name='total-hour-summary-barging'),
    path('summary/hour/chart/barging/', total_barging_by_hour, name='total-hour-chart-barging'),

    # Plan Mine Productions
    path('mine-production-plan/page/', plan_mine_production_page, name='mine-production-plan-page'), 
    path('mine-production-plan/list/', viewPlanMineProduction.as_view(), name='mine-production-plan-list'),
    path('mine-production-plan/delete/', delete_productions_plan, name='mine-production-plan-delete'),

    # Analyst Mine Production
    path('mine-production/analyst-days-page/', mine_production_days_page, name='mine-production-analyst-days-page'), 
    path('mine-production/analyst-days/', productionsMineByDays, name='get-production-analyst-days'), 
    path('mine-production/analyst-hours/', productionsMineByHours, name='get-production-analyst-hours'), 
    path('mine-production/analyst-week-group/', materialWeekProduction, name='get-production-group-week'), 
    path('mine-production/analyst-week-date/', achievmentWeekProduction, name='get-production-date-week'), 
    path('mine-production/analyst-month/', materialMonthProduction, name='get-production-material-month'), 
    path('mine-production/analyst-daily/', achievmentMonthProduction, name='get-production-achievment-daily'), 
    path('mine-production/analyst-year/', achievmentByYearProduction, name='get-production-achievment-year'), 
    path('mine-production/analyst-year-material/', materialByYearProduction, name='get-material-achievment-year'), 

    # Truck Factors
    path('mine-production/truck-factors/page/',truck_factors_page,name='mine-production-truck-factor-page'),
    path('mine-production/truck-factors/list/',dataTruckFactors.as_view(),name='mine-production-truck-factor-list'),
    path('mine-production/truck-factors/create/', create_truck_factors, name='mine-production-truck-factor-create'),
    path('mine-production/truck-factors/get/', getIdTruckFactors, name='mine-production-truck-factor-get'),
    path('mine-production/truck-factors/update/<int:id>/', update_truck_factors, name='mine-production-truck-factor-update'),
    path('mine-production/truck-factors/delete/',delete_truck_factors,name='mine-production-truck-factor-delete'),

    # Weather Data
    path('mine-production/weather/page/',weather_page,name='mine-production-weather-page'),
    path('mine-production/weather/list/',dataWeather.as_view(),name='mine-production-weather-list'),
    path('mine-production/weather/create/', create_weather, name='mine-production-weather-create'),
    path('mine-production/weather/get/', getIdWeather, name='mine-production-weather-get'),
    path('mine-production/weather/update/<int:id>/', update_weather, name='mine-production-weather-update'),
    path('mine-production/weather/delete/',delete_weather,name='mine-production-weather-delete'),

    # Timesheet Data
    path('mine-production/timesheet/page/',timesheet_page,name='mine-production-timesheet-page'),
    # path('mine-production/timesheet/list/',dataTimesheet.as_view(),name='mine-production-timesheet-list'),
    path('mine-production/ajax/hm-unit/',ajax_hm_unit_by_date_shift,name='ajax_hm_unit_by_date_shift'),
    path('mine-production/ajax/append-all-fleet/',append_all_fleet,name='ajax_append_all_fleet'),
    path('mine-production/get-hm-unit/<uuid:id>/',getIdHmUnit,name='mine-production-get-hm-unit'),
    path('mine-production/hm-unit/update/<uuid:id>/', update_hm_unit, name='mine-production-hm-unit-update'),

    path('mine-production/ajax/hm-unit/<uuid:hm_unit_id>/',ajax_hm_unit_detail,name='ajax_hm_unit_detail'),
    path('mine-production/timesheet/create/', create_timesheet, name='mine-production-timesheet-create'),
    path('mine-production/get-detail-hm/<uuid:id>/',getIdDetailHm,name='mine-production-get-detail-hm'),
    path('mine-production/detail-hm/update/<uuid:id>/', update_detail_hm, name='mine-production-detail-hm-update'),
    path('mine-production/hm-detail/delete/',delete_hm_detail,name='mine-production-hm-detail-delete'),

    # Volume adjustment
    path('mine-production/volume-adjustment/page/',volume_adjustment_page,name='mine-production-volume-adjustment-page'),
    path('mine-production/volume-adjustment/list/',volumeAdjustmentList.as_view(),name='mine-production-volume-adjustment-list'),
    path('mine-production/volume-adjustment/create/',insert_volume_adjustment,name='mine-production-volume-adjustment-create'), 
    path('mine-production/volume-adjustment/get/',getIdVolumeAdjusment,name='mine-production-volume-adjustment-get'), 
    path('mine-production/volume-adjustment/update/<int:id>/',update_volume_adjustment,name='mine-production-volume-adjustment-update'), 
    path('mine-production/volume-adjustment/delete/',delete_volume_adjustment,name='mine-production-volume-adjustment-delete'), 
    # Category
    path('mine-production/truck-factors/get_category_mine/',get_category_mine_volume,name='get-truck-factors-category-mine'),
    path('mine-production/truck-factors/get_direct_mine/',get_direct_mine_volume,name='get-truck-factors-get-direct-mine'),
    path('mine-production/truck-factors/get_vendors_mine/',get_vendors_mine_volume,name='get-truck-factors-get-vendors-mine'),
    path('mine-production/truck-factors/get_sources_mine/',get_sources_mine_volume,name='get-truck-factors-get-sources-mine'),
    path('mine-production/truck-factors/get_loading_mine/',get_loading_mine_volume,name='get-truck-factors-get-loading-mine'),
    path('mine-production/truck-factors/get_hauler_mine/',get_hauler_class_volume,name='get-truck-factors-get-hauler-mine'),
    path('mine-production/truck-factors/get_material_mine/',get_material_volume,name='get-truck-factors-get-material-mine'),
    path('mine-production/truck-factors/get_volume_mine/',get_volume_data,name='get-truck-factors-get-volume-mine'),

]