from django.urls import path
from ..views.dashboard.index import *

# Reserve
from ..views.dashboard.api.reserve import *
from ..views.dashboard.api.daily.reserve import *
# Quality
from ..views.dashboard.api.geology import *
from ..views.dashboard.api.details.quality import *

from ..views.dashboard.api.selling import *
from ..views.dashboard.api.selling_coa import *
from ..views.dashboard.api.barging import *
from ..views.dashboard.api.barging_group import *
from ..views.dashboard.api.inventory import *
from ..views.dashboard.api.details.inventory import *

# Get Mining
from ..views.dashboard.mining.all_summary import *
from ..views.dashboard.mining.details_ore import *
from ..views.dashboard.mining.details_topsoil import *
from ..views.dashboard.mining.details_ob import *
from ..views.dashboard.mining.details_waste import *
from ..views.dashboard.mining.details_quarry import *
from ..views.dashboard.mining.details_others import *

# Get Daily Report Mining
from ..views.dashboard.api.daily.mining import *
from ..views.dashboard.api.daily.productions import *

# Fuel summary Report
from ..views.dashboard.fuel.summary_fuel import *

# Weather
from ..views.dashboard.mining.weather import *

urlpatterns = [
    # Reserve Dashboard
    path('api/reserve-summary/', get_reserve_summary, name='get_reserve_summary'),
    # Geology Dashboard
    path('geology/', geology_home, name='home-geology'),
    path('api/ore-summary/', get_ore_summary, name='get_ore_summary'),
    path('api/ore-chart/', get_chart_ore, name='get_chart_ore'),
    path('api/ore-class-chart/', get_chart_ore_class, name='get_chart_ore_class'),
    path('api/chart/detail-quality/', get_chart_detail_quality, name='get_chart_detail_quality'),
    path('api/chart/detail-ore-class-lim/', get_chart_ore_class_lim, name='get_chart_ore_class_lim'),
    path('api/chart/detail-ore-class-sap/', get_chart_ore_class_sap, name='get_chart_ore_class_sap'),
   
    # Mining Dashboard
    path('api/summary/mines/ore', get_chart_ore_mining, name='get_chart_ore_mining'),
    path('api/summary/mines/quality/', get_chart_ore_quality, name='get_chart_ore_quality'),
    path('api/summary/mines', get_summary_mines, name='get_summary_mines'),
    path('api/chart/detail-ore/', get_chart_detail_ore, name='get_chart_detail_ore'),
    path('api/chart/detail-topsoil/', get_chart_detail_topsoil, name='get_chart_detail_topsoil'),
    path('api/chart/detail-ob/', get_chart_detail_ob, name='get_chart_detail_ob'),
    path('api/chart/detail-waste/', get_chart_detail_waste, name='get_chart_detail_waste'),
    path('api/chart/detail-quarry/', get_chart_detail_quarry, name='get_chart_detail_quarry'),
    path('api/chart/detail-others/', get_chart_detail_others, name='get_chart_detail_others'),

    # Weather
    path('api/weather/data/', get_data_weather, name='get_data_weather'),

    # Selling Dashboard
    path('api/selling-summary/', get_selling_summary, name='get_selling_summary'),
    path('api/selling-chart/', get_chart_selling, name='get_chart_selling'),
    # COA
    path('api/selling/coa/ni/', niChartCoa, name='get_chart_selling_coa_ni'),
    path('api/selling/coa/fe/', feChartCoa, name='get_chart_selling_coa_fe'),
    path('api/selling/coa/mgo/', mgoChartCoa, name='get_chart_selling_coa_mgo'),
    path('api/selling/coa/sio2/', sio2ChartCoa, name='get_chart_selling_coa_sio2'),
    path('api/selling/coa/sm/', smChartCoa, name='get_chart_selling_coa_sm'),
    path('api/selling/coa/all/', allChartCoa, name='get_chart_selling_coa_all'),

    # Barging
    path('api/barging-summary/', get_barging_summary, name='get-barging-summary'),
    path('api/barging-chart/', get_chart_barging, name='get-chart-barging'),
    # Group Barging
    path('api/barging-summary/group/', get_barging_summary_group, name='get-barging-summary-group'),
    path('api/barging-chart/group/', get_chart_barging_group, name='get-chart-barging-group'),

    # Inventory Dashboard
    path('api/inventory-summary/', get_inventory_summary, name='get_inventory_summary'),
    path('api/inventory-chart/', get_chart_inventory, name='get_chart_inventory'),
    path('api/stock-grade/', get_stockpile_roa, name='get_stockpile_roa'),
    path('api/dome-grade/', get_dome_roa, name='get_dome_roa'),
    path('api/ore-grade/', get_grade_roa, name='get_grade_roa'),

    path('api/inventory/chart/details/', get_chart_inventory_details, name='get_chart_inventory_details'),

    path('api/inventory-data/', get_data_inventory, name='get-data-inventory'),
    path('api/inventory-lim/', get_inventory_lim, name='get-lim-inventory'),
    path('api/inventory-sap/', get_inventory_sap, name='get-sap-inventory'),
    path('api/inventory-stockpile/', get_inventory_stockpile, name='get-stockpile-inventory'),
    # Finish Inventory
    path('api/inventory-finish/', get_inventory_finished, name='get-finish-inventory'),
    path('api/inventory-finish-stockpile/', get_stockpile_finished, name='get-finish-stockpile-inventory'),

    # Fuel Summary Dashboard
    path('api/fuel/summary/', get_chart_fuel, name='get_fuel_summary'),
    path('api/fuel/summary/category/', get_chart_fuel_category, name='get_fuel_summary_category'),
    path('api/fuel/summary/vendors/', get_chart_fuel_vendors, name='get_fuel_summary_vendors'),


    # For Daily Report Mining Page
    path('api/reserve-daily/', get_reserve_summary_daily, name='get_reserve_daily'),
    path('api/daily/mining/productions/', get_chart_daily_mining, name='get_chart_daily_mining'),
    path('api/summary/daily/mining/', get_summary_daily_mining, name='get_summary_daily_mining'),
    path('api/summary/daily/mining/materials/', get_summary_materials, name='get_summary_materials'),
    path('api/summary/daily/mining/materials/grouped/', get_summary_materials_grouped, name='get_summary_materials_grouped'),
    path('api/summary/daily/mining/weather/grouped/', get_weather_grouped, name='get_summary_weather_grouped'),
    path('api/summary/daily/mining/weather/grouped/', get_weather_grouped, name='get_summary_weather_grouped'),
    path('api/summary/daily/mining/fuel/', get_fuel_daily_report, name='get_summary_fuel_daily'),
    path('api/summary/daily/mining/fuel/ratio/', get_daily_fuel_ratio, name='get_summary_fuel_daily_ratio'),
    path('api/summary/daily/mining/fuel/ratio/ore/', get_daily_fuel_ratio_ore, name='get_summary_fuel_daily_ratio_ore'),
    # Kpi Hauler
    path('api/daily/mining/kpi/hauler/', get_kpi_daily_hauler, name='get_kpi_hauler'),
    # Kpi Digger
    path('api/daily/mining/kpi/digger/', get_kpi_daily_digger, name='get_kpi_digger'),
    # Detail productions
    path('api/daily/mining/productions/details/', get_daily_detail_productions, name='get_daily_detail_productions'),
]
    