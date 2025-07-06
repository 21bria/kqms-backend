# # views.py
# import logging
# from django.http import JsonResponse
# from django.db import connections, DatabaseError
# import pandas as pd
# from datetime import datetime, timedelta
# from ....utils.utils import validate_month,validate_year
# from ....models.ore_productions_model import OreProductions
# import itertools
# from itertools import accumulate
# from datetime import timedelta
# from django.utils.timezone import now
# logger = logging.getLogger(__name__) 
# from ....utils.db_utils import get_db_vendor

#  # Memanggil fungsi utility
# db_vendor = get_db_vendor('kqms_db')
# import json

# def build_filter_clause(filter_type, year, month, week, date, date_start, date_end):
#     where_actual = "1=1"
#     where_plan   = "1=1"
#     params = []

#     if filter_type == 'daily' and date:
#         group_actual = "DATE(date_production)"
#         group_plan = "DATE(date_plan)"
#         where_actual += " AND DATE(date_production) = %s"
#         where_plan += " AND DATE(date_plan) = %s"
#         params += [date, date]

#     elif filter_type == 'weekly' and week:
#         group_actual = "TO_CHAR(date_production, 'IYYY-IW')"
#         group_plan   = "TO_CHAR(date_plan, 'IYYY-IW')"
#         where_actual += " AND TO_CHAR(date_production, 'IYYY-IW') = %s"
#         where_plan += " AND TO_CHAR(date_plan, 'IYYY-IW') = %s"
#         params += [week, week]

#     elif filter_type == 'monthly' and year and month:
#         group_actual = "TO_CHAR(date_production, 'YYYY-MM')"
#         group_plan = "TO_CHAR(date_plan, 'YYYY-MM')"
#         where_actual += " AND EXTRACT(YEAR FROM date_production) = %s AND EXTRACT(MONTH FROM date_production) = %s"
#         where_plan += " AND EXTRACT(YEAR FROM date_plan) = %s AND EXTRACT(MONTH FROM date_plan) = %s"
#         params += [year, month, year, month]

#     elif filter_type == 'yearly' and year:
#         group_actual = "EXTRACT(YEAR FROM date_production)::int"
#         group_plan = "EXTRACT(YEAR FROM date_plan)::int"
#         where_actual += " AND EXTRACT(YEAR FROM date_production) = %s"
#         where_plan += " AND EXTRACT(YEAR FROM date_plan) = %s"
#         params += [year, year]

#     elif filter_type == 'range' and date_start and date_end:
#         group_actual = "DATE(date_production)"
#         group_plan = "DATE(date_plan)"
#         where_actual += " AND date_production BETWEEN %s AND %s"
#         where_plan += " AND date_plan BETWEEN %s AND %s"
#         params += [date_start, date_end, date_start, date_end]

#     else:  # filter_type == 'all' atau tidak valid
#         group_actual = "EXTRACT(YEAR FROM date_production)::int"
#         group_plan   = "EXTRACT(YEAR FROM date_plan)::int"

#     return where_actual, where_plan, group_actual, group_plan, params


# # Project to Date Ore
# # def summary_ore(request):
# #     try:
# #         if db_vendor == 'postgresql':
# #             query = """
# #                 SELECT 
# #                     COALESCE(ROUND(SUM(CASE WHEN stockpile != 'Temp-Rompile_KM09' THEN tonnage ELSE 0 END)::numeric, 2), 0) AS total,
# #                     COALESCE(ROUND(SUM(CASE WHEN nama_material = 'LIM' THEN tonnage ELSE 0 END)::numeric, 2), 0) AS total_lim,
# #                     COALESCE(ROUND(SUM(CASE WHEN nama_material = 'SAP' AND stockpile != 'Temp-Rompile_KM09' THEN tonnage ELSE 0 END)::numeric, 2), 0) AS total_sap
# #                 FROM ore_production
# #                 """
# #         elif db_vendor in ['mssql', 'microsoft','mysql']:
# #             query = """
# #                 SELECT
# #                     COALESCE(ROUND(SUM(CASE WHEN stockpile!= 'Temp-Rompile_KM09' THEN tonnage ELSE 0 END), 2), 0) AS total,
# #                     COALESCE(ROUND(SUM(CASE WHEN nama_material = 'LIM' THEN tonnage ELSE 0 END), 2), 0) AS total_lim,
# #                     COALESCE(ROUND(SUM(CASE WHEN nama_material = 'SAP' AND stockpile != 'Temp-Rompile_KM09' THEN tonnage ELSE 0 END), 2), 0) AS total_sap
# #                 FROM ore_production
# #             """
# #         else:
# #             raise ValueError("Unsupported database vendor.")  
# #         # Use the correct database connection
# #         with connections['kqms_db'].cursor() as cursor:
# #             cursor.execute(query)
# #             data = cursor.fetchall()

# #         total_ore = [entry[0] for entry in data]
# #         data_hpal = [entry[1] for entry in data]
# #         data_rkef = [entry[2] for entry in data]

# #         return JsonResponse({
# #             'data_hpal': data_hpal,
# #             'data_rkef': data_rkef,
# #             'total_ore': total_ore,
# #         })

# #     except DatabaseError as e:
# #         logger.error(f"Database query failed: {e}")
# #         return JsonResponse({'error': str(e)}, status=500) 

