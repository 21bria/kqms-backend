from django.contrib import admin
from django.urls import path, include
from .views.auth.login import *
from .views.generate_dummy import *


urlpatterns = [
    path('', login_view, name='login'),
    path('logout/', custom_logout, name='logout'),
    path('redirect/', redirect_by_role, name='redirect_by_role'),
    

    # Urls Sub
    path('dashboard/', include('kqms.urls_path.dashboard')),
    path('dropdown/', include('kqms.urls_path.dropdown')),
    path('geology/', include('kqms.urls_path.geology')),
    path('mining/', include('kqms.urls_path.mining')),
    path('master/', include('kqms.urls_path.master')),
    path('config/', include('kqms.urls_path.config')),
    path('report/', include('kqms.urls_path.report')),
    path('task/', include('kqms.urls_path.task')),
    path('users/', include('kqms.urls_path.users')),

    # Get Dummy Data
    path('generate-dummy-ore/', generate_dummy_ore, name='generate_dummy_ore'),
    path('generate-dummy-dome/', generate_dummy_dome, name='generate_dummy_dome'),
    path('generate-dummy-stockpile/', generate_dummy_stockpile, name='generate_dummy_stockpile'),
    path('generate-dummy-loading/', generate_dummy_loading, name='generate_dummy_loading'),

    path('generate-dummy-selling/', generate_dummy_selling, name='generate_dummy_selling'),
    path('generate-dummy-selling-plan/', generate_dummy_selling_plan, name='generate_dummy_selling_plan'),
    path('generate-dummy-mine-pds/', generate_dummy_mine_productions, name='generate_dummy_mine_productions'),
    path('generate-dummy-plan-mine/', generate_dummy_plan_productions, name='generate_dummy_plan_productions'),

   

    
]
