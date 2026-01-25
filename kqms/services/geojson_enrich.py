from shapely.geometry import shape

# def enrich_pit_properties(data):
#     for feature in data.get("features", []):
#         geom = shape(feature["geometry"])
#         centroid = geom.centroid

#         props = feature.setdefault("properties", {})

#         # normalisasi PIT
#         pit = (
#             props.get("PIT")
#             or props.get("pit")
#             or props.get("name")
#             or "UNKNOWN"
#         )

#         props.update({
#             "pit": pit,
#             "x": round(centroid.x, 6),
#             "y": round(centroid.y, 6),
#             "area_ha": round(geom.area / 10000, 2) if geom.area else None
#         })

#     return data

def enrich_pit_properties(data, default_pit=None):
    for feature in data.get("features", []):
        geom = shape(feature["geometry"])
        centroid = geom.centroid

        props = feature.setdefault("properties", {})

        # === PRIORITAS NAMA PIT ===
        pit = (
            props.get("PIT")
            or props.get("pit")
            or props.get("name")
            or default_pit
            or "UNKNOWN"
        )

        props.update({
            "pit": pit,
            "x": round(centroid.x, 6),
            "y": round(centroid.y, 6),
            "area_ha": round(geom.area / 10000, 2) if geom.area else None
        })

    return data