# def summary_ore(request):
#     try:
#         if db_vendor == 'postgresql':
#             query = """
#                 SELECT 
#                     SUM(CASE WHEN nama_material IN ('LGLO', 'MGLO', 'HGLO','LGSO', 'MGSO', 'HGSO') THEN tonnage ELSE 0 END)::numeric  AS total,
#                     SUM(CASE WHEN nama_material IN ('LGLO', 'MGLO', 'HGLO') THEN tonnage ELSE 0 END)::numeric AS limonite,
#                     SUM(CASE WHEN nama_material IN ('LGSO', 'MGSO', 'HGSO') THEN tonnage ELSE 0 END)::numeric AS saprolite
#                 FROM mine_productions
#                 """
#         else:
#             raise ValueError("Unsupported database vendor.")  
#         # Use the correct database connection
#         with connections['kqms_db'].cursor() as cursor:
#             cursor.execute(query)
#             data = cursor.fetchall()

#         total_ore = [entry[0] for entry in data]
#         data_hpal = [entry[1] for entry in data]
#         data_rkef = [entry[2] for entry in data]

#         return JsonResponse({
#             'data_hpal': data_hpal,
#             'data_rkef': data_rkef,
#             'total_ore': total_ore,
#         })

#     except DatabaseError as e:
#         logger.error(f"Database query failed: {e}")
#         return JsonResponse({'error': str(e)}, status=500) 
      
# def summary_mines(request):
#     try:
#         if db_vendor == 'postgresql':
#             query = """
#                SELECT 
#                     ROUND(COALESCE(SUM(CASE WHEN nama_material = 'Top Soil' THEN tonnage ELSE 0 END), 0)::numeric, 2) AS "TopSoil",
#                     ROUND(COALESCE(SUM(CASE WHEN nama_material = 'Waste' THEN tonnage ELSE 0 END), 0)::numeric, 2) AS "Waste",
#                     ROUND(COALESCE(SUM(CASE WHEN nama_material = 'OB' THEN tonnage ELSE 0 END), 0)::numeric, 2) AS "OB",
#                     ROUND(COALESCE(SUM(CASE WHEN nama_material = 'Quarry' THEN tonnage ELSE 0 END), 0)::numeric, 2) AS "Quarry",
#                     ROUND(COALESCE(SUM(CASE WHEN nama_material = 'Ballast' THEN tonnage ELSE 0 END), 0)::numeric, 2) AS "Ballast",
#                     ROUND(COALESCE(SUM(CASE WHEN nama_material = 'Biomass' THEN tonnage ELSE 0 END), 0)::numeric, 2) AS "Biomass"
#                 FROM mine_productions
#                 """
#         else:
#             raise ValueError("Unsupported database vendor.")  
#         # Use the correct database connection
#         with connections['kqms_db'].cursor() as cursor:
#             cursor.execute(query)
#             data = cursor.fetchall()

#         data_topsoil = [entry[0] for entry in data]
#         data_waste   = [entry[1] for entry in data]
#         data_ob      = [entry[2] for entry in data]
#         data_quarry  = [entry[3] for entry in data]
#         data_ballast = [entry[4] for entry in data]
#         data_biomass = [entry[5] for entry in data]

#         # Tambahkan data_orders: jumlahkan  ob + quarry + ballast + biomass
#         data_orders = [entry[2] + entry[3] + entry[4] + entry[5] for entry in data]

#         return JsonResponse({
#             'data_topsoil'  : data_topsoil,
#             'data_waste'    : data_waste,
#             'data_ob'       : data_ob,
#             'data_ballast'  : data_ballast,
#             'data_quarry'   : data_quarry,
#             'data_biomass'  : data_biomass,
#             'data_orders'   : data_orders,
#         })
#     except DatabaseError as e:
#         logger.error(f"Database query failed: {e}")
#         return JsonResponse({'error': str(e)}, status=500)    

# # For Detail All
# def get_chart_mines(request):
#     filter_type  = request.GET.get('filter_type', 'all')
#     filter_year  = request.GET.get('filter_year')
#     filter_month = request.GET.get('filter_month')
#     filter_week  = request.GET.get('filter_week')
#     filter_date  = request.GET.get('filter_date')
#     date_start   = request.GET.get('date_start')
#     date_end     = request.GET.get('date_end')

#     if db_vendor != 'postgresql':
#         return JsonResponse({'error': 'Unsupported DB'}, status=400)

#      # Panggil fungsi untuk membentuk klausa WHERE dan GROUP BY
#     where_actual, where_plan, group_actual, group_plan, params = build_filter_clause(
#         filter_type, filter_year, filter_month, filter_week, filter_date, date_start, date_end
#     )

