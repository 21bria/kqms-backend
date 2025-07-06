from django.urls import path
from ..views.dashboard.index import *
from ..views.dashboard.api.geology import *
from ..views.dashboard.api.selling import *
from ..views.dashboard.api.inventory import *

# Get Mining
from ..views.dashboard.mining.all_summary import *
from ..views.dashboard.mining.details_ore import *
from ..views.dashboard.mining.details_topsoil import *
from ..views.dashboard.mining.details_ob import *
from ..views.dashboard.mining.details_waste import *
from ..views.dashboard.mining.details_quarry import *
from ..views.dashboard.mining.details_others import *


urlpatterns = [
    # Geology Dashboard
    path('geology/', geology_home, name='home-geology'),
    path('api/ore-summary/', get_ore_summary, name='get_ore_summary'),
    path('api/ore-chart/', get_chart_ore, name='get_chart_ore'),
    path('api/ore-class-chart/', get_chart_ore_class, name='get_chart_ore_class'),
   
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

    
    # Selling Dashboard
    path('api/selling-summary/', get_selling_summary, name='get_selling_summary'),
    path('api/selling-chart/', get_chart_selling, name='get_chart_selling'),

    # Inventory Dashboard
    path('api/inventory-summary/', get_inventory_summary, name='get_inventory_summary'),
    path('api/inventory-chart/', get_chart_inventory, name='get_chart_inventory'),
    path('api/stock-grade/', get_stockpile_roa, name='get_stockpile_roa'),
    path('api/dome-grade/', get_dome_roa, name='get_dome_roa'),
    path('api/ore-grade/', get_grade_roa, name='get_grade_roa'),

]
    