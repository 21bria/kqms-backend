# management/commands/populate_menu.py
from django.core.management.base import BaseCommand
from kqms.models import Menu
# TRUNCATE TABLE table_name RESTART IDENTITY;
# python manage.py populate_menu

class Command(BaseCommand):
    help = 'Populate menu from existing HTML structure'

    def handle(self, *args, **options):
        # Hapus menu lama
        Menu.objects.all().delete()
        
        # Kategori Main
        main_category = Menu.objects.create(
            title="Main",
            is_category=True,
            category_title="Main",
            order=1,
            allowed_group_names=['superadmin','admin-demo','management','data-control','admin-mgoqa','admin-mining','admin-selling','admin-lab','user-mgoqa','entry-selling','entry-vendors']
        )
        
        # Dashboard
        dashboard = Menu.objects.create(
            title="Dashboards",
            icon="bx bx-home",
            order=2,
            allowed_group_names=['superadmin','admin-demo','management','data-control','admin-mgoqa','admin-mining','admin-selling','admin-lab','user-mgoqa','entry-selling','entry-vendors']
        )
        
        Menu.objects.create(
            title="Analytics",
            url="home-geology",
            parent=dashboard,
            order=1
        )
        
        # Kategori Geology
        geology_category = Menu.objects.create(
            title="Geology",
            is_category=True,
            category_title="Geology",
            order=3,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-mining','admin-selling','admin-lab','user-mgoqa','entry-vendors']
        )
        
        # Samples
        samples = Menu.objects.create(
            title="Samples",
            icon="bx bx-file-blank",
            order=4,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-selling','admin-lab','user-mgoqa']
        )
        
        Menu.objects.create(
            title="List Data",
            url="samples-productions-page",
            parent=samples,
            order=1,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-selling','admin-lab','user-mgoqa']
        )
        
        from_entry = Menu.objects.create(
            title="From Entry",
            parent=samples,
            order=2,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa']
        )
        
        Menu.objects.create(
            title="Samples Qa",
            url="samples-entry-page",
            parent=from_entry,
            order=1,
            open_new_tab=True
        )
        
        Menu.objects.create(
            title="Sample Selling",
            url="samples-sale-entry-page",
            parent=from_entry,
            order=2,
            open_new_tab=True
        )
        
        check_data = Menu.objects.create(
            title="Check Sample",
             url=None,
            parent=samples,
            order=3,
             allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa']
        )
        
        Menu.objects.create(
            title="No Relation PDS",
            url="samples-relation-page",
            parent=check_data,
            order=1
        )
        
        Menu.objects.create(
            title="Pending to Lab",
            url="#",
            parent=check_data,
            order=2
        )
        
        # Waybills
        waybills = Menu.objects.create(
            title="Waybills",
            icon="bx bx-task",
            order=5,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-selling','admin-lab','user-mgoqa']
        )
        
        Menu.objects.create(
            title="Entry data",
            url="waybill-create-page",
            parent=waybills,
            order=1,
             allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa']
        )
        
        Menu.objects.create(
            title="Data Waybill",
            url="waybill-list-page",
            parent=waybills,
            order=2,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-selling','admin-lab','user-mgoqa']
        )
        
        waybill_check = Menu.objects.create(
            title="Check Waybill",
            url=None,
            parent=waybills,
            order=3,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-lab']
        )
        
        Menu.objects.create(
            title="Mral Over",
            url="over-mral-page",
            parent=waybill_check,
            order=3
        )
        
        Menu.objects.create(
            title="Roa Over",
            url="over-roa-page",
            parent=waybill_check,
            order=4
        )

        # Laboratory
        laboratory = Menu.objects.create(
            title="Laboratory",
            icon="bx bx-recycle",
            order=6,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-selling','admin-lab','user-mgoqa']
        )
        
        Menu.objects.create(
            title="Entry data",
            url="laboratory-create-page",
            parent=laboratory,
            order=1,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-lab','admin-mgoqa']
        )
        
        Menu.objects.create(
            title="Data Lab.",
            url="laboratory-list-page",
            parent=laboratory,
            order=2,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-selling','admin-lab','user-mgoqa']
        )
        
        # Menu.objects.create(
        #     title="Status Lab.",
        #     url="status-prep-page",
        #     parent=laboratory,
        #     order=3,
        #     allowed_group_names=['superadmin','data-control','admin-mgoqa','admin-lab']
        # )
        
        
        # Productions
        productions = Menu.objects.create(
            title="Productions",
            icon="bx bx-list-ol",
            order=7,
             allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-mining','admin-selling','admin-lab','user-mgoqa','entry-vendors']
        )
        
        Menu.objects.create(
            title="Entry data",
            url="ore-entry-page",
            parent=productions,
            order=1,
            open_new_tab=True,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa']
        )
        
        list_data = Menu.objects.create(
            title="List Data",
            parent=productions,
            order=2,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-mining','admin-selling','admin-lab','user-mgoqa','entry-vendors']
        )
        
        Menu.objects.create(
            title="List Ore",
            url="ore-productions-page",
            parent=list_data,
            order=1
        )
        
        Menu.objects.create(
            title="Details Ore",
            url="ore-details-page",
            parent=list_data,
            order=2
        )
        
        Menu.objects.create(
            title="Batch Status",
            url="ore-batch-page",
            parent=productions,
            order=3,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa']
        )
        
        # Assay Data
        assay = Menu.objects.create(
            title="Assay Data",
            icon="bx bxs-alarm",
            order=8,
            allowed_group_names=['superadmin','data-control','admin-mgoqa','admin-selling','admin-lab','user-mgoqa']
        )
        
        Menu.objects.create(
            title="Data mral",
            url="assay-mral-page",
            parent=assay,
            order=1,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-selling','admin-lab','user-mgoqa']
        )
        
        Menu.objects.create(
            title="Data roa",
            url="assay-roa-page",
            parent=assay,
            order=2,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-selling','admin-lab','user-mgoqa']
        )
        
        # Kategori Mining
        mining_category = Menu.objects.create(
            title="Mining",
            is_category=True,
            category_title="Mining",
            order=9,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mining','entry-vendors']

        )
        
        # Data Productions (Mining)
        mining_productions = Menu.objects.create(
            title="Data Productions",
            icon="bx bxs-folder-open",
            order=10,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mining','entry-vendors']
        )
        
        Menu.objects.create(
            title="Daily Plan",
            url="mine-production-plan-page",
            parent=mining_productions,
            order=1,
             allowed_group_names=['superadmin','admin-demo','data-control','admin-mining','entry-vendors']

        )
        
        Menu.objects.create(
            title="Daily productions",
            url="mine-production-page",
            parent=mining_productions,
            order=2,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mining','user-mining','entry-vendors']
        )
        
        # Forms
        forms = Menu.objects.create(
            title="Forms Entry",
            icon="bx bxs-message-edit",
            order=11,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mining','entry-vendors']
        )
        
        Menu.objects.create(
            title="Production",
            url="mine-production-entry-page",
            parent=forms,
            order=1,
            open_new_tab=True,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mining','entry-vendors']
        )
        Menu.objects.create(
            title="Weather",
            url="mine-production-weather-page",
            parent=forms,
            order=2,
            open_new_tab=False,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mining','entry-vendors']
        )
        
        Menu.objects.create(
            title="Summary Daily",
            url="mine-summary-daily-page",
            parent=forms,
            order=2,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mining','user-mining','entry-vendors']
        )
        # TimeSheet
        time_sheet =  Menu.objects.create(
            title="Timesheet Units",
            icon=" bx bx-task-x",
            # url="#",
            order=12,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mining','entry-vendors']
        )

        Menu.objects.create(
            title="Timesheet",
            url="mine-production-timesheet-page",
            parent=time_sheet,
            order=1,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mining','entry-vendors']
        )
        
        Menu.objects.create(
            title="Data Status",
            url="mine-production-status-activity-page",
            parent=time_sheet,
            order=2,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mining','entry-vendors']
        )
        
        Menu.objects.create(
            title="Summary",
            url="mine-summary-hm-kpi-unit-page",
            parent=time_sheet,
            order=3,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mining','entry-vendors']
        )
        
        
        Menu.objects.create(
            title="Fuel Consumption",
            icon="bx bxs-ev-station",
            url='mine-daily-fuel-page',
            order=13,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mining','entry-vendors']
        )
        

        # Configuration (Mining)
        mining_config = Menu.objects.create(
            title="Configuration",
            icon="bx bx-cog",
            order=14,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mining','entry-vendors']
        )
        
        Menu.objects.create(
            title="Truck Factors",
            url="mine-production-truck-factor-page",
            parent=mining_config,
            order=1,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mining','entry-vendors']
        )
        
        Menu.objects.create(
            title="Adjust volume",
            url="mine-production-volume-adjustment-page",
            parent=mining_config,
            order=2,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mining','entry-vendors']
        )
        Menu.objects.create(
            title="Delete bulk",
            url="remove-mine-page",
            parent=mining_config,
            order=3,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mining','entry-vendors']
        )

        # Kategori Selling
        selling_category = Menu.objects.create(
            title="Selling",
            is_category=True,
            category_title="Selling",
            order=15,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-selling','user-selling','user-mgoqa','entry-selling','admin-mining']
        )
        selling = Menu.objects.create(
            title="Selling Data",
            icon="bx bx-dollar-circle",
            order=16,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-selling','user-selling','user-mgoqa','admin-mining']
        )

        Menu.objects.create(
            title="Daily Selling",
            url="selling-barge-page",
            parent=selling,
            order=1,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-selling','user-selling','user-mgoqa','admin-mining']
        )
    
       
        blending_ore = Menu.objects.create(
            title="Ore Blending",
            parent=selling,
            order=2,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-selling','user-selling','user-mgoqa']
        )
        Menu.objects.create(
            title="Form Blending",
            url="blending-form-page",
            parent=blending_ore,
            order=1,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-selling','user-selling','user-mgoqa']
        )
 
         #Plan  Selling & Barging b
        data_plan_selling = Menu.objects.create(
            title="Plan Selling",
            parent=selling,
            order=3,
             allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','entry-selling','admin-mining']
        )
        Menu.objects.create(
            title="Selling",
            url="selling-plan-page",
            parent=data_plan_selling,
            order=1,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-selling','user-selling','user-mgoqa','admin-mining']
        )
        Menu.objects.create(
            title="Barging",
            url="barging-plan-page",
            parent=data_plan_selling,
            order=2,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-selling','user-selling','user-mgoqa','admin-mining']
        )

    
        # Analytics
        Menu.objects.create(
            title="Analytics",
            icon="bx bx-stats",
            url="selling-analysis-page",
            order=17,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-selling','user-selling','user-mgoqa']
        )

         # Forms
        forms = Menu.objects.create(
            title="Forms Entry",
            icon="bx bx-file",
            order=18,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','entry-selling','admin-mining']
        )
        
        # Menu.objects.create(
        #     title="Quick Page",
        #     url="selling-entry-quick-page",
        #     parent=forms,
        #     order=1,
        #     allowed_group_names=['superadmin','data-control','admin-mgoqa','entry-selling','admin-mining']
        # )
        # Menu.objects.create(
        #     title="Summary Daily",
        #     url="selling-daily-quick-summary-page",
        #     parent=forms,
        #     order=2,
        #     allowed_group_names=['superadmin','data-control','admin-mgoqa','entry-selling','admin-mining']
        # )
        # Menu.objects.create(
        #     title="Delete temp.",
        #     url="remove-selling-temp-page",
        #     parent=forms,
        #     order=3,
        #     allowed_group_names=['superadmin','data-control','admin-selling','admin-mgoqa']
        # )
        Menu.objects.create(
            title="Entry Barging",
            url="barging-entry-page",
            parent=forms,
            order=1,
            open_new_tab=True,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-mining']
        )
        Menu.objects.create(
            title="Summary Daily",
            url="barging-daily-summary-page",
            parent=forms,
            order=2,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-mining']
        )
        Menu.objects.create(
            title="Adjustment Barging",
            url="barging-finish-status-page",
            parent=forms,
            order=3,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-mining']
        )

        # Transfer Direct
        Menu.objects.create(
            title="Sale Direct Transfer",
            url="selling-direct-staging-page",
            parent=forms,
            order=4, 
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-selling']
        )

        # By Quick
        data_quick_barging = Menu.objects.create(
            title="Quick Entry Barging",
            parent=forms,
            order=5,
             allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','entry-selling','admin-mining']
        )
        Menu.objects.create(
            title="Entry barging",
            url="selling-entry-quick-page",
            parent=data_quick_barging,
            order=1,
             allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','entry-selling','admin-mining']
        )
        Menu.objects.create(
            title="Summary Quick",
            url="selling-daily-quick-summary-page",
            parent=data_quick_barging,
            order=2,
             allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','entry-selling','admin-mining']
        )
        Menu.objects.create(
            title="Delete temp.",
            url="remove-selling-temp-page",
            parent=data_quick_barging,
            order=3,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-selling','admin-mgoqa']
        )
      

        #Kategori Report &amp; Charts
        reporting = Menu.objects.create(
            title="Report &amp; Charts",
            is_category=True,
            category_title="Report",
            order=19,
            allowed_group_names=['superadmin','admin-demo','management','data-control','admin-mgoqa','admin-mining','admin-selling','admin-lab','user-mgoqa']
            
        )
       
        achievements = Menu.objects.create(
            title="Achievements",
            icon="bx bx-table",
            order=20,
            allowed_group_names=['superadmin','admin-demo','management','data-control','admin-mgoqa','admin-mining','admin-selling','admin-lab','user-mgoqa','entry-selling']
        )

        Menu.objects.create(
            title="Data by mral",
            url="achievement-mral-page",
            parent=achievements,
            order=1
        )
        Menu.objects.create(
            title="Data by roa",
            url="achievement-roa-page",
            parent=achievements,
            order=2
        )
        # By Stockpile
        data_by_stockpile = Menu.objects.create(
            title="By Stockpile",
            parent=achievements,
            order=3
        )
        Menu.objects.create(
            title="Data mral",
            url="stockpile-mral-page",
            parent=data_by_stockpile,
            order=1
        )
        Menu.objects.create(
            title="Data roa",
            url="stockpile-roa-page",
            parent=data_by_stockpile,
            order=2
        )
        # By Source
        data_by_source = Menu.objects.create(
            title="By Sources",
            parent=achievements,
            order=4
        )
        Menu.objects.create(
            title="Data mral",
            url="source-mral-page",
            parent=data_by_source,
            order=1
        )
        Menu.objects.create(
            title="Data roa",
            url="source-roa-page",
            parent=data_by_source,
            order=2
        )
        # Sources to Stock
        sources_to_stock = Menu.objects.create(
            title="Sources to Stock",
            parent=achievements,
            order=5
        )
        Menu.objects.create(
            title="Data mral",
            url="to-stockpile-mral-page",
            parent=sources_to_stock,
            order=1
        )
        Menu.objects.create(
            title="Data roa",
            url="to-stockpile-roa-page",
            parent=sources_to_stock,
            order=2
        )
        # Sources to Dome
        source_to_dome = Menu.objects.create(
            title="Sources to dome",
            parent=achievements,
            order=6
        )
        Menu.objects.create(
            title="Data roa",
            url="to-dome-roa-page",
            parent=source_to_dome,
            order=1
        )

        # Inventory
        inventory = Menu.objects.create(
            title="Inventory stock",
            icon="bx bx-map-alt",
            order=21,
             allowed_group_names=['superadmin','admin-demo','management','data-control','admin-mgoqa','admin-mining','admin-selling','admin-lab','user-mgoqa','entry-selling']
        )
        Menu.objects.create(
            title="Data All",
            url="inventory-page-all",
            parent=inventory,
             order=1
        )
        Menu.objects.create(
            title="Limonite",
            url="inventory-page-hpal",
            parent=inventory,
             order=2
        )
        Menu.objects.create(
            title="Saprolite",
            url="inventory-page-rkef",
            parent=inventory,
             order=3
        )
        Menu.objects.create(
            title="By Stockpile",
            url="inventory-page-stockpile",
            parent=inventory,
            order=4
        )
        Menu.objects.create(
            title="By Status Selling",
            url="inventory-page-status-all",
            parent=inventory,
            order=5
        )
        # Finish Selling
        finish_selling = Menu.objects.create(
            title="Finish Selling",
            parent=inventory,
            order=6
        )
        Menu.objects.create(
            title="Data all",
            url="inventory-finished",
            parent=finish_selling,
            order=1
        )
        Menu.objects.create(
            title="By stockpile",
            url="stockpile-finished",
            parent=finish_selling,
            order=2
        )

        # Geology
        geology = Menu.objects.create(
            title="Geology",
            icon="bx bx-map",
            order=22,
             allowed_group_names=['superadmin','admin-demo','management','data-control','admin-mgoqa','admin-mining','admin-selling','admin-lab','user-mgoqa','entry-selling']
        )
        Menu.objects.create(
            title="Data Samples",
            url="page-sample-gc",
            parent=geology,
            order=1
        )
        expect_mral = Menu.objects.create(
            title="Expect-mral",
            parent=geology,
            order=2
        )
        Menu.objects.create(
            title="Data",
            url="page-grade-expectations-mral",
            parent=expect_mral,
            order=1
        )
        Menu.objects.create(
            title="Chart",
            url="page-grade-expect-chart-mral",
            parent=expect_mral,
            order=2
        )
        expect_roa = Menu.objects.create(
            title="Expect-roa",
            parent=geology,
            order=3
        )
        Menu.objects.create(
            title="Data",
            url="page-grade-expectations-roa",
            parent=expect_roa,
            order=1
        )
        Menu.objects.create(
            title="Chart",
            url="page-grade-expect-chart-roa",
            parent=expect_roa,
            order=2
        )
        
        # Quality Assurance
        quality_assurance = Menu.objects.create(
            title="Quality Assurance",
            icon="bx bx-bar-chart-square",
            order=23,
             allowed_group_names=['superadmin','admin-demo','management','data-control','admin-mgoqa','admin-mining','admin-selling','admin-lab','user-mgoqa','entry-selling']
        )
       
        sample_dup_roa = Menu.objects.create(
            title="Sample dup-roa",
            parent=quality_assurance,
            order=1
        )
        Menu.objects.create(
            title="List Data",
            url="samples-duplicated-roa-page",
            parent=sample_dup_roa,
            order=1
        )
        Menu.objects.create(
            title="Scatter Chart",
            url="scatter-duplicate-roa",
            parent=sample_dup_roa,
            order=2
        )
        Menu.objects.create(
            title="Sample Wet",
            url="sample-duplicate-wet-roa",
            parent=sample_dup_roa,
            order=3
        )
       
        Menu.objects.create(
            title="CRM Certificate",
            url="sample-crm-page",
            parent=quality_assurance,
            order=2
        )
       
        crm_mral = Menu.objects.create(
            title="CRM mral",
            parent=quality_assurance,
            order=3
        )
        Menu.objects.create(
            title="Data",
            url="sample-crm-mral-page",
            parent=crm_mral,
            order=1
        )
        Menu.objects.create(
            title="Chart",
            url="samples-crm-mral-chart-page",
            parent=crm_mral,
            order=2
        )
        crm_roa = Menu.objects.create(
            title="CRM roa",
            parent=quality_assurance,
            order=4
        )
        Menu.objects.create(
            title="Data",
            url="sample-crm-roa-page",
            parent=crm_roa,
            order=1
        )
        Menu.objects.create(
            title="Chart",
            url="samples-crm-roa-chart-page",
            parent=crm_roa,
            order=2
        )
        mral_vs_roa = Menu.objects.create(
            title="MRAL vs ROA",
            parent=quality_assurance,
            order=5
        )
        Menu.objects.create(
            title="Data",
            url="sample-analyse-page",
            parent=mral_vs_roa,
            order=1
        )
        Menu.objects.create(
            title="Wet Chart",
            url="chart-analyse-page",
            parent=mral_vs_roa,
            order=2
        )
        Menu.objects.create(
            title="Scatter Chart",
            url="scatter-analyse-page",
            parent=mral_vs_roa,
            order=3
        )
        tat_laboratory = Menu.objects.create(
            title="Laboratory (tat)",
            parent=quality_assurance,
            order=6
        )
        Menu.objects.create(
            title="Sample order",
            url="sample-orders-tat-page",
            parent=tat_laboratory,
            order=1
        )
        Menu.objects.create(
            title="Samples (type)",
            url="sample-analyse-type-page",
            parent=tat_laboratory,
            order=2
        )
        Menu.objects.create(
            title="By Week Charts",
            url="sample-analyse-tat-page",
            parent=tat_laboratory,
            order=3
        )
        Menu.objects.create(
            title="Last Week Charts",
            url="sample-analyse-week-tat-page",
            parent=tat_laboratory,
            order=4
        )
        Menu.objects.create(
            title="Plan Grede",
            url="analyst-data-ore-plan",
            parent=quality_assurance,
            order=7
        )

        #  Export to Excel
        export = Menu.objects.create(
            title="Export Data",
            icon="bx bxs-file-doc",
            order=24,
        )
        
        Menu.objects.create(
            title="Export to Excel",
            url="export-excel-page",
            parent=export,
            order=1
        )

        # Kategory Settings
        settings = Menu.objects.create(
            title="Settings",
            is_category=True,
            category_title="Settings",
            order=25,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-mining','admin-selling','admin-lab']
        )
       
        users = Menu.objects.create(
            title="Users",
            icon="bx bx-fingerprint",
            order=26,
            allowed_group_names=['superadmin','data-control']
        )

        Menu.objects.create(
            title="Users",
            url="user-page",
            parent=users,
            order=1,
            allowed_group_names=['superadmin','data-control']
        )
        Menu.objects.create(
            title="Group",
            url="group-page",
            parent=users,
            order=2,
            allowed_group_names=['superadmin','data-control']
        )
        Menu.objects.create(
            title="Permmissions",
            url="#",
            parent=users,
            order=3,
            allowed_group_names=['superadmin','data-control']
        )
        #  Master
        master = Menu.objects.create(
            title="Master",
            icon="bx bx-data",
            order=27,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-mining','admin-selling','entry-vendors']
        )

        Menu.objects.create(
            title="Block",
            url="block-page",
            parent=master,
            order=1,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-mining']
        )
        Menu.objects.create(
            title="Materials",
            url="material-page",
            parent=master,
            order=2,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-mining']
        )
        Menu.objects.create(
            title="Source area",
            url="source-page",
            parent=master,
            order=3,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-mining']
        )
        Menu.objects.create(
            title="Loading point",
            url="source-loading-point-page",
            parent=master,
            order=4,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-mining','entry-vendors']
        )
        Menu.objects.create(
            title="Dumping point",
            url="source-dumping-point-page",
            parent=master,
            order=5,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-mining','entry-vendors']
        )
        Menu.objects.create(
            title="Dome",
            url="source-dome-point-page",
            parent=master,
            order=6,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-mining','entry-vendors']
        )
        Menu.objects.create(
            title="Mine units",
            url="mine-units-page",
            parent=master,
            order=7,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-mining','entry-vendors']
        )
        Menu.objects.create(
            title="Sample method",
            url="sample-method-page",
            parent=master,
            order=8,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-mining']
        )
        Menu.objects.create(
            title="Sample type",
            url="sample-type-page",
            parent=master,
            order=9,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-mining']
        )
        Menu.objects.create(
            title="Mine geology",
            url="mine-geologies-page",
            parent=master,
            order=10,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-mining']
        )
        Menu.objects.create(
            title="Selling Code",
            url="sale-code-page",
            parent=master,
            order=11,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-mining']
        )
        Menu.objects.create(
            title="Selling Factory",
            url="sale-factory-page",
            parent=master,
            order=12,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-mining']
        )
        Menu.objects.create(
            title="Selling Barge",
            url="sale-barge-page",
            parent=master,
            order=13,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-mining']
        )
        Menu.objects.create(
            title="Selling Jetty",
            url="sale-port-page",
            parent=master,
            order=14,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-mining']
        )

        #  Configuration
        Menu.objects.create(
            title="Configuration",
            icon="bx bx-cog",
            url="data-control-page",
            order=28,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa']
        )

        # Remove data by
        Menu.objects.create(
            title="Delete data",
            url="remove-page",
            icon="bx bx-trash-alt",
            order=29,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa']
        )

        #  Task
        task = Menu.objects.create(
            title="Task",
            icon="bx bx-task",
            order=30,
             allowed_group_names=['superadmin','data-control','admin-mgoqa','admin-mining','admin-lab']
        )

        Menu.objects.create(
            title="Import data",
            url="import-excel-page",
            parent=task,
            order=1
        )
        Menu.objects.create(
            title="Template excel",
            url="format-excel",
            parent=task,
            order=2,
            allowed_group_names=['superadmin','admin-demo','data-control','admin-mgoqa','admin-mining','admin-lab']
        )
        Menu.objects.create(
            title="Master task",
            url="task-table-page",
            parent=task,
            order=3,
            allowed_group_names=['superadmin','admin-demo','data-control']
        )
      
        self.stdout.write(self.style.SUCCESS('Successfully created menu'))