#     query = f"""
#         WITH actual AS (
#             SELECT
#                 {group_actual} AS periode,
#                 SUM(CASE WHEN nama_material = 'Top Soil' THEN tonnage ELSE 0 END)::numeric AS topsoil,
#                 SUM(CASE WHEN nama_material = 'OB' THEN tonnage ELSE 0 END)::numeric AS ob,
#                 SUM(CASE WHEN nama_material = 'Waste' THEN tonnage ELSE 0 END)::numeric AS waste,
#                 SUM(CASE WHEN nama_material = 'Quarry' THEN tonnage ELSE 0 END)::numeric AS quarry,
#                 SUM(CASE WHEN nama_material = 'Ballast' THEN tonnage ELSE 0 END)::numeric AS ballast,
#                 SUM(CASE WHEN nama_material = 'Biomass' THEN tonnage ELSE 0 END)::numeric AS biomass,
#                 SUM(CASE WHEN nama_material = 'LGLO' THEN tonnage ELSE 0 END)::numeric AS lglo,
#                 SUM(CASE WHEN nama_material = 'MGLO' THEN tonnage ELSE 0 END)::numeric AS mglo,
#                 SUM(CASE WHEN nama_material = 'HGLO' THEN tonnage ELSE 0 END)::numeric AS hglo,
#                 SUM(CASE WHEN nama_material = 'MWS' THEN tonnage ELSE 0 END)::numeric AS mws,
#                 SUM(CASE WHEN nama_material = 'LGSO' THEN tonnage ELSE 0 END)::numeric AS lgso,
#                 SUM(CASE WHEN nama_material = 'MGSO' THEN tonnage ELSE 0 END)::numeric AS mgso,
#                 SUM(CASE WHEN nama_material = 'HGSO' THEN tonnage ELSE 0 END)::numeric AS hgso
#             FROM mine_productions
#             WHERE {where_actual}
#             GROUP BY {group_actual}
#         ),
#         plan AS (
#             SELECT
#                 {group_plan} AS periode,
#                 SUM(topsoil)::numeric AS topsoil_plan,
#                 SUM(ob)::numeric AS ob_plan,
#                 SUM(waste)::numeric AS waste_plan,
#                 SUM(quarry)::numeric AS quarry_plan,
#                 SUM(ballast)::numeric AS ballast_plan,
#                 SUM(biomass)::numeric AS biomass_plan,
#                 SUM(lglo)::numeric AS lglo_plan,
#                 SUM(mglo)::numeric AS mglo_plan,
#                 SUM(hglo)::numeric AS hglo_plan,
#                 SUM(mws)::numeric AS mws_plan,
#                 SUM(lgso)::numeric AS lgso_plan,
#                 SUM(mgso)::numeric AS mgso_plan,
#                 SUM(hgso)::numeric AS hgso_plan
#             FROM plan_productions
#             WHERE {where_plan}
#             GROUP BY {group_plan}
#         )
#         SELECT
#             COALESCE(a.periode, p.periode) AS periode,
#             ROUND(COALESCE(a.topsoil, 0), 2) AS topsoil,
#             ROUND(COALESCE(p.topsoil_plan, 0), 2) AS topsoil_plan,
#             ROUND(COALESCE(a.ob, 0), 2) AS ob,
#             ROUND(COALESCE(p.ob_plan, 0), 2) AS ob_plan,
#             ROUND(COALESCE(a.waste, 0), 2) AS waste,
#             ROUND(COALESCE(p.waste_plan, 0), 2) AS waste_plan,
#             ROUND(COALESCE(a.quarry, 0), 2) AS quarry,
#             ROUND(COALESCE(p.quarry_plan, 0), 2) AS quarry_plan,
#             ROUND(COALESCE(a.ballast, 0), 2) AS ballast,
#             ROUND(COALESCE(p.ballast_plan, 0), 2) AS ballast_plan,
#             ROUND(COALESCE(a.biomass, 0), 2) AS biomass,
#             ROUND(COALESCE(p.biomass_plan, 0), 2) AS biomass_plan,
#             ROUND(COALESCE(a.lglo, 0), 2) AS lglo,
#             ROUND(COALESCE(p.lglo_plan, 0), 2) AS lglo_plan,
#             ROUND(COALESCE(a.mglo, 0), 2) AS mglo,
#             ROUND(COALESCE(p.mglo_plan, 0), 2) AS mglo_plan,
#             ROUND(COALESCE(a.hglo, 0), 2) AS hglo,
#             ROUND(COALESCE(p.hglo_plan, 0), 2) AS hglo_plan,
#             ROUND(COALESCE(a.mws, 0), 2) AS mws,
#             ROUND(COALESCE(p.mws_plan, 0), 2) AS mws_plan,
#             ROUND(COALESCE(a.lgso, 0), 2) AS lgso,
#             ROUND(COALESCE(p.lgso_plan, 0), 2) AS lgso_plan,
#             ROUND(COALESCE(a.mgso, 0), 2) AS mgso,
#             ROUND(COALESCE(p.mgso_plan, 0), 2) AS mgso_plan,
#             ROUND(COALESCE(a.hgso, 0), 2) AS hgso,
#             ROUND(COALESCE(p.hgso_plan, 0), 2) AS hgso_plan
#         FROM actual a
#         FULL OUTER JOIN plan p ON a.periode = p.periode
#         ORDER BY periode
#     """

#     try:
#         with connections['kqms_db'].cursor() as cursor:
#             cursor.execute(query, params)
#             data = cursor.fetchall()

#         df = pd.DataFrame(data, columns=[
#             'periode', 'topsoil', 'topsoil_plan',
#             'ob', 'ob_plan', 'waste', 'waste_plan', 'quarry', 'quarry_plan',
#             'ballast', 'ballast_plan', 'biomass', 'biomass_plan',
#             'lglo', 'lglo_plan', 'mglo', 'mglo_plan', 'hglo', 'hglo_plan',
#             'mws', 'mws_plan', 'lgso', 'lgso_plan', 'mgso', 'mgso_plan', 'hgso', 'hgso_plan'
#         ])

