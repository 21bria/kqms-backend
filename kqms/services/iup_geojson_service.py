from django.contrib.gis.db.models.functions import AsGeoJSON
import json
from django.db.models import Sum
from collections import defaultdict
from django.db import connections
from kqms.models.source_model import MineIUP,SourceMines
from kqms.models.mine_productions import mineProductions
from kqms.utils.db_utils import get_db_vendor

 # Memanggil fungsi utility
db_vendor = get_db_vendor('kqms_db')

# def get_iup_with_sources_geojson(iup_id):
#     iup = MineIUP.objects.filter(id=iup_id).first()
#     if not iup or not iup.geometry:
#         return None

#     # IUP GeoJSON
#     iup_geojson = json.loads(
#         MineIUP.objects
#         .filter(id=iup_id)
#         .annotate(geojson=AsGeoJSON('geometry'))
#         .values_list('geojson', flat=True)[0]
#     )

#     # Sources di dalam IUP
#     sources = (
#         SourceMines.objects
#         .filter(
#             geometry__isnull=False,
#             geometry__within=iup.geometry
#         )
#         .annotate(geojson=AsGeoJSON('geometry'))
#     )
#     source_features = []

#     for s in sources:
#         extra = s.extra_properties or {}

#         source_features.append({
#             "type": "Feature",
#             "geometry": json.loads(s.geojson),
#             "properties": {
#                 "sources_area": s.sources_area,
#                 "latitude": s.latitude,
#                 "longitude": s.longitude,
#                 "pit": extra.get("pit"),
#                 "luas_ha": extra.get("Luas"),
#                 "area_ha": extra.get("area_ha"),
#                 "status" : s.status,
#             }
#         })

#     return {
#         "iup": {
#             "type": "Feature",
#             "geometry": iup_geojson,
#             "properties": {
#                 "id": iup.id,
#                 "name": iup.iup_name,
#             }
#         },
#         "sources": {
#             "type": "FeatureCollection",
#             "features": source_features
#         }
#     }

def get_source_production_summary(iup_id):
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute("""
            SELECT
                t1.sources_area AS source_id,
                m.nama_material,
                SUM(t1.tonnage) AS tonnage,
                SUM(SUM(t1.tonnage)) OVER (PARTITION BY t1.sources_area) AS total_source      
            FROM productions_mines t1
            JOIN mine_sources s ON s.id = t1.sources_area
            JOIN mine_iup mi ON mi.id = s.id_iup 
            JOIN materials m ON m.id = t1.id_material
            WHERE s.id_iup = %s
            GROUP BY t1.sources_area, m.nama_material;  
        """, [iup_id])

        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

def get_iup_with_sources_geojson(iup_id):
    iup = MineIUP.objects.filter(id=iup_id).first()
    if not iup or not iup.geometry:
        return None

    iup_geojson = json.loads(
        MineIUP.objects
        .filter(id=iup_id)
        .annotate(geojson=AsGeoJSON('geometry'))
        .values_list('geojson', flat=True)[0]
    )

    # ambil produksi summary
    production_rows = get_source_production_summary(iup_id)

    # mapping source_id -> produksi
    production_map = {}
    for row in production_rows:
        sid = row['source_id']
        production_map.setdefault(sid, {
            "total": 0,
            "materials": []
        })

        production_map[sid]["materials"].append({
            "material": row['nama_material'],
            "tonnage": float(row['tonnage'])
        })

        production_map[sid]["total"] = float(row['total_source'])
    
    sources = (
        SourceMines.objects
        .filter(
            geometry__within=iup.geometry,
            geometry__isnull=False
        )
        .annotate(geojson=AsGeoJSON('geometry'))
    )

    source_features = []

    for s in sources:
        extra = s.extra_properties or {}

        source_features.append({
            "type": "Feature",
            "geometry": json.loads(s.geojson),
            "properties": {
                "id": s.id,
                "sources_area": s.sources_area,
                "pit": extra.get("pit"),
                "luas_ha": extra.get("Luas"),
                "status": s.status,
                "productions": production_map.get(s.id, [])  #  FIX
            }
        })

    return {
        "iup": {
            "type": "Feature",
            "geometry": iup_geojson,
            "properties": {
                "id": iup.id,
                "name": iup.iup_name,
            }
        },
        "sources": {
            "type": "FeatureCollection",
            "features": source_features
        }
    }
