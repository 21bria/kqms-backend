from django.urls import path
# achievements
from ..views.report.achievements.achievements_mral_view import *
from ..views.report.achievements.achievements_roa_view import *

# inventory
from ..views.report.inventory.inventory_all_view import *
from ..views.report.inventory.inventory_finish_view import *

# Grade Control sample
from ..views.report.grade_control.samples_gc_view import *
from ..views.report.grade_control.grade_expectations_view import *
from ..views.report.grade_control.grade_expectations_roa import *

# QA Report :
from ..views.report.quality_assurance.samples_duplicate.sample_duplicate_plotly import *
from ..views.report.quality_assurance.samples_duplicate.sample_duplicate_mral import *
from ..views.report.quality_assurance.samples_duplicate.sample_duplicate_roa import *
from ..views.report.quality_assurance.samples_duplicate.sample_duplicate_roa_plotly import *
from ..views.report.quality_assurance.samples_crm.sample_crm_view import *
from ..views.report.quality_assurance.samples_crm.sample_crm_mral_view import *
from ..views.report.quality_assurance.samples_crm.sample_crm_roa_view import *
from ..views.report.quality_assurance.analysis_mral_roa.analyse_mral_roa_view import *
from ..views.report.quality_assurance.analysis_mral_roa.analyse_mral_roa_plotly import *
from ..views.report.lab_performance.sample_type_count_view import *
from ..views.report.lab_performance.lab_performance_view import *
from ..views.report.lab_performance.lab_performance_weeks_view import *
from ..views.report.lab_performance.samples_orders_view import *
from ..views.report.quality_assurance.analyst_ore_plan import *
from ..views.report.quality_assurance.grade_ore_batch import *


