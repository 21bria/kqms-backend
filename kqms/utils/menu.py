from django.shortcuts import render

# utils/menu.py

def get_menu_items():
    return [
        {"section_title": "Apps"},
        {
            "label": "Workflow",
            "icon": "fa-briefcase",
            "key": "workflow",
            "dropdown": True,
             "children": [
                  
                    {
                        "label": "List",
                        "url": "page-leave-list-approval",
                    },

                      {
                        "label": "Error Pages",
                        "url": None,
                        "submenu": [
                            {"label": "404", "url": "page-leave-list-approval"},
                            {"label": "500", "url": "page-leave-list-approval"},
                            {"label": "503", "url": "page-leave-list-approval"},
                        ],
                    },
                ]
        },
        {
            "label": "Calendar",
            "icon": "fa-calendar",
            "key": "calendar",
            "dropdown": False,
            "url": "#"
        },
        {"section_title": "HR Management"},
        {
            "label": "Employee",
            "icon": "fa-users",
            "key": "employee",
            "dropdown": True,
            "children": [
                {"label": "Employee Data", "url": "page_employee_list"},
            ]
        },
        {
            "label": "Leaves Manage",
            "icon": "fa-calendar",
            "key": "leaves_manage",
            "dropdown": True,
            "children": [
                {"label": "Add Leave", "url": "leave-user-create"},
                {"label": "Data Leave", "url": "leave-user"},
                {"label": "Leaves History", "url": "page-leave-balance"},
            ]
        },
    ]