#         ore_cols = ['lglo', 'mglo', 'hglo', 'lgso', 'mgso', 'hgso', 'mws']
#         lim_cols = ['lglo', 'mglo', 'hglo']
#         sap_cols = ['lgso', 'mgso', 'hgso', 'mws']
#         non_ore_cols = ['topsoil', 'ob', 'waste', 'quarry', 'ballast', 'biomass']
#         ore_plan_cols = [f + '_plan' for f in ore_cols]
#         lim_plan_cols = [f + '_plan' for f in lim_cols]
#         sap_plan_cols = [f + '_plan' for f in sap_cols]
#         non_ore_plan_cols = [f + '_plan' for f in non_ore_cols]

#         df['total_ore'] = df[ore_cols].sum(axis=1)
#         df['total_ore_plan'] = df[ore_plan_cols].sum(axis=1)
#         df['total_limonite'] = df[lim_cols].sum(axis=1)
#         df['total_limonite_plan'] = df[lim_plan_cols].sum(axis=1)
#         df['total_saprolite'] = df[sap_cols].sum(axis=1)
#         df['total_saprolite_plan'] = df[sap_plan_cols].sum(axis=1)
#         df['total_non_ore'] = df[non_ore_cols].sum(axis=1)
#         df['total_non_ore_plan'] = df[non_ore_plan_cols].sum(axis=1)

#         df['total_actual'] = df['total_ore'] + df['total_non_ore']
#         df['total_plan']   = df['total_ore_plan'] + df['total_non_ore_plan']

#         df['achievement'] = df.apply(lambda r: round((r['total_actual'] / r['total_plan'] * 100), 2) if r['total_plan'] > 0 else 0, axis=1)

#         total_summary = {
#             'total_ore': round(df['total_ore'].sum(), 2),
#             'total_ore_plan': round(df['total_ore_plan'].sum(), 2),
#             'total_limonite': round(df['total_limonite'].sum(), 2),
#             'total_limonite_plan': round(df['total_limonite_plan'].sum(), 2),
#             'total_saprolite': round(df['total_saprolite'].sum(), 2),
#             'total_saprolite_plan': round(df['total_saprolite_plan'].sum(), 2),
#             'total_non_ore': round(df['total_non_ore'].sum(), 2),
#             'total_non_ore_plan': round(df['total_non_ore_plan'].sum(), 2),
#             'total_actual': round(df['total_actual'].sum(), 2),
#             'total_plan': round(df['total_plan'].sum(), 2),
#             'achievement': round(df['achievement'].mean(), 2)
#         }

#         return JsonResponse({
#             'x_data': df['periode'].tolist(),
#             'total_ore': df['total_ore'].tolist(),
#             'total_ore_plan': df['total_ore_plan'].tolist(),
#             'total_limonite': df['total_limonite'].tolist(),
#             'total_limonite_plan': df['total_limonite_plan'].tolist(),
#             'total_saprolite': df['total_saprolite'].tolist(),
#             'total_saprolite_plan': df['total_saprolite_plan'].tolist(),
#             'total_non_ore': df['total_non_ore'].tolist(),
#             'total_non_ore_plan': df['total_non_ore_plan'].tolist(),
#             'total_actual': df['total_actual'].tolist(),
#             'total_plan': df['total_plan'].tolist(),
#             'achievement': df['achievement'].tolist(),
#             'summary': total_summary
#         }, safe=False)

#     except DatabaseError as e:
#         return JsonResponse({'error': str(e)}, status=500)

# def get_chart_ore(request):
#     filter_type  = request.GET.get('filter_type')
#     filter_year  = request.GET.get('filter_year')
#     filter_month = request.GET.get('filter_month')
#     filter_week  = request.GET.get('filter_week')
#     filter_date  = request.GET.get('filter_date')
#     date_start   = request.GET.get('date_start')
#     date_end     = request.GET.get('date_end')

#     if db_vendor != 'postgresql':
#         return JsonResponse({'error': 'Unsupported DB'}, status=400)

#     # Pakai helper universal
#     where_actual, where_plan, group_actual, group_plan, params = build_filter_clause(
#         filter_type, filter_year, filter_month, filter_week, filter_date, date_start, date_end
#     )

