# hr/menu_data.py

from django.contrib.auth.models import Group

def get_menu_data():
    workflow_group, _ = Group.objects.get_or_create(name="Workflow")
    hr_group, _       = Group.objects.get_or_create(name="HR Management")  # Tambahkan group baru
    hr_employee, _    = Group.objects.get_or_create(name="HR Employee")  # Tambahkan group baru
    travel_group, _   = Group.objects.get_or_create(name="Admin Travel")  # Tambahkan group baru
    return [
        {
            "label": "Dashboard",
            "icon": "fa-home",
            "key": "dashboard",
            "dropdown": True,
            "groups": [workflow_group,hr_group,travel_group,hr_employee],
            "children": [
                {"label": "Quality", "key": "dashboard-travel", "url": "quality_home"},
                {"label": "Mining", "key": "dashboard-analyst", "url": "mining_home"}
            ]
        },
        {"section_title": "Geology"},
        {
            "label": "Samples",
            "icon": "fa-briefcase",
            "key": "samples-leave",
            "dropdown": True,
            "groups": [workflow_group],
            "children": [
                {"label": "Appovals", "key":  "workflow-approval", "url": "page-leave-list-approval"},
                {"label": "Delegation", "key": "workflow-delegation", "url": "delegation-page"},
            ]
        },
        {
            "label": "Waybills",
            "icon": "fa-users",
            "key": "leave-employee",
            "dropdown": True,
            "groups": [hr_employee],  # Bisa juga
            "children": [
                {"label": "Add  Leave", "key": "leave-employee-add", "url": "leave-user-create"},
                {"label": "Data Leave", "key": "leave-employee-data", "url": "leave-user"},
                {"label": "Data Travel", "key": "leave-employee-travel", "url": "page-travel"},
                {"label": "Data History", "key": "leave-employee-history", "url": "page-leave-balance"},
            ],
        },
        {"section_title": "Mining"},
        {
            "label": "Employee",
            "icon": "fa-users",
            "key": "employee",
            "dropdown": True,
            "groups": [hr_group],  # hanya untuk grup HR
            "children": [
                {"label": "Employee Data", "key": "employee-data", "url": "page_employee_list"}
            ]
        },
        {
            "label": "Leaves Manage",
            "icon": "fa-calendar",
            "key": "leave-manage",
            "dropdown": True,
            "groups": [hr_group],  # Bisa juga
            "children": [
                {"label": "Add Leave", "key": "leave-manage-add", "url": "leave-user-create"},
                {"label": "Data Leave", "key": "leave-manage-data", "url": "leave-user"},
                {"label": "Data Travel", "key": "leave-manage-travel", "url": "page-travel"},
                {"label": "Leave History", "key": "leave-manage-history", "url": "page-leave-balance"},
            ],
        },
        {
            "label": "Visitor Manage",
            "icon": "fa-bar-chart",
            "key": "visitor-manage",
            "dropdown": True,
            "groups": [hr_group],  # Bisa juga
            "children": [
                {"label": "Data Visitor", "key": "visitor-manage-data", "url": "visitor-page"},
                {"label": "Add Site Visit", "key" : "visitor-manage-add", "url": "site-visit-form"},
                {"label": "Data Site Visit", "key" : "visitor-manage-site-visit", "url": "visitor-page"},
            ],
        },
        {"section_title": "Selling Ore"},
        {
            "label": "Employee",
            "icon": "fa-users",
            "key": "employee",
            "dropdown": True,
            "groups": [hr_group],  # hanya untuk grup HR
            "children": [
                {"label": "Employee Data", "key": "employee-data", "url": "page_employee_list"}
            ]
        },
        {
            "label": "Leaves Manage",
            "icon": "fa-calendar",
            "key": "leave-manage",
            "dropdown": True,
            "groups": [hr_group],  # Bisa juga
            "children": [
                {"label": "Add Leave", "key": "leave-manage-add", "url": "leave-user-create"},
                {"label": "Data Leave", "key": "leave-manage-data", "url": "leave-user"},
                {"label": "Data Travel", "key": "leave-manage-travel", "url": "page-travel"},
                {"label": "Leave History", "key": "leave-manage-history", "url": "page-leave-balance"},
            ],
        },
        {
            "label": "Visitor Manage",
            "icon": "fa-bar-chart",
            "key": "visitor-manage",
            "dropdown": True,
            "groups": [hr_group],  # Bisa juga
            "children": [
                {"label": "Data Visitor", "key": "visitor-manage-data", "url": "visitor-page"},
                {"label": "Add Site Visit", "key" : "visitor-manage-add", "url": "site-visit-form"},
                {"label": "Data Site Visit", "key" : "visitor-manage-site-visit", "url": "visitor-page"},
            ],
        },
        {"section_title": "Report"},
         {
            "label": "Report",
            "icon": "fa-area-chart",
            "key": "report",
            "dropdown": True,
            "groups": [workflow_group],
            "children": [
                {"label": "List HRD", "key": "report-list", "url": "page-leave-list-approval"},
                {
                    "label": "HRD Report",
                    "key": "hrd-report-pages",
                    "url": None,
                    "children": [
                        {"label": "404", "key": "report-hrd-404", "url": "page-leave-list-approval"},
                        {"label": "500", "key": "report-hrd-500", "url": "page-leave-list-approval"},
                        {"label": "503", "key": "report-hrd-503", "url": "page-leave-list-approval"},
                    ]
                }
            ]
        },
        {"section_title": "Configuration"},
         {
            "label": "Master",
            "icon": "fa-area-chart",
            "key": "report",
            "dropdown": True,
            "groups": [workflow_group],
            "children": [
                {"label": "List HRD", "key": "report-list", "url": "page-leave-list-approval"},
                {
                    "label": "HRD Report",
                    "key": "hrd-report-pages",
                    "url": None,
                    "children": [
                        {"label": "404", "key": "report-hrd-404", "url": "page-leave-list-approval"},
                        {"label": "500", "key": "report-hrd-500", "url": "page-leave-list-approval"},
                        {"label": "503", "key": "report-hrd-503", "url": "page-leave-list-approval"},
                    ]
                }
            ]
        },
    ]
