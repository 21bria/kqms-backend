from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import View
from ...models.mine_productions_view import mineProductionsView
from ...models.ore_production_view import OreProductionsView
from django.core.cache import cache
from datetime import datetime
from django.utils.timezone import now as timezone_now
from django.db.models import Sum

def recon_mine_day(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Gunakan GET request.'}, status=405)

    try:
        filter_date = request.GET.get('filter_date')

        # --- Query GC ---
        gc_data = (
            OreProductionsView.objects
            .filter(tgl_production=filter_date)
            .values('tgl_production', 'prospect_area', 'shift', 'nama_material', 'direct')
            .annotate(
                gc_total_ritase=Sum('ritase'),
                gc_total_tonnage=Sum('tonnage')
            )
            .order_by('tgl_production', 'prospect_area', 'shift', 'nama_material', 'direct')
        )

        # --- Query Mining ---
        mining_data = (
            mineProductionsView.objects
            .filter(date_production=filter_date)
            .values('date_production', 'loading_point', 'shift', 'nama_material', 'direct')
            .annotate(
                mining_total_ritase=Sum('ritase'),
                mining_total_tonnage=Sum('tonnage')
            )
            .order_by('date_production', 'loading_point', 'shift', 'nama_material', 'direct')
        )

        # Buat dictionary untuk mining
        mining_dict = {
            (m['date_production'], m['loading_point'], m['shift'], m['nama_material'], m['direct']): {
                'mining_total_ritase': round(m['mining_total_ritase'], 2),
                'mining_total_tonnage': round(m['mining_total_tonnage'], 2),
            }
            for m in mining_data
        }

        # Gabungkan hasil rekonsiliasi + hitung total
        reconciliation_data = []
        total_gc_ritase = total_mining_ritase = 0
        total_gc_tonnage = total_mining_tonnage = 0

        for gc in gc_data:
            key = (
                gc['tgl_production'],
                gc['prospect_area'],
                gc['shift'],
                gc['nama_material'],
                gc['direct'],
            )
            mining = mining_dict.get(key)

            gc_total_ritase = round(gc['gc_total_ritase'], 2)
            gc_total_tonnage = round(gc['gc_total_tonnage'], 2)

            mining_total_ritase = mining['mining_total_ritase'] if mining else 0
            mining_total_tonnage = mining['mining_total_tonnage'] if mining else 0

            # update total
            total_gc_ritase += gc_total_ritase
            total_gc_tonnage += gc_total_tonnage
            total_mining_ritase += mining_total_ritase
            total_mining_tonnage += mining_total_tonnage

            reconciliation_data.append({
                'date': gc['tgl_production'],
                'area': gc['prospect_area'],
                'shift': gc['shift'],
                'material': gc['nama_material'],
                'selling_direct': gc['direct'],
                'gc_total_ritase': gc_total_ritase,
                'mining_total_ritase': mining_total_ritase,
                'ritase_difference': round(gc_total_ritase - mining_total_ritase, 2),
                'gc_total_tonnage': gc_total_tonnage,
                'mining_total_tonnage': mining_total_tonnage,
                'tonnage_difference': round(gc_total_tonnage - mining_total_tonnage, 2),
            })

        # Buat summary card
        summary = {
            'gc_total_ritase': round(total_gc_ritase, 2),
            'mining_total_ritase': round(total_mining_ritase, 2),
            'ritase_difference': round(total_gc_ritase - total_mining_ritase, 2),
            'gc_total_tonnage': round(total_gc_tonnage, 2),
            'mining_total_tonnage': round(total_mining_tonnage, 2),
            'tonnage_difference': round(total_gc_tonnage - total_mining_tonnage, 2),
        }

        return JsonResponse({'data': reconciliation_data, 'summary': summary}, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
