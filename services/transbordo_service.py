import os
import json
from shapely.geometry import shape, Point, mapping
from shapely.ops import nearest_points, substring, linemerge

CARPETA_GEOJSON = os.path.join(os.getcwd(), "data", "geojson")


def cargar_rutas():
    rutas = []

    for archivo in os.listdir(CARPETA_GEOJSON):
        if archivo.endswith(".geojson"):
            path = os.path.join(CARPETA_GEOJSON, archivo)

            try:
                with open(path, "r", encoding="utf-8") as f:
                    geojson = json.load(f)

                geometrias = [
                    shape(feature["geometry"])
                    for feature in geojson["features"]
                ]

                linea = linemerge(geometrias)

                if linea.geom_type == "MultiLineString":
                    linea = max(linea.geoms, key=lambda l: l.length)

                rutas.append({
                    "nombre": archivo.replace(".geojson", ""),
                    "linea": linea
                })

            except Exception:
                continue

    return rutas


def recortar_linea(linea, punto_a, punto_b):
    distancia_a = linea.project(punto_a)
    distancia_b = linea.project(punto_b)

    inicio = min(distancia_a, distancia_b)
    fin = max(distancia_a, distancia_b)

    tramo = substring(linea, inicio, fin)

    return {
        "type": "Feature",
        "properties": {},
        "geometry": mapping(tramo)
    }


def buscar_transbordo(origen, destino):
    rutas = cargar_rutas()

    punto_origen = Point(origen["lon"], origen["lat"])
    punto_destino = Point(destino["lon"], destino["lat"])

    mejor = None
    mejor_puntaje = float("inf")

    for ruta_origen in rutas:
        distancia_origen = ruta_origen["linea"].distance(punto_origen)

        if distancia_origen > 0.01:
            continue

        for ruta_destino in rutas:
            if ruta_origen["nombre"] == ruta_destino["nombre"]:
                continue

            distancia_destino = ruta_destino["linea"].distance(punto_destino)

            if distancia_destino > 0.01:
                continue

            p1, p2 = nearest_points(
                ruta_origen["linea"],
                ruta_destino["linea"]
            )

            distancia_union = p1.distance(p2)

            if distancia_union > 0.003:
                continue

            puntaje = distancia_origen + distancia_destino + distancia_union

            if puntaje < mejor_puntaje:
                mejor_puntaje = puntaje

                punto_transbordo = {
                    "lat": p1.y,
                    "lon": p1.x,
                    "nombre": "Punto de transbordo aproximado"
                }

                tramo_1 = recortar_linea(
                    ruta_origen["linea"],
                    punto_origen,
                    p1
                )

                tramo_2 = recortar_linea(
                    ruta_destino["linea"],
                    p2,
                    punto_destino
                )

                mejor = {
                    "tipo": "transbordo",
                    "linea_1": ruta_origen["nombre"],
                    "linea_2": ruta_destino["nombre"],
                    "transbordo": punto_transbordo,
                    "tramos_geojson": {
                        "type": "FeatureCollection",
                        "features": [
                            {
                                **tramo_1,
                                "properties": {
                                    "linea": ruta_origen["nombre"],
                                    "color": "blue"
                                }
                            },
                            {
                                **tramo_2,
                                "properties": {
                                    "linea": ruta_destino["nombre"],
                                    "color": "red"
                                }
                            }
                        ]
                    }
                }

    return mejor