#     query = f"""
#         WITH actual AS (
#             SELECT
#                 {group_actual} AS periode,
#                 SUM(CASE WHEN nama_material = 'LGLO' THEN tonnage ELSE 0 END)::numeric AS lglo,
#                 SUM(CASE WHEN nama_material = 'MGLO' THEN tonnage ELSE 0 END)::numeric AS mglo,
#                 SUM(CASE WHEN nama_material = 'HGLO' THEN tonnage ELSE 0 END)::numeric AS hglo,
#                 SUM(CASE WHEN nama_material = 'MWS' THEN tonnage ELSE 0 END)::numeric AS mws,
#                 SUM(CASE WHEN nama_material = 'LGSO' THEN tonnage ELSE 0 END)::numeric AS lgso,
#                 SUM(CASE WHEN nama_material = 'MGSO' THEN tonnage ELSE 0 END)::numeric AS mgso,
#                 SUM(CASE WHEN nama_material = 'HGSO' THEN tonnage ELSE 0 END)::numeric AS hgso
#             FROM mine_productions
#             WHERE {where_actual}
#             GROUP BY {group_actual}
#         ),
#         plan AS (
#             SELECT
#                 {group_plan} AS periode,
#                 SUM(lglo)::numeric AS lglo_plan,
#                 SUM(mglo)::numeric AS mglo_plan,
#                 SUM(hglo)::numeric AS hglo_plan,
#                 SUM(mws)::numeric AS mws_plan,
#                 SUM(lgso)::numeric AS lgso_plan,
#                 SUM(mgso)::numeric AS mgso_plan,
#                 SUM(hgso)::numeric AS hgso_plan
#             FROM plan_productions
#             WHERE {where_plan}
#             GROUP BY {group_plan}
#         )
#         SELECT
#             COALESCE(a.periode, p.periode) AS periode,
#             ROUND(COALESCE(a.lglo, 0), 2) AS lglo,
#             ROUND(COALESCE(p.lglo_plan, 0), 2) AS lglo_plan,
#             ROUND(CASE WHEN p.lglo_plan > 0 THEN (a.lglo * 100.0 / p.lglo_plan)::numeric ELSE 0 END, 2) AS lglo_ach,
#             ROUND(COALESCE(a.mglo, 0), 2) AS mglo,
#             ROUND(COALESCE(p.mglo_plan, 0), 2) AS mglo_plan,
#             ROUND(CASE WHEN p.mglo_plan > 0 THEN (a.mglo * 100.0 / p.mglo_plan)::numeric ELSE 0 END, 2) AS mglo_ach,
#             ROUND(COALESCE(a.hglo, 0), 2) AS hglo,
#             ROUND(COALESCE(p.hglo_plan, 0), 2) AS hglo_plan,
#             ROUND(CASE WHEN p.hglo_plan > 0 THEN (a.hglo * 100.0 / p.hglo_plan)::numeric ELSE 0 END, 2) AS hglo_ach,
#             ROUND(COALESCE(a.mws, 0), 2) AS mws,
#             ROUND(COALESCE(p.mws_plan, 0), 2) AS mws_plan,
#             ROUND(CASE WHEN p.mws_plan > 0 THEN (a.mws * 100.0 / p.mws_plan)::numeric ELSE 0 END, 2) AS mws_ach,
#             ROUND(COALESCE(a.lgso, 0), 2) AS lgso,
#             ROUND(COALESCE(p.lgso_plan, 0), 2) AS lgso_plan,
#             ROUND(CASE WHEN p.lgso_plan > 0 THEN (a.lgso * 100.0 / p.lgso_plan)::numeric ELSE 0 END, 2) AS lgso_ach,
#             ROUND(COALESCE(a.mgso, 0), 2) AS mgso,
#             ROUND(COALESCE(p.mgso_plan, 0), 2) AS mgso_plan,
#             ROUND(CASE WHEN p.mgso_plan > 0 THEN (a.mgso * 100.0 / p.mgso_plan)::numeric ELSE 0 END, 2) AS mgso_ach,
#             ROUND(COALESCE(a.hgso, 0), 2) AS hgso,
#             ROUND(COALESCE(p.hgso_plan, 0), 2) AS hgso_plan,
#             ROUND(CASE WHEN p.hgso_plan > 0 THEN (a.hgso * 100.0 / p.hgso_plan)::numeric ELSE 0 END, 2) AS hgso_ach
#         FROM actual a
#         FULL OUTER JOIN plan p ON a.periode = p.periode
#         ORDER BY periode
#     """

#     try:
#         with connections['kqms_db'].cursor() as cursor:
#             cursor.execute(query, params)  #  Gunakan parameterized query
#             chart_data = cursor.fetchall()

#         df = pd.DataFrame(chart_data, columns=[
#             'periode',
#             'lglo', 'lglo_plan', 'lglo_ach',
#             'mglo', 'mglo_plan', 'mglo_ach',
#             'hglo', 'hglo_plan', 'hglo_ach',
#             'mws', 'mws_plan', 'mws_ach',
#             'lgso', 'lgso_plan', 'lgso_ach',
#             'mgso', 'mgso_plan', 'mgso_ach',
#             'hgso', 'hgso_plan', 'hgso_ach',
#         ])

#         lim_cols = ['lglo', 'mglo', 'hglo']
#         sap_cols = ['lgso', 'mgso', 'hgso', 'mws']
#         lim_plan_cols = [f + '_plan' for f in lim_cols]
#         sap_plan_cols = [f + '_plan' for f in sap_cols]

#         df['limonite'] = df[lim_cols].sum(axis=1)
#         df['limonite_plan'] = df[lim_plan_cols].sum(axis=1)
#         df['saprolite'] = df[sap_cols].sum(axis=1)
#         df['saprolite_plan'] = df[sap_plan_cols].sum(axis=1)

#         df['total_actual'] = df['limonite'] + df['saprolite']
#         df['total_plan']   = df['limonite_plan'] + df['saprolite_plan']
#         df['achievement']  = df.apply(lambda row: round((row['total_actual'] / row['total_plan'] * 100), 2) if row['total_plan'] > 0 else 0, axis=1)

