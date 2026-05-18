import os
import json
from shapely.geometry import shape, Point, LineString, mapping

CARPETA_GEOJSON = os.path.join(os.getcwd(), "data", "geojson")

def obtener_tramo_ruta(nombre_ruta, origen, destino):
    archivo = f"{nombre_ruta}.geojson"
    ruta_path = os.path.join(CARPETA_GEOJSON, archivo)

    with open(ruta_path, "r", encoding="utf-8") as f:
        geojson = json.load(f)

    feature = geojson["features"][0]
    linea = shape(feature["geometry"])

    if linea.geom_type == "MultiLineString":
        linea = max(linea.geoms, key=lambda l: l.length)

    punto_origen = Point(origen["lon"], origen["lat"])
    punto_destino = Point(destino["lon"], destino["lat"])

    distancia_origen = linea.project(punto_origen)
    distancia_destino = linea.project(punto_destino)

    inicio = min(distancia_origen, distancia_destino)
    fin = max(distancia_origen, distancia_destino)

    coordenadas = list(linea.coords)

    puntos_tramo = []

    for coord in coordenadas:
        punto = Point(coord)
        distancia = linea.project(punto)

        if inicio <= distancia <= fin:
            puntos_tramo.append(coord)

    if len(puntos_tramo) < 2:
        return geojson

    tramo = LineString(puntos_tramo)

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "ruta": nombre_ruta
                },
                "geometry": mapping(tramo)
            }
        ]
    }