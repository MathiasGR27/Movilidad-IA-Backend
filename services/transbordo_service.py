import os
import json
from shapely.geometry import shape, Point, mapping
from shapely.ops import nearest_points, substring, linemerge, transform
from pyproj import Transformer

CARPETA_GEOJSON = os.path.join(os.getcwd(), "data", "geojson")

transformer_to_m = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:32717",
    always_xy=True
)

transformer_to_geo = Transformer.from_crs(
    "EPSG:32717",
    "EPSG:4326",
    always_xy=True
)

MAX_CAMINATA_ORIGEN = 500
MAX_CAMINATA_DESTINO = 500
MAX_DISTANCIA_TRANSBORDO = 350


def a_metros(geom):
    return transform(transformer_to_m.transform, geom)


def a_geojson(geom):
    return transform(transformer_to_geo.transform, geom)


def cargar_rutas():
    rutas = []

    for archivo in os.listdir(CARPETA_GEOJSON):
        if not archivo.lower().endswith(".geojson"):
            continue

        path = os.path.join(CARPETA_GEOJSON, archivo)

        try:
            with open(path, "r", encoding="utf-8") as f:
                geojson = json.load(f)

            geometrias = []

            for feature in geojson["features"]:
                geom = shape(feature["geometry"])

                if geom.geom_type in ["LineString", "MultiLineString"]:
                    geometrias.append(geom)

            if not geometrias:
                continue

            linea = linemerge(geometrias)

            if linea.geom_type == "MultiLineString":
                linea = max(linea.geoms, key=lambda l: l.length)

            linea_metros = a_metros(linea)

            rutas.append({
                "nombre": archivo.replace(".geojson", ""),
                "linea_geo": linea,
                "linea_metros": linea_metros
            })

        except Exception as e:
            print(f"Error cargando {archivo}: {e}")

    return rutas


def recortar_linea_metros(linea_metros, punto_a_m, punto_b_m):
    distancia_a = linea_metros.project(punto_a_m)
    distancia_b = linea_metros.project(punto_b_m)

    inicio = min(distancia_a, distancia_b)
    fin = max(distancia_a, distancia_b)

    tramo_metros = substring(linea_metros, inicio, fin)
    tramo_geo = a_geojson(tramo_metros)

    return tramo_metros, {
        "type": "Feature",
        "properties": {},
        "geometry": mapping(tramo_geo)
    }


def buscar_transbordo(origen, destino):
    rutas = cargar_rutas()

    punto_origen = Point(origen["lon"], origen["lat"])
    punto_destino = Point(destino["lon"], destino["lat"])

    punto_origen_m = a_metros(punto_origen)
    punto_destino_m = a_metros(punto_destino)

    mejor = None
    mejor_puntaje = float("inf")

    for ruta_origen in rutas:
        linea_1 = ruta_origen["linea_metros"]

        caminata_inicio = linea_1.distance(punto_origen_m)

        if caminata_inicio > MAX_CAMINATA_ORIGEN:
            continue

        for ruta_destino in rutas:
            if ruta_origen["nombre"] == ruta_destino["nombre"]:
                continue

            linea_2 = ruta_destino["linea_metros"]

            caminata_final = linea_2.distance(punto_destino_m)

            if caminata_final > MAX_CAMINATA_DESTINO:
                continue

            p1_m, p2_m = nearest_points(linea_1, linea_2)

            caminata_transbordo = p1_m.distance(p2_m)

            if caminata_transbordo > MAX_DISTANCIA_TRANSBORDO:
                continue

            tramo_1_m, tramo_1_geojson = recortar_linea_metros(
                linea_1,
                punto_origen_m,
                p1_m
            )

            tramo_2_m, tramo_2_geojson = recortar_linea_metros(
                linea_2,
                p2_m,
                punto_destino_m
            )

            recorrido_bus_1 = tramo_1_m.length
            recorrido_bus_2 = tramo_2_m.length

            puntaje = (
                caminata_inicio * 2
                + recorrido_bus_1
                + caminata_transbordo * 3
                + recorrido_bus_2
                + caminata_final * 2
            )

            if puntaje < mejor_puntaje:
                mejor_puntaje = puntaje

                punto_transbordo_geo = a_geojson(p1_m)

                mejor = {
                    "tipo": "transbordo",
                    "linea_1": ruta_origen["nombre"],
                    "linea_2": ruta_destino["nombre"],
                    "puntaje": round(puntaje, 2),
                    "distancias": {
                        "caminata_inicio_m": round(caminata_inicio, 2),
                        "recorrido_bus_1_m": round(recorrido_bus_1, 2),
                        "caminata_transbordo_m": round(caminata_transbordo, 2),
                        "recorrido_bus_2_m": round(recorrido_bus_2, 2),
                        "caminata_final_m": round(caminata_final, 2)
                    },
                    "transbordo": {
                        "lat": punto_transbordo_geo.y,
                        "lon": punto_transbordo_geo.x,
                        "nombre": "Punto de transbordo aproximado"
                    },
                    "tramos_geojson": {
                        "type": "FeatureCollection",
                        "features": [
                            {
                                **tramo_1_geojson,
                                "properties": {
                                    "linea": ruta_origen["nombre"],
                                    "color": "blue"
                                }
                            },
                            {
                                **tramo_2_geojson,
                                "properties": {
                                    "linea": ruta_destino["nombre"],
                                    "color": "red"
                                }
                            }
                        ]
                    }
                }

    return mejor