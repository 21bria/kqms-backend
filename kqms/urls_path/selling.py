from django.urls import path
from ..views.geology.samples.samples_create_sale import *
from ..views.selling.selling_details import *
from ..views.selling.selling_plan import *
from ..views.selling.barging_plan import *
from ..views.selling.selling_official import *
from ..views.selling.split_sample.selling_split_range import *
from ..views.selling.split_sample.selling_split_chart import *
from ..views.selling.split_sample.barging_monitoring_range import *
from ..views.selling.blending.source_inventoy import *
from ..views.selling.blending.target_blending import *
from ..views.selling.blending.create_data import *
from ..views.selling.entry.barging_data import *
from ..views.selling.entry.selling_data import *
from ..views.selling.entry.daily_summary import *
from ..views.selling.entry.daily_summary_barging import *
from ..views.selling.direct.staging_data import *
from ..views.selling.sale_analysis import *


urlpatterns = [
    # Samples Selling
    path('samples-entry/', samples_sale_page, name='samples-sale-entry-page'), 
    path('samples-entry/list/', viewEntrySale.as_view(), name='samples-sale-entry-list'),
    path('sample/create/', create_sample_sale, name='create-samples-sale'),
    # Data Selling
    path('ore-selling-totals/', total_selling, name='ore-selling-totals'),
    path('ore-selling/totals/', total_selling_details, name='ore-selling-totals-details'),
    path('barge/page/', sale_details_page, name='selling-barge-page'), 
    
    path('barge/list/', SellingDetails.as_view(), name='selling-barge-list'),
    path('export/daily/', export_sale_data, name='export-selling-data'), 
    # Plan
    path('plan-page/selling', sale_plan_page, name='selling-plan-page'),
    path('plan/list/', sellingDataPlan.as_view(), name='selling-plan-list'),

    # Analysis
    path('analysis/page/', sale_analysis_page, name='selling-analysis-page'),
   
    # CRUD
    path('plan/create/', create_plan_sale, name='create-plan-sale'),
    path('plan/get-id/<uuid:id>/', getIdPlanSale, name='get-id-sale-plan'), 
    path('plan/update/<uuid:id>/', update_sale_plan, name='update-sale-plan'),
    path('plan/delete/', delete_sale_plan, name='delete-sale-plan'),

    path('plan-page/barge/', sale_barge_plan_page, name='barging-plan-page'),
    path('plan/list/barging/', bargingDataPlan.as_view(), name='barging-plan-list'),
    path('plan/delete/barging/', delete_barging_plan, name='delete-barging-plan'),

    # Official
    path('official-page/', sale_official_page, name='sale-official-page'),
    path('official/list/', sellingDataOfficial.as_view(), name='sale-official-list'),
    path('official/create/', create_official_sale, name='create-official-sale'),
    path('official/get-id/<int:id>/', getIdOfficial, name='get-sale-official'),
    path('official/update/<int:id>/', update_official, name='update-sale-official'),
    path('official/delete/', delete_sale_official, name='delete-official-sale'),

    # Monitoring Split Selling
    
    path('monitoring/sample/page/', monitoringSamplePage, name='monitoring-sample-page'),
    path('monitoring/chart/page/', monitoringChartPage, name='monitoring-chart-page'),
    path('monitoring/sample/list/', samplesMonitoring, name='barging-monitoring-sample-list'),

    # Split  Selling
    path('split/sample/page/', splitSamplePage, name='sale-split-sample-page'),
    path('split/sample/list/', samplesSplit, name='sale-split-sample-list'),

    # Official COA
    path('split/coa/page/', splitOfficialPage, name='sale-split-coa-page'),
    path('split/coa/list/', splitOfficial, name='sale-split-coa-list'),

    # Official COA Plotly Chart
    path('split/coa/chart/page/', splitOfficialChartPage, name='sale-split-coa-chart-page'),
    path('split/ni/chart/', niChartPlot, name='split-ni-coa-chart'),
    path('split/fe/chart/', feChartPlot, name='split-fe-coa-chart'),
    path('split/mgo/chart/', mgoChartPlot, name='split-mgo-coa-chart'),
    path('split/sio2/chart/', sio2ChartPlot, name='split-sio2-coa-chart'),
    path('split/sm/chart/', smChartPlot, name='split-sm-coa-chart'),

    # Blending
    path('blending/data/source/', get_data_source, name='blending-get-source'),
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
    path('quick/get/<uuid:id>/', get_sale_quick, name='sale-quik-get'),
    path('quick/update/<uuid:id>/', update_quick_selling, name='sale-quick-update'),
    path('quick/delete/', delete_selling_temp, name='selling-quick-delete'),

    # Create Barging
    path('entry/page/barging/', barging_entry_page, name='barging-entry-page'),
    path('barging/list/', BargingTemp.as_view(), name='barging-list-temp'),
    path('barging/create/', create_barging_data, name='create-barging-data'),
    path('barging/delete/', delete_barging_temp, name='barging-delete-temp'),

    # Daily summary temp
    path('daily/quick/summary/',daily_selling_summary_page, name='selling-daily-quick-summary-page'),
    path('daily/quick/summary/data/',total_daily_summary_quick, name='selling-daily-quick-summary'),
    path('daily/quick/summary/sublot/',total_daily_sublot, name='sublot-daily-quick-summary'),

    # Daily barging summary
    path('daily/barging/summary/',daily_barging_summary_page, name='barging-daily-summary-page'),
    path('daily/barging/summary/data/',total_daily_summary_barging, name='daily-barging-summary'),
    path('daily/barging/summary/sublot/',total_daily_barging_sublot, name='sublot-daily-barging-summary'),
    path('summary/hours/material/barging/', total_time_barging_by_hours, name='total-hours-summary-barging'),
    path('summary/housr/chart/barging/', total_barging_by_hours, name='total-hours-chart-barging'),

    # Direct Trasfer
    path('direct/selling/page/', staging_data_page, name='selling-direct-staging-page'),
    path('direct/selling/staging/list/', dataStagingList.as_view(), name='selling-direct-staging-list'),
    path('direct/get/tonnage/', get_tonnage_direct,name='direct-get-tonnage'),
    path('direct/insert/productions/', transfers_direct_production, name='insert-direct-sale-productions'),

   
]