urlpatterns = [
      # achievement
    path('achievement/mral-index', achievement_mral_page, name='achievement-mral-page'), 
    path('achievement/mral',achievement_mral, name='achievement-mral'),

    path('stockpile/mral-index', stockpile_mral_page, name='stockpile-mral-page'), 
    path('stockpile/mral',stockpile_mral, name='stockpile-mral'),

    path('source/mral-index', source_mral_page, name='source-mral-page'), 
    path('source/mral',source_mral, name='source-mral'),

    path('to-stockpile/mral-index', to_stockpile_mral_page, name='to-stockpile-mral-page'), 
    path('to-stockpile/mral',to_stockpile_mral, name='to-stockpile-mral'),

    path('to-dome-/mral-index', to_dome_mral_page, name='to-dome-mral-page'), 
    path('to-dome/mral',to_dome_mral, name='to-dome-mral'),
    
    path('achievement/roa-index', achievement_roa_page, name='achievement-roa-page'), 
    path('achievement/roa',achievement_roa, name='achievement-roa'),

    path('stockpile/roa-index', stockpile_roa_page, name='stockpile-roa-page'), 
    path('stockpile/roa',stockpile_roa, name='stockpile-roa'),

    path('source/roa-index', source_roa_page, name='source-roa-page'), 
    path('source/roa',source_roa, name='source-roa'),

    path('to-stockpile/roa-index', to_stockpile_roa_page, name='to-stockpile-roa-page'), 
    path('to-stockpile/roa',to_stockpile_roa, name='to-stockpile-roa'),

    path('to-dome-/roa-index', to_dome_roa_page, name='to-dome-roa-page'), 
    path('to-dome/roa',to_dome_roa, name='to-dome-roa'),

    # inventory
    path('inventory/all-page',inventory_all_page, name='inventory-page-all'),
    path('inventory/hpal-page',inventory_hpal_page, name='inventory-page-hpal'),
    path('inventory/rkef-page',inventory_rkef_page, name='inventory-page-rkef'),
    path('inventory/get-all',getInventoryAll, name='get-inventory-all'),
    path('inventory/get-hpal',getInventoryHpal, name='get-inventory-hpal'),
    path('inventory/get-rkef',getInventoryRkef, name='get-inventory-rkef'),

    path('inventory/stockpile-page',inventory_stockpile_page, name='inventory-page-stockpile'),
    path('inventory/stockpile-hpal',inventory_stockpile_hpal, name='inventory-stockpile-hpal'),
    path('inventory/stockpile-rkef',inventory_stockpile_rkef, name='inventory-stockpile-rkef'),
    path('inventory/get-stockpile',getStockpileAll, name='get-stockpile-all'),
    path('inventory/get-stockpile-hpal',getStockpileHpal, name='get-stockpile-hpal'),
    path('inventory/get-stockpile-rkef',getStockpileRkef, name='get-stockpile-rkef'),

    path('inventory/finished-page',inventory_finished_page, name='inventory-finished'),
    path('inventory/get-finished',getInventoryFinished, name='get-inventory-finished'),

    path('inventory/stockpile-finished',stockpile_finished_page, name='stockpile-finished'),
    path('inventory/get-stockpile-finished',getStockpileFinished, name='get-stockpile-finished'),

    # Grade Conrtrol samples
    path('sample/gc-page',sample_gc_page, name='page-sample-gc'),
    path('sample/grade-control', GcSamples.as_view(), name='list-sample-gc'), 
    path('export/sample/gc/',export_gc_sample, name='export-samples-gc'),

    path('grade-expectations/mral-page', grade_expectations_page, name='page-grade-expectations-mral'), 
    path('grade-expectations/get-data-mral', GradeExpectations_mral.as_view(), name='list-grade-expectations-mral'),

    path('grade-expectations/chart-mral-page', grade_expect_chart_page, name='page-grade-expect-chart-mral'), 
    path('grade-expectations/scatter-mral', scatter_plot_grade_exmral, name='grade-expect-scatter-mral'), 
    path('grade-expectations/line-sample-mral', line_plot_sample_exmral, name='grade-expect-sample-mral'), 
    path('grade-expectations/line-date-mral', line_plot_date_exmral, name='grade-expect-date-mral'), 
    path('grade-expectations/line-geos-mral', line_plot_geos_exmral, name='grade-expect-geos-mral'), 

    path('grade-expectations/page-geos-mral/', geos_expect_chart_page, name='page-geos-expect-chart-mral'), 
    path('grade-expectations/scatter-geos-mral/', scatterMineGeosExmral, name='grade-expect-geos-scatter-mral'), 
    path('grade-expectations/group-geos-mral/', lineMineGeosExmral, name='grade-expect-geos-group-mral'), 

    path('grade-expectations/roa-page', grade_expectations_roa_page, name='page-grade-expectations-roa'), 
    path('grade-expectations/get-data-roa', GradeExpectations_roa.as_view(), name='list-grade-expectations-roa'), 

    path('grade-expectations/chart-roa-page', grade_expect_roa_page, name='page-grade-expect-chart-roa'), 
    path('grade-expectations/scatter-roa', scatterGradeExRoa, name='grade-expect-scatter-roa'), 
    path('grade-expectations/line-sample-roa', lineSampleExRoa, name='grade-expect-sample-roa'), 
    path('grade-expectations/line-date-roa', lineDateExRoa, name='grade-expect-date-roa'), 
    path('grade-expectations/line-geos-roa', lineGeosExRoa, name='grade-expect-geos-roa'), 

    path('grade-expectations/page-geos-roa/', geos_expect_roa_page, name='page-geos-expect-chart-roa'), 
    path('grade-expectations/scatter-geos-roa/', scatterMineGeosExRoa, name='grade-expect-geos-scatter-roa'), 
    path('grade-expectations/group-geos-roa/', lineMineGeosExRoa, name='grade-expect-geos-group-roa'),


     # OQA Report
    path('samples-duplicated/page/', sampleDuplicateMral, name='samples-duplicated-page'), 
    path('samples-duplicated/list/', SamplesDuplicatedMral.as_view(), name='samples-duplicated-list'), 

    path('scatter/sample-dup-mral', scatter_plot_dup_mral, name='scatter-plot-dup-mral'),
    path('scatter/plotly/ni', scatter_plotly_ni, name='scatter_plotly_ni'),
    path('scatter/plotly/co', scatter_plotly_co, name='scatter_plotly_co'),
    path('scatter/plotly/fe', scatter_plotly_fe, name='scatter_plotly_fe'),
    path('scatter/plotly/mgo', scatter_plotly_mgo, name='scatter_plotly_mgo'),
    path('scatter/plotly/sio2', scatter_plotly_sio2, name='scatter_plotly_sio2'),

    path('samples-duplicated/page-roa/', sampleDuplicateRoa, name='samples-duplicated-roa-page'), 
    path('samples-duplicated/list-roa/', SamplesDuplicatedRoa.as_view(), name='samples-duplicated-roa-list'), 

    # for Wet  Mral & roa
    path('chart/sample-wet-mral', sampleDuplicateWetMral, name='sample-duplicate-wet-mral'),
    path('chart/sample-wet-year/mral', wetYearDataMral, name='sample-wet-year-mral'),
    path('chart/sample-wet-month/mral', wetMonthDataMral, name='sample-wet-month-mral'),
    path('chart/sample-wet-week/mral', wetWeekDataMral, name='sample-wet-week-mral'),
    path('chart/plotly/sample-wet-year/mral', chart_wet_year, name='plotly-sample-wet-year-mral'),
    path('chart/plotly/sample-wet-month/mral', chart_wet_month, name='plotly-sample-wet-month-mral'),
    path('chart/plotly/sample-wet-week/mral', chart_wet_week, name='plotly-sample-wet-week-mral'),

    path('chart/sample-wet-roa', sampleDuplicateWetRoa, name='sample-duplicate-wet-roa'),
    path('chart/sample-wet-year/roa', weYearDataRoa, name='sample-wet-year-roa'),
    path('chart/sample-wet-month/roa', wetMonthDataRoa, name='sample-wet-month-roa'),
    path('chart/sample-wet-week/roa', wetWeekDataRoa, name='sample-wet-week-roa'),
    path('chart/plotly/sample-wet-year/roa', chart_wet_year_roa, name='plotly-sample-wet-year-roa'),
    path('chart/plotly/sample-wet-month/roa', chart_wet_month_roa, name='plotly-sample-wet-month-roa'),
    path('chart/plotly/sample-wet-week/roa', chart_wet_week_roa, name='plotly-sample-wet-week-roa'),

    path('scatter/duplicate/roa', scatterPlotRoa, name='scatter-duplicate-roa'),
    path('scatter/duplicate/roa-ni', scatter_plotly_ni_roa, name='scatter-duplicate-roa-ni'),
    path('scatter/duplicate/roa-co', scatter_plotly_co_roa, name='scatter-duplicate-roa-co'),
    path('scatter/duplicate/roa-fe', scatter_plotly_fe_roa, name='scatter-duplicate-roa-fe'),
    path('scatter/duplicate/roa-mgo', scatter_plotly_mgo_roa, name='scatter-duplicate-roa-mgo'),
    path('scatter/duplicate/roa-sio2', scatter_plotly_sio2_roa, name='scatter-duplicate-roa-sio2'),
  
    # CRM certified
    path('samples-crm/page/', sampleCrmPage, name='sample-crm-page'), 
    path('samples-crm/list/', SamplesCrm.as_view(), name='samples-crm-list'), 

    path('samples-crm/page-mral/', sampleCrmMralPage, name='sample-crm-mral-page'), 
    path('samples-crm/list-mral/', sampleCrmMral.as_view(), name='samples-crm-mral-list'), 
    path('samples-crm/page-chart-mral/', sampleCrmMralChart, name='samples-crm-mral-chart-page'), 
    path('samples-crm/get-mral/', getDataCrmMral, name='samples-crm-mral-get'), 
    path('samples-crm/get-mral-plotly/', getDataCrmMralplotly, name='samples-crm-mral-plotly-get'), 

    path('samples-crm/page-roa/', sampleCrmRoaPage, name='sample-crm-roa-page'), 
    path('samples-crm/list-roa/', sampleCrmRoa.as_view(), name='samples-crm-roa-list'), 
    path('samples-crm/page-chart-roa/', sampleCrmRoaChart, name='samples-crm-roa-chart-page'), 
    path('samples-crm/get-roa/', getDataCrmRoa, name='samples-crm-roa-get'), 
    path('samples-crm/get-roa-plotly/', getDataCrmRoaplotly, name='samples-crm-roa-plotly-get'), 

    # Mral vs Roa Analise
    path('samples-analyse/page/', analyseMralRoaPage, name='sample-analyse-page'), 
    path('samples-analyse/list-mral-roa/', getAnalyseData.as_view(), name='analyse-mral-roa-list'), 
    path('samples-analyse/chart/page/', analyseMralRoaChartPage, name='chart-analyse-page'), 
    path('samples-analyse/chart/mral-roa-year/', yearDataAnalyse, name='analyse-mral-roa-year'), 
    path('samples-analyse/chart/mral-roa-month/', monthDataAnalyse, name='analyse-mral-roa-month'), 
    path('samples-analyse/chart/mral-roa-week/', weekDataAnalyse, name='analyse-mral-roa-week'), 
    # Plotly
    path('samples-analyse/plotly/chart/mral-roa-year/', plotly_wet_year, name='analyse-plotly-mral-roa-year'), 
    path('samples-analyse/plotly/chart/mral-roa-month/', plotly_wet_month, name='analyse-plotly-mral-roa-month'), 
    path('samples-analyse/plotly/chart/mral-roa-week/', plotly_wet_weekly, name='analyse-plotly-mral-roa-week'), 

    path('scatter/analyse/page/', scatter_plot_mral_roa, name='scatter-analyse-page'), 
    path('scatter/analyse/mral-roa-ni', scatterplotlyNi, name='scatter-analyse-mral-roa-ni'),
    path('scatter/analyse/mral-roa-co', scatterplotlyCo, name='scatter-analyse-mral-roa-co'),
    path('scatter/analyse/mral-roa-fe', scatterplotlyFe, name='scatter-analyse-mral-roa-fe'),
    path('scatter/analyse/mral-roa-mgo', scatterplotlyMgo, name='scatter-analyse-mral-roa-mgo'),
    path('scatter/analyse/mral-roa-sio2', scatterplotlySio2, name='scatter-analyse-mral-roa-sio2'),

    # Sample Type Data
    path('sample/analyse/type', sampleTypeChart, name='sample-analyse-type-page'),
    path('sample/analyse/type-year', chartTypeYear, name='sample-analyse-type-year'),
    path('sample/analyse/type-month', chartTypeMonth, name='sample-analyse-type-month'),
    path('sample/analyse/orders-year', chartOrdersYear, name='sample-analyse-orders-year'),
    path('sample/analyse/orders-five-week', chartFiveWeeks, name='sample-analyse-orders-five-week'),
    path('sample/analyse/orders-table-range', getSampleOrdersByWeeks, name='sample-analyse-orders-range'),
    path('sample/analyse/orders-chart-range', chartTypeByWeek, name='sample-analyse-chart-range'),
    path('sample/analyse/orders-donut-range', donutTypeByWeek, name='sample-analyse-donut-range'),
    path('sample/analyse/orders-chart-range-gc', chartGcByWeek, name='sample-analyse-chart-range-gc'),
    path('sample/analyse/orders-chart-range-qa', chartQaByWeek, name='sample-analyse-chart-range-qa'),
    path('sample/analyse/orders-chart-range-sale', chartSaleByWeek, name='sample-analyse-chart-range-sale'),

    # Lab Performace TAT
    path('sample/orders/tat', sampleTatOrders, name='sample-orders-tat-page'),
    path('samples/orders/list/', samplesOrders.as_view(), name='samples-orders-list'), 

    path('sample/analyse/tat', sampleTatChart, name='sample-analyse-tat-page'),
    path('sample/analyse/tat-mral', getDataMralByWeeks, name='sample-analyse-tat-mral'),
    path('sample/analyse/tat-roa', getDataRoaByWeeks, name='sample-analyse-tat-roa'),
    path('sample/analyse/chart-tat-mral', chartTatMral, name='sample-analyse-chart-tat-mral'),
    path('sample/analyse/chart-tat-roa', chartTatRoa, name='sample-analyse-chart-tat-roa'),

    path('sample/analyse/week-tat', sampleWeekTatChart, name='sample-analyse-week-tat-page'),
    path('sample/analyse/week-tat-mral', getMralGroupWeeks, name='sample-analyse-week-tat-mral'),
    path('sample/analyse/week-tat-roa', getRoaGroupWeeks, name='sample-analyse-week-tat-roa'),
    path('sample/analyse/week-tat-chart-mral', chartWeeksTatMral, name='sample-analyse-week-tat-chart-mral'),
    path('sample/analyse/week-tat-chart-roa', chartWeeksTatRoa, name='sample-analyse-week-tat-chart-roa'),

    #QA PLan Grade
    path('data-analyst/ore-histograms/', get_data_histograms, name='get-ore-data-histograms-analyst'),
    path('analyst/data-ore-plan/', analystOrePlan_page, name='analyst-data-ore-plan'),
    path('data-analyst/ore-histograms-mral/', get_ore_grade_mral, name='get-ore-mral-histograms-analyst'),
    path('data-analyst/ore-histograms-roa/', get_ore_grade_roa, name='get-ore-roa-histograms-analyst'),
    path('data-analyst/ore-bar-date/', get_ore_date_qa, name='get-ore-date-histograms-analyst'),
    path('data-analyst/ore-bar-dome/', get_ore_dome_qa, name='get-ore-dome-histograms-analyst'),

    # Qa Ore Grade
    path('page/grade/ore-batch/', grade_ore_page, name='page-ore-grade-batch'),
    path('data/grade/ore-batch/mral/', mralgradeBatch, name='data_grade_ore_batch_mral'),
    path('data/grade/ore-batch/roa/', roagradeBatch, name='data_grade_ore_batch_roa'),


]