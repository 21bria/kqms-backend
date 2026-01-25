import os
import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.gis.geos import GEOSGeometry
from django.db import transaction
from shapely.errors import ShapelyError
from django.views.decorators.csrf import csrf_exempt
from kqms.services.geojson_transform import convert_to_wgs84
from kqms.services.geojson_enrich import enrich_pit_properties
from kqms.models import SourceMines, SourceMinesLoading

@login_required
def imports_json_page(request):
    return render(request, 'gis/template-import.html')

# fungsi review Maps:
# @csrf_exempt
# def upload_convert_geojson(request):
#     if request.method != "POST":
#         return JsonResponse({"error": "POST only"}, status=405)

#     file = request.FILES.get("file")
#     if not file:
#         return JsonResponse({"error": "File tidak ditemukan"}, status=400)

#     data = json.load(file)

#     data = convert_to_wgs84(data)
#     data = enrich_pit_properties(data)

#     return JsonResponse({
#         "status": "ok",
#         "geojson": data
#     })

@csrf_exempt
def upload_convert_geojson(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    file = request.FILES.get("file")
    if not file:
        return JsonResponse({"error": "File tidak ditemukan"}, status=400)

    try:
        # === ambil PIT dari nama file ===
        filename = file.name                       # PIT_A.geojson
        pit_from_file = os.path.splitext(filename)[0]
        pit_from_file = pit_from_file.replace("_", " ").upper()

        # === load geojson ===
        data = json.load(file)

        # === convert & enrich ===
        data = convert_to_wgs84(data)
        data = enrich_pit_properties(
            data,
            default_pit=pit_from_file
        )

        return JsonResponse({
            "status": "ok",
            "geojson": data
        })

    except json.JSONDecodeError:
        return JsonResponse({"error": "File bukan GeoJSON valid"}, status=400)

    except ShapelyError as e:
        return JsonResponse({"error": f"Geometry error: {str(e)}"}, status=400)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
@csrf_exempt
def sync_geojson_to_db(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    payload = json.loads(request.body)
    import_type = payload.get("import_type")
    geojson = payload.get("geojson")

    if not import_type or not geojson:
        return JsonResponse({"error": "Data tidak lengkap"}, status=400)

    features = geojson.get("features", [])

    updated = 0
    updated_keys = []
    skipped = []

    with transaction.atomic():
        for i, feature in enumerate(features, start=1):
            props = feature.get("properties", {})
            geom_json = json.dumps(feature.get("geometry"))

            geom = GEOSGeometry(geom_json, srid=4326)
            centroid = geom.centroid

            lat = centroid.y
            lng = centroid.x

            # ================= mine_sources =================
            if import_type == "mine_sources":
                key = props.get("pit") or props.get("name")

                if not key:
                    skipped.append({
                        "row": i,
                        "reason": "PIT / name tidak ditemukan",
                        "properties": props
                    })
                    continue

                rows = SourceMines.objects.filter(
                    sources_area=key
                ).update(
                    latitude=lat,
                    longitude=lng,
                    geometry=geom,
                    extra_properties=props,
                    status=1
                )

                if rows == 0:
                    skipped.append({
                        "row": i,
                        "key": key,
                        "reason": "Tidak ditemukan di database"
                    })
                else:
                    updated += rows
                    updated_keys.append(key)

            # ================= loading_point =================
            elif import_type == "point_loading":
                key = props.get("loading_point") or props.get("name")

                if not key:
                    skipped.append({
                        "row": i,
                        "reason": "loading_point / name tidak ditemukan",
                        "properties": props
                    })
                    continue

                rows = SourceMinesLoading.objects.filter(
                    loading_point=key
                ).update(
                    latitude=lat,
                    longitude=lng,
                    geometry=geom,
                    extra_properties=props,
                    status=1
                )

                if rows == 0:
                    skipped.append({
                        "row": i,
                        "key": key,
                        "reason": "Tidak ditemukan di database"
                    })
                else:
                    updated += rows
                    updated_keys.append(key)

    return JsonResponse({
        "status": "ok",
        "updated": updated,
        "updated_keys": updated_keys,
        "skipped": skipped,
        "has_error": len(skipped) > 0
    })
