# views.py
import logging
from django.http import JsonResponse
from django.db import connections
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
logger = logging.getLogger(__name__) #tambahkan ini untuk multi database.
import json
from scipy.optimize import linprog
import numpy as np
from decimal import Decimal
from django.db.models import Max
from ....models.selling_blending import BlendingResult

@login_required
def blending_manual_page(request):
    return render(request, 'admin-selling/blending/form-manual.html')

# def auto_blend_optimizer(target_tonase, target_ni, selected_piles):
#     ni_list = [p['ni'] for p in selected_piles]
#     max_available = [p['balance'] for p in selected_piles]

#     n = len(selected_piles)

#     # ========== OBJECTIVE ==========
#     # Objective function: minimize 0 (karena kita hanya cari solusi feasible)
#     c = [0] * n

#     # ========== CONSTRAINTS ==========
#     # Constraint 1: sum(x) = target_tonase
#     # Constraint 2: sum(x_i * ni_i) = target_tonase * target_ni

#     A_eq = [
#         [1] * n,                   # sum(x_i) = total tonase
#         ni_list                    # sum(x_i * ni_i) = total ni
#     ]
#     b_eq = [
#         target_tonase,
#         target_tonase * target_ni
#     ]

#     bounds = [(0, avail) for avail in max_available]

#     # ========== SOLVE ==========
#     result = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')

#     if result.success:
#         used = result.x
#         total_ni = sum(used[i] * ni_list[i] for i in range(len(used)))
#         avg_ni = total_ni / target_tonase

#         final_result = []
#         for i, p in enumerate(selected_piles):
#             final_result.append({
#                 'pile_id': p['pile_id'],
#                 'used_tonase': round(used[i], 2),
#                 'ni': p['ni'],
#                 'fe': p.get('fe', 0),
#                 'balance': p.get('balance', 0)
#             })

#         return {
#             'success': True,
#             'result': final_result,
#             'final_grade': {
#                 'ni': round(avg_ni, 2)
#             },
#             'total_used': round(target_tonase, 2)
#         }
#     else:
#         return {
#             'success': False,
#             'error': 'Tidak ditemukan kombinasi yang memenuhi target grade dan tonase.'
#         }

def auto_blend_optimizer(target_tonase, target_ni, selected_piles):
    ni_list = [p['ni'] for p in selected_piles]
    max_available = [p['balance'] for p in selected_piles]

    n = len(selected_piles)
    c = [abs(ni - target_ni) for ni in ni_list]
    A_eq = [[1]*n, ni_list]
    b_eq = [target_tonase, target_tonase * target_ni]
    bounds = [(0, avail) for avail in max_available]

    result = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')

    if result.success:
        used = result.x

        # Sum-product untuk semua unsur
        total = target_tonase
        total_ni = sum(used[i] * selected_piles[i]['ni'] for i in range(n))
        total_fe = sum(used[i] * selected_piles[i].get('fe', 0) for i in range(n))
        total_co = sum(used[i] * selected_piles[i].get('co', 0) for i in range(n))
        total_al2o3 = sum(used[i] * selected_piles[i].get('al2o3', 0) for i in range(n))
        total_mgo = sum(used[i] * selected_piles[i].get('mgo', 0) for i in range(n))
        total_sio2 = sum(used[i] * selected_piles[i].get('sio2', 0) for i in range(n))
        total_sm = sum(used[i] * selected_piles[i].get('sm', 0) for i in range(n))

        final_result = []
        for i, p in enumerate(selected_piles):
            final_result.append({
                'pile_id': p['pile_id'],
                'used_tonase': round(used[i], 2),
                'balance': p.get('balance', 0),
                'ni': p.get('ni', 0),
                'fe': p.get('fe', 0),
                'co': p.get('co', 0),
                'mgo': p.get('mgo', 0),
                'al2o3': p.get('al2o3', 0),
                'sio2': p.get('sio2', 0),
                'sm': p.get('sm', 0),
            })

        return {
            'success': True,
            'result': final_result,
            'final_grade': {
                'ni'    : round(total_ni / total, 2),
                'fe'    : round(total_fe / total, 2),
                'co'    : round(total_co / total, 2),
                'al2o3' : round(total_al2o3 / total, 2),
                'mgo'   : round(total_mgo / total, 2),
                'sio2'  : round(total_sio2 / total, 2),
                'sm': round(total_sio2 / total_mgo, 2) if total_mgo != 0 else 0  # ✅ langsung dibagi
            },
            'total_used': round(total, 2)
        }

@csrf_exempt
def calculate_blending_auto(request):
    if request.method == "POST":
        try:
            payload         = json.loads(request.body)
            selected_piles  = payload.get("selected_piles", [])
            target_tonase   = payload.get("target_tonase")
            target_ni       = payload.get("target_ni")

            result = auto_blend_optimizer(target_tonase, target_ni, selected_piles)
            return JsonResponse(result)

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)
    return JsonResponse({"success": False, "error": "Only POST allowed"}, status=405)

@csrf_exempt
def calculate_blending_auto_all(request):
    if request.method == 'POST':
        try:
            payload = json.loads(request.body)

            try:
                target_tonase = float(payload.get("target_tonase", 0))
                target_ni     = float(payload.get("target_ni", 0))
            except (TypeError, ValueError):
                return JsonResponse({"success": False, "error": "Target tonase dan Ni harus berupa angka."}, status=400)

            material = payload.get("material")

            query = """
                SELECT 
                    t1.pile_id, 
                    t1.stockpile, 
                    t1.nama_material,
                    ROUND((t1.released - COALESCE(t2.tonnage, 0))::numeric, 2) AS balance,
                    t1.Ni,
                    t1.Co,
                    t1.Al2O3,
                    t1.Fe,
                    t1.Mgo,
                    t1.SiO2,
                    t1.MC,
                    t1.SM
                FROM inventory_by_dome AS t1
                LEFT JOIN selling_by_dome AS t2 
                    ON t2.stockpile = t1.stockpile 
                    AND t2.dome = t1.pile_id
                WHERE t1.status_dome != 'Finished'
                  AND t1.released > 0
                  AND t1.ni IS NOT NULL
            """

            params = []
            if material:
                query += " AND t1.sale_adjust = %s"
                params.append(material)

            with connections['kqms_db'].cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                all_piles = [dict(zip(columns, row)) for row in rows]

            # 🔄 Konversi nilai ke float
            # Pastikan semua field numerik dikonversi ke float
            for item in all_piles:
                for field in ['balance', 'ni', 'fe', 'co', 'mgo', 'al2o3', 'sio2', 'sm']:
                    val = item.get(field)
                    if isinstance(val, Decimal):
                        item[field] = float(val)
                    elif isinstance(val, (float, int)):
                        item[field] = float(val)
                    elif isinstance(val, str) and val.replace('.', '', 1).isdigit():
                        item[field] = float(val)


            result = auto_blend_optimizer(target_tonase, target_ni, all_piles)
            return JsonResponse(result)

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({"success": False, "error": "Only POST allowed"}, status=405)