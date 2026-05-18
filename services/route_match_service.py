import os
import json
from shapely.geometry import shape, Point
from shapely.ops import transform
from pyproj import Transformer

CARPETA_GEOJSON = os.path.join(os.getcwd(), "data", "geojson")

RUTAS_PERMITIDAS = [
    "LINEA_19_IDA.geojson",
    "LINEA_19_RETORNO.geojson",
    "LINEA_24B_IDA.geojson"
]

transformer = Transformer.from_crs("EPSG:4326", "EPSG:32717", always_xy=True)

def convertir_a_metros(geom):
    return transform(transformer.transform, geom)

def distancia_a_ruta(punto, archivo):
    ruta_path = os.path.join(CARPETA_GEOJSON, archivo)

    with open(ruta_path, "r", encoding="utf-8") as f:
        geojson = json.load(f)

    punto_metros = convertir_a_metros(punto)

    distancia_minima = float("inf")

    for feature in geojson["features"]:
        geometria = shape(feature["geometry"])
        geometria_metros = convertir_a_metros(geometria)

        distancia = punto_metros.distance(geometria_metros)

        if distancia < distancia_minima:
            distancia_minima = distancia

    return distancia_minima

def recomendar_linea(origen, destino):
    punto_origen = Point(origen["lon"], origen["lat"])
    punto_destino = Point(destino["lon"], destino["lat"])

    mejor_ruta = None
    mejor_puntaje = float("inf")

    for archivo in RUTAS_PERMITIDAS:
        distancia_origen = distancia_a_ruta(punto_origen, archivo)
        distancia_destino = distancia_a_ruta(punto_destino, archivo)

        puntaje = distancia_origen + distancia_destino

        if puntaje < mejor_puntaje:
            mejor_puntaje = puntaje
            mejor_ruta = archivo

    return {
        "linea": mejor_ruta.replace(".geojson", ""),
        "distancia_aproximada_m": round(mejor_puntaje, 2)
    }