#         df['limonite_ach'] = df.apply(
#             lambda r: round((r['limonite'] / r['limonite_plan'] * 100), 2) if r['limonite_plan'] > 0 else 0, axis=1
#         )
#         df['saprolite_ach'] = df.apply(
#             lambda r: round((r['saprolite'] / r['saprolite_plan'] * 100), 2) if r['saprolite_plan'] > 0 else 0, axis=1
#         )

#         return JsonResponse({
#             'x_data'        : df['periode'].tolist(),
#             'limonite'      : df['limonite'].tolist(),
#             'limonite_plan' : df['limonite_plan'].tolist(),
#             'limonite_ach'  : df['limonite_ach'].tolist(),
#             'saprolite'     : df['saprolite'].tolist(),
#             'saprolite_plan': df['saprolite_plan'].tolist(),
#             'saprolite_ach' : df['saprolite_ach'].tolist(),
#             'total_actual'  : df['total_actual'].tolist(),
#             'total_plan'    : df['total_plan'].tolist(),
#             'achievement'   : df['achievement'].tolist()
#         }, safe=False)



#     except DatabaseError as e:
#         return JsonResponse({'error': f"Database query failed: {e}"}, status=500)

# def get_chart_soil(request):
#     filter_type  = request.GET.get('filter_type')
#     filter_year  = request.GET.get('filter_year')
#     filter_month = request.GET.get('filter_month')
#     filter_week  = request.GET.get('filter_week')
#     filter_date  = request.GET.get('filter_date')
#     date_start   = request.GET.get('date_start')
#     date_end     = request.GET.get('date_end')

#     if db_vendor != 'postgresql':
#         return JsonResponse({'error': 'Unsupported DB'}, status=400)

#     where_actual, where_plan, group_actual, group_plan, params = build_filter_clause(
#         filter_type, filter_year, filter_month, filter_week, filter_date, date_start, date_end
#     )

#     query = f"""
#         WITH actual AS (
#             SELECT
#                 {group_actual} AS periode,
#                 SUM(CASE WHEN nama_material = 'Top Soil' THEN tonnage ELSE 0 END)::numeric AS topsoil
#             FROM mine_productions
#             WHERE {where_actual}
#             GROUP BY {group_actual}
#         ),
#         plan AS (
#             SELECT
#                 {group_plan} AS periode,
#                 SUM(topsoil)::numeric AS topsoil_plan
#             FROM plan_productions
#             WHERE {where_plan}
#             GROUP BY {group_plan}
#         )
#         SELECT
#             COALESCE(a.periode, p.periode) AS periode,
#             ROUND(COALESCE(a.topsoil, 0), 2) AS topsoil,
#             ROUND(COALESCE(p.topsoil_plan, 0), 2) AS topsoil_plan,
#             ROUND(CASE WHEN p.topsoil_plan > 0 THEN (a.topsoil * 100.0 / p.topsoil_plan)::numeric ELSE 0 END, 2) AS topsoil_ach
#         FROM actual a
#         FULL OUTER JOIN plan p ON a.periode = p.periode
#         ORDER BY periode
#     """

#     try:
#         with connections['kqms_db'].cursor() as cursor:
#             cursor.execute(query, params)
#             chart_data = cursor.fetchall()

#         df = pd.DataFrame(chart_data, columns=[
#             'periode', 'topsoil', 'topsoil_plan', 'topsoil_ach'
#         ])

#         df['total_actual'] = df[['topsoil']].sum(axis=1)
#         df['total_plan'] = df[['topsoil_plan']].sum(axis=1)
#         df['achievement'] = df.apply(
#             lambda row: round((row['total_actual'] / row['total_plan'] * 100), 2) if row['total_plan'] > 0 else 0,
#             axis=1
#         )

#         return JsonResponse({
#             'x_data': df['periode'].tolist(),
#             'y_actual': df['total_actual'].tolist(),
#             'y_plan': df['total_plan'].tolist(),
#             'achievement': df['achievement'].tolist()
#         }, safe=False)

#     except DatabaseError as e:
#         logger.error(f"Database query failed: {e}")
#         return JsonResponse({'error': f"Database query failed: {e}"}, status=500)

# def get_chart_ob(request):
#     filter_type  = request.GET.get('filter_type')
#     filter_year  = request.GET.get('filter_year')
#     filter_month = request.GET.get('filter_month')
#     filter_week  = request.GET.get('filter_week')
#     filter_date  = request.GET.get('filter_date')
#     date_start   = request.GET.get('date_start')
#     date_end     = request.GET.get('date_end')

#     if db_vendor != 'postgresql':
#         return JsonResponse({'error': 'Unsupported DB'}, status=400)

#     where_actual, where_plan, group_actual, group_plan, params = build_filter_clause(
#         filter_type, filter_year, filter_month, filter_week, filter_date, date_start, date_end
#     )

#     query = f"""
#         WITH actual AS (
#             SELECT {group_actual} AS periode,
#                    SUM(CASE WHEN nama_material = 'OB' THEN tonnage ELSE 0 END)::numeric AS ob
#             FROM mine_productions
#             WHERE {where_actual}
#             GROUP BY {group_actual}
#         ),
#         plan AS (
#             SELECT {group_plan} AS periode,
#                    SUM(ob)::numeric AS ob_plan
#             FROM plan_productions
#             WHERE {where_plan}
#             GROUP BY {group_plan}
#         )
#         SELECT COALESCE(a.periode, p.periode) AS periode,
#                ROUND(COALESCE(a.ob, 0), 2) AS ob,
#                ROUND(COALESCE(p.ob_plan, 0), 2) AS ob_plan,
#                ROUND(CASE WHEN p.ob_plan > 0 THEN (a.ob * 100.0 / p.ob_plan)::numeric ELSE 0 END, 2) AS ob_ach
#         FROM actual a
#         FULL OUTER JOIN plan p ON a.periode = p.periode
#         ORDER BY periode
#     """

