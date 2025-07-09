from django.shortcuts import render

# utils/menu.py

menu_structure = [
    {
        "category": "Main",
        "title": "Dashboards",
        "icon": "bx bx-home",
        "order": 1,
        "groups": ["superadmin", "admin-geology"],
        "children": [
            {"title": "Geology", "url": "/dashboard/geology", "order": 1, "groups": ["admin-geology"]},
            {"title": "Analytics", "url": "/dashboard/analytics", "order": 2, "groups": ["admin-geology"]}
        ]
    },
    {
        "category": "Geology",
        "title": "Samples",
        "icon": "bx bx-file-blank",
        "order": 2,
        "groups": ["admin-geology"],
        "children": [
            {"title": "List Data", "url": "/samples/list", "order": 1, "groups": ["admin-geology"]},
            {
                "title": "From Entry", "order": 2, "groups": ["admin-geology"],
                "children": [
                    {"title": "Samples Qa", "url": "/samples/qa", "order": 1, "groups": ["admin-geology"]},
                    {"title": "Sample Selling", "url": "/samples/selling", "order": 2, "groups": ["admin-geology"]}
                ]
            },
            {
                "title": "Check Data", "order": 3, "groups": ["admin-geology"],
                "children": [
                    {"title": "No Relation PDS", "url": "/samples/check/no-relation", "order": 1, "groups": ["admin-geology"]},
                    {"title": "Pending to Lab", "url": "/samples/check/pending-lab", "order": 2, "groups": ["admin-geology"]}
                ]
            }
        ]
    },
    {
        "category": "Geology",
        "title": "Waybills",
        "icon": "bx bx-task",
        "order": 3,
        "groups": ["admin-geology"],
        "children": [
            {"title": "Entry Data", "url": "/waybills/entry", "order": 1, "groups": ["admin-geology"]},
            {"title": "List Data", "url": "/waybills/list", "order": 2, "groups": ["admin-geology"]},
            {
                "title": "Check Data", "order": 3, "groups": ["admin-geology"],
                "children": [
                    {"title": "Mral Over", "url": "/waybills/check/mral-over", "order": 1, "groups": ["admin-geology"]},
                    {"title": "Roa Over", "url": "/waybills/check/roa-over", "order": 2, "groups": ["admin-geology"]}
                ]
            }
        ]
    },
    {
        "category": "Geology",
        "title": "Productions",
        "icon": "bx bx-fingerprint",
        "order": 4,
        "groups": ["admin-geology", "superadmin"],
        "children": [
            {"title": "Entry data", "url": "/productions/entry", "order": 1, "groups": ["admin-geology"]},
            {
                "title": "List Data", "order": 2, "groups": ["admin-geology"],
                "children": [
                    {"title": "List Ore", "url": "/productions/list-ore", "order": 1, "groups": ["admin-geology"]},
                    {"title": "Details Ore", "url": "/productions/details-ore", "order": 2, "groups": ["admin-geology"]}
                ]
            },
            {"title": "Batch Status", "url": "/productions/batch-status", "order": 3, "groups": ["admin-geology"]}
        ]
    },
    {
        "category": "Geology",
        "title": "Assay Data",
        "icon": "bx bx-error",
        "order": 5,
        "groups": ["admin-geology"],
        "children": [
            {"title": "Data MRAL", "url": "/assay/mral", "order": 1, "groups": ["admin-geology"]},
            {"title": "Data ROA", "url": "/assay/roa", "order": 2, "groups": ["admin-geology"]}
        ]
    },
  
    {
    "category": "Mining",
    "title": "Data Productions",
    "icon": "bx bx-box",
    "order": 6,
    "groups": ["admin-mining"],
    "children": [
        {
            "title": "Data Plan",
            "url": "/mining/plan",
            "order": 1,
            "groups": ["admin-mining"]
        },
        {
            "title": "Daily Productions",
            "url": "/mining/daily",
            "order": 2,
            "groups": ["admin-mining"]
        }
    ]
    },
    {
        "category": "Mining",
        "title": "Forms",
        "icon": "bx bx-file",
        "order": 7,
        "groups": ["admin-mining"],
        "children": [
            {
                "title": "Form Quick",
                "url": "/mining/forms/quick",
                "order": 1,
                "groups": ["admin-mining"]
            },
            {
                "title": "List Data",
                "url": "/mining/forms/list",
                "order": 2,
                "groups": ["admin-mining"]
            }
        ]
    },
    {
        "category": "Mining",
        "title": "Configuration",
        "icon": "bx bx-medal",
        "order": 8,
        "groups": ["admin-mining"],
        "children": [
            {
                "title": "Truck Factors",
                "url": "/mining/config/truck-factors",
                "order": 1,
                "groups": ["admin-mining"]
            },
            {
                "title": "Adjust Volume",
                "url": "/mining/config/volume-adjustment",
                "order": 2,
                "groups": ["admin-mining"]
            }
        ]
    },
# Selling
    {
    "category": "Selling Ore",
    "title": "Selling",
    "icon": "bx bx-grid-alt",
    "order": 9,
    "groups": ["admin-selling"],
    "children": [
        {"title": "Daily Selling", "url": "/selling/daily", "order": 1, "groups": ["admin-selling"]},
        {"title": "Selling Plan", "url": "/selling/plan", "order": 2, "groups": ["admin-selling"]},
        {"title": "Samples Split", "url": "/selling/split", "order": 3, "groups": ["admin-selling"]},
        {"title": "Data Official", "url": "/selling/official", "order": 4, "groups": ["admin-selling"]},
        {
            "title": "Split Official",
            "order": 5,
            "groups": ["admin-selling"],
            "children": [
                {"title": "Data MRAL", "url": "/selling/split/mral", "order": 1, "groups": ["admin-selling"]},
                {"title": "Data ROA", "url": "/selling/split/roa", "order": 2, "groups": ["admin-selling"]},
                {"title": "Data by Range", "url": "/selling/split/range", "order": 3, "groups": ["admin-selling"]}
            ]
        }
    ]
    },
    {
        "category": "Selling Ore",
        "title": "Analytics",
        "icon": "bx bx-layer",
        "order": 10,
        "groups": ["admin-selling"],
        "children": [
            {"title": "Daily Grade", "url": "/selling/analytics/daily-grade", "order": 1, "groups": ["admin-selling"]},
            {"title": "Grade by Code", "url": "/selling/analytics/grade-by-code", "order": 2, "groups": ["admin-selling"]},
            {"title": "Daily MRAL", "url": "/selling/analytics/daily-mral", "order": 3, "groups": ["admin-selling"]}
        ]
    },
    {
        "category": "Report & Charts",
        "title": "Achievements",
        "icon": "bx bx-table",
        "order": 11,
        "groups": ["admin-geology"],
        "children": [
            {"title": "Data by MRAL", "url": "/achievement/mral", "order": 1, "groups": ["admin-geology"]},
            {"title": "Data by ROA", "url": "/achievement/roa", "order": 2, "groups": ["admin-geology"]},
            {
                "title": "By Stockpile", "order": 3, "groups": ["admin-geology"],
                "children": [
                    {"title": "Data MRAL", "url": "/achievement/stockpile/mral", "order": 1, "groups": ["admin-geology"]},
                    {"title": "Data ROA", "url": "/achievement/stockpile/roa", "order": 2, "groups": ["admin-geology"]}
                ]
            },
            {
                "title": "By Sources", "order": 4, "groups": ["admin-geology"],
                "children": [
                    {"title": "Data MRAL", "url": "/achievement/sources/mral", "order": 1, "groups": ["admin-geology"]},
                    {"title": "Data ROA", "url": "/achievement/sources/roa", "order": 2, "groups": ["admin-geology"]}
                ]
            },
            {
                "title": "Sources to Stock", "order": 5, "groups": ["admin-geology"],
                "children": [
                    {"title": "Data MRAL", "url": "/achievement/to-stockpile/mral", "order": 1, "groups": ["admin-geology"]},
                    {"title": "Data ROA", "url": "/achievement/to-stockpile/roa", "order": 2, "groups": ["admin-geology"]}
                ]
            },
            {
                "title": "Sources to Dome", "order": 6, "groups": ["admin-geology"],
                "children": [
                    {"title": "Data ROA", "url": "/achievement/to-dome/roa", "order": 1, "groups": ["admin-geology"]}
                ]
            }
        ]
    },
    {
        "category": "Report & Charts",
        "title": "Inventory Stock",
        "icon": "bx bx-chart",
        "order": 12,
        "groups": ["admin-geology"],
        "children": [
            {"title": "Data All", "url": "/inventory/all", "order": 1, "groups": ["admin-geology"]},
            {"title": "Limonite", "url": "/inventory/hpal", "order": 2, "groups": ["admin-geology"]},
            {"title": "Saprolite", "url": "/inventory/rkef", "order": 3, "groups": ["admin-geology"]},
            {"title": "By Stockpile", "url": "/inventory/stockpile", "order": 4, "groups": ["admin-geology"]},
            {
                "title": "Finish Selling", "order": 5, "groups": ["admin-geology"],
                "children": [
                    {"title": "Data All", "url": "/inventory/finished", "order": 1, "groups": ["admin-geology"]},
                    {"title": "By Stockpile", "url": "/inventory/finished/stockpile", "order": 2, "groups": ["admin-geology"]}
                ]
            }
        ]
    },
    {
        "category": "Report & Charts",
        "title": "Geology",
        "icon": "bx bx-map",
        "order": 13,
        "groups": ["admin-geology"],
        "children": [
            {"title": "Data Samples", "url": "/report/samples", "order": 1, "groups": ["admin-geology"]},
            {
                "title": "Expect-MRAL", "order": 2, "groups": ["admin-geology"],
                "children": [
                    {"title": "Data", "url": "/report/expect-mral/data", "order": 1, "groups": ["admin-geology"]},
                    {"title": "Chart", "url": "/report/expect-mral/chart", "order": 2, "groups": ["admin-geology"]}
                ]
            },
            {
                "title": "Expect-ROA", "order": 3, "groups": ["admin-geology"],
                "children": [
                    {"title": "Data", "url": "/report/expect-roa/data", "order": 1, "groups": ["admin-geology"]},
                    {"title": "Chart", "url": "/report/expect-roa/chart", "order": 2, "groups": ["admin-geology"]}
                ]
            }
        ]
    },
     {
        "category": "Report & Charts",
        "title": "Quality Assurance",
        "icon": "bx bx-bar-chart-square",
        "order": 14,
        "groups": ["admin-geology"],
        "children": [
            {
                "title": "Sample dup-roa", "order": 1, "groups": ["admin-geology"],
                "children": [
                    {"title": "List data", "url": "/qa/dup-roa/list", "order": 1, "groups": ["admin-geology"]},
                    {"title": "Scatter Charts", "url": "/qa/dup-roa/scatter", "order": 2, "groups": ["admin-geology"]},
                    {"title": "Sample wet", "url": "/qa/dup-roa/wet", "order": 3, "groups": ["admin-geology"]}
                ]
            },
            {"title": "CRM Certificate", "url": "/qa/crm", "order": 2, "groups": ["admin-geology"]},
            {
                "title": "CRM MRAL", "order": 3, "groups": ["admin-geology"],
                "children": [
                    {"title": "Data", "url": "/qa/crm-mral/data", "order": 1, "groups": ["admin-geology"]},
                    {"title": "Charts", "url": "/qa/crm-mral/charts", "order": 2, "groups": ["admin-geology"]}
                ]
            },
            {
                "title": "CRM ROA", "order": 4, "groups": ["admin-geology"],
                "children": [
                    {"title": "Data", "url": "/qa/crm-roa/data", "order": 1, "groups": ["admin-geology"]},
                    {"title": "Charts", "url": "/qa/crm-roa/charts", "order": 2, "groups": ["admin-geology"]}
                ]
            },
            {
                "title": "MRAL vs ROA", "order": 5, "groups": ["admin-geology"],
                "children": [
                    {"title": "Data", "url": "/qa/compare-mral-roa/data", "order": 1, "groups": ["admin-geology"]},
                    {"title": "Wet Charts", "url": "/qa/compare-mral-roa/wet", "order": 2, "groups": ["admin-geology"]},
                    {"title": "Scatter Charts", "url": "/qa/compare-mral-roa/scatter", "order": 3, "groups": ["admin-geology"]}
                ]
            },
            {
                "title": "Laboratory (tat)", "order": 6, "groups": ["admin-geology"],
                "children": [
                    {"title": "Sample order", "url": "/qa/tat/orders", "order": 1, "groups": ["admin-geology"]},
                    {"title": "Charts samples(type)", "url": "/qa/tat/type", "order": 2, "groups": ["admin-geology"]},
                    {"title": "By Week Charts", "url": "/qa/tat/week", "order": 3, "groups": ["admin-geology"]},
                    {"title": "Last Week Charts", "url": "/qa/tat/last-week", "order": 4, "groups": ["admin-geology"]}
                ]
            },
            {"title": "Plan Grade", "url": "/qa/plan-grade", "order": 7, "groups": ["admin-geology"]}
        ]
    },
    {
        "category": "Settings",
        "title": "Users",
        "icon": "bx bx-fingerprint",
        "order": 15,
        "groups": ["superadmin"],
        "children": [
            {"title": "Users", "url": "/settings/users", "order": 1, "groups": ["superadmin"]},
            {"title": "Group", "url": "/settings/groups", "order": 2, "groups": ["superadmin"]},
            {"title": "Permissions", "url": "/settings/permissions", "order": 3, "groups": ["superadmin"]}
        ]
    },
    {
        "category": "Settings",
        "title": "Master",
        "icon": "bx bx-store-alt",
        "order": 16,
        "groups": ["superadmin"],
        "children": [
            {"title": "Block", "url": "/settings/master/block", "order": 1, "groups": ["superadmin"]},
            {"title": "Material", "url": "/settings/master/material", "order": 2, "groups": ["superadmin"]},
            {"title": "Dome", "url": "/settings/master/dome", "order": 3, "groups": ["superadmin"]},
            {"title": "Dumping Point", "url": "/settings/master/dumping", "order": 4, "groups": ["superadmin"]},
            {"title": "Loading Point", "url": "/settings/master/loading", "order": 5, "groups": ["superadmin"]},
            {"title": "Sources Area", "url": "/settings/master/sources", "order": 6, "groups": ["superadmin"]},
            {"title": "Mine Units", "url": "/settings/master/units", "order": 7, "groups": ["superadmin"]},
            {"title": "Sample Method", "url": "/settings/master/sample-method", "order": 8, "groups": ["superadmin"]},
            {"title": "Sample Type", "url": "/settings/master/sample-type", "order": 9, "groups": ["superadmin"]},
            {"title": "Mine Geology", "url": "/settings/master/geology", "order": 10, "groups": ["superadmin"]}
        ]
    },
    {
        "category": "Settings",
        "title": "Configuration",
        "icon": "bx bx-cog",
        "order": 17,
        "groups": ["superadmin"],
        "children": [
            {"title": "Class Ore", "url": "/settings/config/class-ore", "order": 1, "groups": ["superadmin"]},
            {"title": "Truck Factors", "url": "/settings/config/truck-factors", "order": 2, "groups": ["superadmin"]},
            {"title": "Volume Adjust.", "url": "/settings/config/volume-adjust", "order": 3, "groups": ["superadmin"]},
            {"title": "Dome Close", "url": "/settings/config/dome-close", "order": 4, "groups": ["superadmin"]},
            {"title": "Dome Finished", "url": "/settings/config/dome-finished", "order": 5, "groups": ["superadmin"]},
            {"title": "Merge Dome", "url": "/settings/config/merge-dome", "order": 6, "groups": ["superadmin"]},
            {"title": "Merge Stock", "url": "/settings/config/merge-stock", "order": 7, "groups": ["superadmin"]}
        ]
    },
    {
        "category": "Settings",
        "title": "Remove Data",
        "icon": "bx bx-bell",
        "order": 18,
        "groups": ["superadmin"],
        "children": [
            {"title": "Waybill", "url": "/settings/remove/waybill", "order": 1, "groups": ["superadmin"]},
            {"title": "Mral Job", "url": "/settings/remove/mral", "order": 2, "groups": ["superadmin"]},
            {"title": "Roa Job", "url": "/settings/remove/roa", "order": 3, "groups": ["superadmin"]}
        ]
    },
    {
        "category": "Settings",
        "title": "Task",
        "icon": "bx bx-task",
        "order": 19,
        "groups": ["superadmin"],
        "children": [
            {"title": "Import Data", "url": "/settings/task/import", "order": 1, "groups": ["superadmin"]},
            {"title": "Template Excel", "url": "/settings/task/template", "order": 2, "groups": ["superadmin"]},
            {"title": "Master Task", "url": "/settings/task/master", "order": 3, "groups": ["superadmin"]}
        ]
    }


]
