from django.contrib import admin
from django.urls import path, include
from .views.auth.login import *
from .views.generate_dummy import *
from .views.report.export_excel import *
from .views.gis.geo_json_covert import *
from .views.gis.geo_json_mine_iup import *

urlpatterns = [
    path('', login_view, name='login'),
    path('logout/', custom_logout, name='logout'),
    path('redirect/', redirect_by_role, name='redirect_by_role'),
    

    # Urls Sub
    path('dashboard/', include('kqms.urls_path.dashboard')),
    path('dropdown/', include('kqms.urls_path.dropdown')),
    path('geology/', include('kqms.urls_path.geology')),
    path('laboratory/', include('kqms.urls_path.laboratory')),
    path('mining/', include('kqms.urls_path.mining')),
    path('selling/', include('kqms.urls_path.selling')),
    path('master/', include('kqms.urls_path.master')),
    path('config/', include('kqms.urls_path.config')),
    path('recon/', include('kqms.urls_path.recon')),
    path('report/', include('kqms.urls_path.report')),
    path('task/', include('kqms.urls_path.task')),
    path('users/', include('kqms.urls_path.users')),
    path('excel/', include('kqms.urls_path.excel')),


    # Get Dummy Data
    path('generate-dummy-ore/', generate_dummy_ore, name='generate_dummy_ore'),
    path('generate-dummy-dome/', generate_dummy_dome, name='generate_dummy_dome'),
    path('generate-dummy-stockpile/', generate_dummy_stockpile, name='generate_dummy_stockpile'),
    path('generate-dummy-loading/', generate_dummy_loading, name='generate_dummy_loading'),

    path('generate-dummy-selling/', generate_dummy_selling, name='generate_dummy_selling'),
    path('generate-dummy-selling-plan/', generate_dummy_selling_plan, name='generate_dummy_selling_plan'),
    path('generate-dummy-mine-pds/', generate_dummy_mine_productions, name='generate_dummy_mine_productions'),
    path('generate-dummy-plan-mine/', generate_dummy_plan_productions, name='generate_dummy_plan_productions'),

    # Export Excel
    path('export/excel/page/', export_excel_page, name='export-excel-page'),

    # Services
    path("gis/import/", imports_json_page, name="gis-import-page"),
    path("gis/api/convert-geojson/", upload_convert_geojson, name="upload_convert_geojson"),
    path("gis/sync-geojson/", sync_geojson_to_db, name="sync_geojson_to_db"),

    # Geo Json Mine IUP
    path("gis/mine-iup/", mine_iup_page, name="gis-mine-iup-page"),
    path("gis/api/mine-iup/<int:iup_id>/",api_iup_with_sources, name="api-iup-with-sources"),

]