#     try:
#         with connections['kqms_db'].cursor() as cursor:
#             cursor.execute(query, params)
#             chart_data = cursor.fetchall()

#         df = pd.DataFrame(chart_data, columns=['periode', 'ob', 'ob_plan', 'ob_ach'])
#         df['total_actual'] = df[['ob']].sum(axis=1)
#         df['total_plan'] = df[['ob_plan']].sum(axis=1)
#         df['achievement'] = df.apply(lambda row: round((row['total_actual'] / row['total_plan'] * 100), 2) if row['total_plan'] > 0 else 0, axis=1)

#         return JsonResponse({
#             'x_data': df['periode'].tolist(),
#             'y_actual': df['total_actual'].tolist(),
#             'y_plan': df['total_plan'].tolist(),
#             'achievement': df['achievement'].tolist()
#         }, safe=False)

#     except DatabaseError as e:
#         logger.error(f"Database query failed: {e}")
#         return JsonResponse({'error': f"Database query failed: {e}"}, status=500)

# def get_chart_waste(request):
#     filter_type  = request.GET.get('filter_type')
#     filter_year  = request.GET.get('filter_year')
#     filter_month = request.GET.get('filter_month')
#     filter_week  = request.GET.get('filter_week')
#     filter_date  = request.GET.get('filter_date')
#     date_start   = request.GET.get('date_start')
#     date_end     = request.GET.get('date_end')

#     if db_vendor != 'postgresql':
#         return JsonResponse({'error': 'Unsupported DB'}, status=400)

#     where_actual, where_plan, group_actual, group_plan, params = build_filter_clause(
#         filter_type, filter_year, filter_month, filter_week, filter_date, date_start, date_end
#     )

#     query = f"""
#         WITH actual AS (
#             SELECT {group_actual} AS periode,
#                    SUM(CASE WHEN nama_material = 'Waste' THEN tonnage ELSE 0 END)::numeric AS waste
#             FROM mine_productions
#             WHERE {where_actual}
#             GROUP BY {group_actual}
#         ),
#         plan AS (
#             SELECT {group_plan} AS periode,
#                    SUM(waste)::numeric AS waste_plan
#             FROM plan_productions
#             WHERE {where_plan}
#             GROUP BY {group_plan}
#         )
#         SELECT COALESCE(a.periode, p.periode) AS periode,
#                ROUND(COALESCE(a.waste, 0), 2) AS waste,
#                ROUND(COALESCE(p.waste_plan, 0), 2) AS waste_plan,
#                ROUND(CASE WHEN p.waste_plan > 0 THEN (a.waste * 100.0 / p.waste_plan)::numeric ELSE 0 END, 2) AS waste_ach
#         FROM actual a
#         FULL OUTER JOIN plan p ON a.periode = p.periode
#         ORDER BY periode
#     """

#     try:
#         with connections['kqms_db'].cursor() as cursor:
#             cursor.execute(query, params)
#             chart_data = cursor.fetchall()

#         df = pd.DataFrame(chart_data, columns=['periode', 'waste', 'waste_plan', 'waste_ach'])
#         df['total_actual'] = df[['waste']].sum(axis=1)
#         df['total_plan'] = df[['waste_plan']].sum(axis=1)
#         df['achievement'] = df.apply(lambda row: round((row['total_actual'] / row['total_plan'] * 100), 2) if row['total_plan'] > 0 else 0, axis=1)

#         return JsonResponse({
#             'x_data': df['periode'].tolist(),
#             'y_actual': df['total_actual'].tolist(),
#             'y_plan': df['total_plan'].tolist(),
#             'achievement': df['achievement'].tolist()
#         }, safe=False)

#     except DatabaseError as e:
#         logger.error(f"Database query failed: {e}")
#         return JsonResponse({'error': f"Database query failed: {e}"}, status=500)

# def get_chart_quarry(request):
#     filter_type  = request.GET.get('filter_type')
#     filter_year  = request.GET.get('filter_year')
#     filter_month = request.GET.get('filter_month')
#     filter_week  = request.GET.get('filter_week')
#     filter_date  = request.GET.get('filter_date')
#     date_start   = request.GET.get('date_start')
#     date_end     = request.GET.get('date_end')

#     if db_vendor != 'postgresql':
#         return JsonResponse({'error': 'Unsupported DB'}, status=400)

#     where_actual, where_plan, group_actual, group_plan, params = build_filter_clause(
#         filter_type, filter_year, filter_month, filter_week, filter_date, date_start, date_end
#     )

