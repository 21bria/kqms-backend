import os
import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from kqms.services.iup_geojson_service import get_iup_with_sources_geojson

@login_required
def mine_iup_page(request):
    return render(request, 'gis/template-iup.html')


# @login_required
def api_iup_with_sources(request, iup_id):
    data = get_iup_with_sources_geojson(iup_id)

    if not data:
        return JsonResponse({"error": "IUP tidak ditemukan"}, status=404)

    return JsonResponse(data, safe=False)
