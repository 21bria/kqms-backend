from pyproj import Transformer
import json

def convert_to_wgs84(data, source_epsg="EPSG:32752"):
    transformer = Transformer.from_crs(
        source_epsg,
        "EPSG:4326",
        always_xy=True
    )

    for feature in data.get("features", []):
        geom = feature["geometry"]
        gtype = geom["type"]

        def transform_ring(ring):
            return [list(transformer.transform(x, y)) for x, y in ring]

        if gtype == "Polygon":
            geom["coordinates"] = [
                transform_ring(ring) for ring in geom["coordinates"]
            ]

        elif gtype == "MultiPolygon":
            geom["coordinates"] = [
                [transform_ring(ring) for ring in poly]
                for poly in geom["coordinates"]
            ]

    data.pop("crs", None)
    return data
