# management/commands/populate_menu.py
from django.core.management.base import BaseCommand
from kqms.models import Menu
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
            order=1
        )
        
        # Dashboard
        dashboard = Menu.objects.create(
            title="Dashboards",
            icon="bx bx-home",
            order=2,
            allowed_group_names=["superadmin", "user"]
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
            order=3
        )
        
        # Samples
        samples = Menu.objects.create(
            title="Samples",
            icon="bx bx-file-blank",
            order=4,
            allowed_group_names=["superadmin", "geology"]
        )
        
        Menu.objects.create(
            title="List Data",
            url="samples-productions-page",
            parent=samples,
            order=1
        )
        
        from_entry = Menu.objects.create(
            title="From Entry",
            parent=samples,
            order=2
        )
        
        Menu.objects.create(
            title="Samples Qa",
            url="samples-entry-page",
            parent=from_entry,
            order=1
        )
        
        Menu.objects.create(
            title="Sample Selling",
            url="#",
            parent=from_entry,
            order=2
        )
        
        check_data = Menu.objects.create(
            title="Check Data",
            parent=samples,
            order=3
        )
        
        Menu.objects.create(
            title="No Relation PDS",
            url="#",
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
            allowed_group_names=["superadmin", "production"]
        )
        
        Menu.objects.create(
            title="Entry data",
            url="waybill-create-page",
            parent=waybills,
            order=1
        )
        
        Menu.objects.create(
            title="List Data",
            url="waybill-page",
            parent=waybills,
            order=2
        )
        
        waybill_check = Menu.objects.create(
            title="Check Data",
            parent=waybills,
            order=3
        )
        
        Menu.objects.create(
            title="Mral Over",
            url="over-mral-page",
            parent=waybill_check,
            order=1
        )
        
        Menu.objects.create(
            title="Roa Over",
            url="over-roa-page",
            parent=waybill_check,
            order=2
        )
        
        # Productions
        productions = Menu.objects.create(
            title="Productions",
            icon="bx bx-fingerprint",
            order=6,
            allowed_group_names=["superadmin", "production"]
        )
        
        Menu.objects.create(
            title="Entry data",
            url="ore-entry-page",
            parent=productions,
            order=1
        )
        
        list_data = Menu.objects.create(
            title="List Data",
            parent=productions,
            order=2
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
            url="#",
            parent=productions,
            order=3
        )
        
        # Assay Data
        assay = Menu.objects.create(
            title="Assay Data",
            icon="bx bx-error",
            order=7,
            allowed_group_names=["superadmin", "lab"]
        )
        
        Menu.objects.create(
            title="Data mral",
            url="assay-mral-page",
            parent=assay,
            order=1
        )
        
        Menu.objects.create(
            title="Data roa",
            url="assay-roa-page",
            parent=assay,
            order=2
        )
        
        # Kategori Mining
        mining_category = Menu.objects.create(
            title="Mining",
            is_category=True,
            category_title="Mining",
            order=8
        )
        
        # Data Productions (Mining)
        mining_productions = Menu.objects.create(
            title="Data Productions",
            icon="bx bx-box",
            order=9,
            allowed_group_names=["superadmin", "mining"]
        )
        
        Menu.objects.create(
            title="Data Plan",
            url="mine-production-plan-page",
            parent=mining_productions,
            order=1
        )
        
        Menu.objects.create(
            title="Daily productions",
            url="mine-production-page",
            parent=mining_productions,
            order=2
        )
        
        # Forms
        forms = Menu.objects.create(
            title="Forms",
            icon="bx bx-file",
            order=10,
            allowed_group_names=["superadmin"]
        )
        
        Menu.objects.create(
            title="Form Quick",
            url="#",
            parent=forms,
            order=1
        )
        
        Menu.objects.create(
            title="List Data",
            url="#",
            parent=forms,
            order=2
        )
        
        # Configuration (Mining)
        mining_config = Menu.objects.create(
            title="Configuration",
            icon="bx bx-medal",
            order=11,
            allowed_group_names=["superadmin", "mining"]
        )
        
        Menu.objects.create(
            title="Truck Factors",
            url="mine-production-truck-factor-page",
            parent=mining_config,
            order=1
        )
        
        Menu.objects.create(
            title="Adjust volume",
            url="mine-production-volume-adjustment-page",
            parent=mining_config,
            order=2
        )

        # Kategori Selling
        selling_category = Menu.objects.create(
            title="Selling",
            is_category=True,
            category_title="Selling",
            order=12,
            allowed_group_names=["superadmin", "user"]
        )
        selling = Menu.objects.create(
            title="Selling Data",
            icon="bx bx-grid-alt",
            order=13,
            allowed_group_names=["superadmin", "admin-selling"]
        )

        Menu.objects.create(
            title="Daily Selling",
            url="#",
            parent=selling,
            order=1
        )
        Menu.objects.create(
            title="Selling Plan",
            url="#",
            parent=selling,
            order=2
        )
        Menu.objects.create(
            title="Samples Split",
            url="#",
            parent=selling,
            order=3
        )
        Menu.objects.create(
            title="Data Official",
            url="#",
            parent=selling,
            order=4
        )

        split_official = Menu.objects.create(
            title="Split Official",
            parent=selling,
            order=5
        )
        Menu.objects.create(
            title="Split mral",
            url="#",
            parent=split_official,
            order=1
        )
        Menu.objects.create(
            title="Split roa",
            url="#",
            parent=split_official,
            order=2
        )
       
        # Analytics
        analytics = Menu.objects.create(
            title="Analytics",
            icon="bx bx-layer",
            order=14,
            allowed_group_names=["superadmin", "admin-selling"]
        )
        Menu.objects.create(
            title="Daily Grade",
            url="#",
            parent=analytics,
            order=1
        )
        Menu.objects.create(
            title="Grade by code",
            url="#",
            parent=analytics,
            order=2
        )
        Menu.objects.create(
            title="Daily mral",
            url="#",
            parent=analytics,
            order=3
        )
        
        #Kategori Report &amp; Charts
        reporting = Menu.objects.create(
            title="Report &amp; Charts",
            is_category=True,
            category_title="Report",
            order=15,
            allowed_group_names=["superadmin", "user"]
        )
       
        achievements = Menu.objects.create(
            title="Achievements",
            icon="bx bx-table",
            order=16,
            allowed_group_names=["superadmin", "admin-selling"]
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
            title="By Sources",
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
            icon="bx bx-chart",
            order=17,
            allowed_group_names=["superadmin", "admin-selling"]
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
        # Finish Selling
        finish_selling = Menu.objects.create(
            title="Finish Selling",
            parent=inventory,
            order=5
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
            order=18,
            allowed_group_names=["superadmin", "admin-selling"]
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
            order=19,
            allowed_group_names=["superadmin", "admin-selling"]
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
            title="Charts samples(type)",
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

         #Kategori Setting
      
        # Kategory Settings
        settings = Menu.objects.create(
            title="Settings",
            is_category=True,
            category_title="Settings",
            order=20,
            allowed_group_names=["superadmin", "user"]
        )
       
        users = Menu.objects.create(
            title="Users",
            icon="bx bx-fingerprint",
            order=21,
            allowed_group_names=["superadmin", "admin-selling"]
        )

        Menu.objects.create(
            title="Users",
            url="user-page",
            parent=users,
            order=1
        )
        Menu.objects.create(
            title="Group",
            url="group-page",
            parent=users,
            order=2
        )
        Menu.objects.create(
            title="Permmissions",
            url="#",
            parent=users,
            order=3
        )
        #  Master
        master = Menu.objects.create(
            title="Master",
            icon="bx bx-store-alt",
            order=22,
            allowed_group_names=["superadmin", "admin-selling"]
        )

        Menu.objects.create(
            title="Block",
            url="block-page",
            parent=master,
            order=1
        )
        Menu.objects.create(
            title="Materials",
            url="material-page",
            parent=master,
            order=2
        )
        Menu.objects.create(
            title="Source area",
            url="source-page",
            parent=master,
            order=3
        )
        Menu.objects.create(
            title="Loading point",
            url="source-loading-point-page",
            parent=master,
            order=4
        )
        Menu.objects.create(
            title="Dumping point",
            url="source-dumping-point-page",
            parent=master,
            order=5
        )
        Menu.objects.create(
            title="Dome",
            url="source-dome-point-page",
            parent=master,
            order=6
        )
        Menu.objects.create(
            title="Mine units",
            url="mine-units-page",
            parent=master,
            order=7
        )
        Menu.objects.create(
            title="Sample method",
            url="sample-method-page",
            parent=master,
            order=8
        )
        Menu.objects.create(
            title="Sample type",
            url="sample-type-page",
            parent=master,
            order=9
        )
        Menu.objects.create(
            title="Sample type",
            url="sample-type-page",
            parent=master,
            order=10
        )
        Menu.objects.create(
            title="Mine geology",
            url="mine-geologies-pagee",
            parent=master,
            order=11
        )

        #  Configuration
        configuration = Menu.objects.create(
            title="Configuration",
            icon="bx bx-cog",
            order=23,
            allowed_group_names=["superadmin", "admin-selling"]
        )

        Menu.objects.create(
            title="Class ore",
            url="ore-class-page",
            parent=configuration,
            order=1
        )
        Menu.objects.create(
            title="Truck factors",
            url="ore-factors-page",
            parent=configuration,
            order=2
        )
        Menu.objects.create(
            title="Ore Adjustmet",
            url="ore-adjustment-page",
            parent=configuration,
            order=3
        )
        Menu.objects.create(
            title="Dome Close",
            url="dome-close-status-page",
            parent=configuration,
            order=4
        )
        Menu.objects.create(
            title="Dome finished",
            url="dome-finish-status-page",
            parent=configuration,
            order=5
        )
        Menu.objects.create(
            title="Merge dome",
            url="merge-dome-page",
            parent=configuration,
            order=6
        )
        Menu.objects.create(
            title="Merge stock",
            url="merge-stockpile-page",
            parent=configuration,
            order=7
        )
        
        #  Remove data by
        remove_data = Menu.objects.create(
            title="Remove data",
            icon="bx bx-bell",
            order=24,
            allowed_group_names=["superadmin", "admin-selling"]
        )

        Menu.objects.create(
            title="Waybill",
            url="remove-waybills-page",
            parent=remove_data,
            order=1
        )
        Menu.objects.create(
            title="Job mral",
            url="remove-mral-page",
            parent=remove_data,
            order=2
        )
        Menu.objects.create(
            title="Job roa",
            url="remove-roa-page",
            parent=remove_data,
            order=3
        )
        #  Task
        task = Menu.objects.create(
            title="Task",
            icon="bx bx-task",
            order=25,
            allowed_group_names=["superadmin", "admin-selling"]
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
            order=2
        )
        Menu.objects.create(
            title="Master task",
            url="task-table-page",
            parent=task,
            order=3
        )
      
        self.stdout.write(self.style.SUCCESS('Successfully created menu'))