#     query = f"""
#         WITH actual AS (
#             SELECT {group_actual} AS periode,
#                    SUM(CASE WHEN nama_material = 'Quarry' THEN tonnage ELSE 0 END)::numeric AS quarry
#             FROM mine_productions
#             WHERE {where_actual}
#             GROUP BY {group_actual}
#         ),
#         plan AS (
#             SELECT {group_plan} AS periode,
#                    SUM(quarry)::numeric AS quarry_plan
#             FROM plan_productions
#             WHERE {where_plan}
#             GROUP BY {group_plan}
#         )
#         SELECT COALESCE(a.periode, p.periode) AS periode,
#                ROUND(COALESCE(a.quarry, 0), 2) AS quarry,
#                ROUND(COALESCE(p.quarry_plan, 0), 2) AS quarry_plan,
#                ROUND(CASE WHEN p.quarry_plan > 0 THEN (a.quarry * 100.0 / p.quarry_plan)::numeric ELSE 0 END, 2) AS quarry_ach
#         FROM actual a
#         FULL OUTER JOIN plan p ON a.periode = p.periode
#         ORDER BY periode
#     """

#     try:
#         with connections['kqms_db'].cursor() as cursor:
#             cursor.execute(query, params)
#             chart_data = cursor.fetchall()

#         df = pd.DataFrame(chart_data, columns=['periode', 'quarry', 'quarry_plan', 'quarry_ach'])
#         df['total_actual'] = df[['quarry']].sum(axis=1)
#         df['total_plan'] = df[['quarry_plan']].sum(axis=1)
#         df['achievement'] = df.apply(lambda row: round((row['total_actual'] / row['total_plan'] * 100), 2) if row['total_plan'] > 0 else 0, axis=1)

#         return JsonResponse({
#             'x_data': df['periode'].tolist(),
#             'y_actual': df['total_actual'].tolist(),
#             'y_plan': df['total_plan'].tolist(),
#             'achievement': df['achievement'].tolist()
#         }, safe=False)

#     except DatabaseError as e:
#         logger.error(f"Database query failed: {e}")
#         return JsonResponse({'error': f"Database query failed: {e}"}, status=500)

# def get_chart_others(request):
#     filter_type  = request.GET.get('filter_type')
#     filter_year  = request.GET.get('filter_year')
#     filter_month = request.GET.get('filter_month')
#     filter_week  = request.GET.get('filter_week')
#     filter_date  = request.GET.get('filter_date')
#     date_start   = request.GET.get('date_start')
#     date_end     = request.GET.get('date_end')

#     if db_vendor != 'postgresql':
#         return JsonResponse({'error': 'Unsupported DB'}, status=400)

#     where_actual, where_plan, group_actual, group_plan, params = build_filter_clause(
#         filter_type, filter_year, filter_month, filter_week, filter_date, date_start, date_end
#     )

#     query = f"""
#         WITH actual AS (
#             SELECT {group_actual} AS periode,
#                    SUM(CASE WHEN nama_material = 'Ballast' THEN tonnage ELSE 0 END)::numeric AS ballast,
#                    SUM(CASE WHEN nama_material = 'Biomass' THEN tonnage ELSE 0 END)::numeric AS biomass
#             FROM mine_productions
#             WHERE {where_actual}
#             GROUP BY {group_actual}
#         ),
#         plan AS (
#             SELECT {group_plan} AS periode,
#                    SUM(ballast)::numeric AS ballast_plan,
#                    SUM(biomass)::numeric AS biomass_plan
#             FROM plan_productions
#             WHERE {where_plan}
#             GROUP BY {group_plan}
#         )
#         SELECT COALESCE(a.periode, p.periode) AS periode,
#                ROUND(COALESCE(a.ballast, 0), 2) AS ballast,
#                ROUND(COALESCE(p.ballast_plan, 0), 2) AS ballast_plan,
#                ROUND(CASE WHEN p.ballast_plan > 0 THEN (a.ballast * 100.0 / p.ballast_plan)::numeric ELSE 0 END, 2) AS ballast_ach,
#                ROUND(COALESCE(a.biomass, 0), 2) AS biomass,
#                ROUND(COALESCE(p.biomass_plan, 0), 2) AS biomass_plan,
#                ROUND(CASE WHEN p.biomass_plan > 0 THEN (a.biomass * 100.0 / p.biomass_plan)::numeric ELSE 0 END, 2) AS biomass_ach
#         FROM actual a
#         FULL OUTER JOIN plan p ON a.periode = p.periode
#         ORDER BY periode
#     """

#     try:
#         with connections['kqms_db'].cursor() as cursor:
#             cursor.execute(query, params)
#             chart_data = cursor.fetchall()

#         df = pd.DataFrame(chart_data, columns=['periode', 'ballast', 'ballast_plan', 'ballast_ach', 'biomass', 'biomass_plan', 'biomass_ach'])
#         df['total_actual'] = df[['ballast', 'biomass']].sum(axis=1)
#         df['total_plan'] = df[['ballast_plan', 'biomass_plan']].sum(axis=1)
#         df['achievement'] = df.apply(lambda row: round((row['total_actual'] / row['total_plan'] * 100), 2) if row['total_plan'] > 0 else 0, axis=1)

#         return JsonResponse({
#             'x_data': df['periode'].tolist(),
#             'y_actual': df['total_actual'].tolist(),
#             'y_plan': df['total_plan'].tolist(),
#             'achievement': df['achievement'].tolist()
#         }, safe=False)

#     except DatabaseError as e:
#         logger.error(f"Database query failed: {e}")
#         return JsonResponse({'error': f"Database query failed: {e}"}, status=500)