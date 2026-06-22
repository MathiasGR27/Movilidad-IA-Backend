import json
import os

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

RUTA_PARADAS = os.path.join(
    BASE_DIR,
    "data",
    "paradas.json"
)


def obtener_linea_parada(nombre_parada):
    return nombre_parada.split(" - ")[0]


def cargar_indice_paradas():
    with open(RUTA_PARADAS, encoding="utf-8") as f:
        paradas = json.load(f)

    indice = {}

    for ruta, lista_paradas in paradas.items():
        for parada in lista_paradas:
            indice[parada["nombre"]] = {
                "lat": parada["lat"],
                "lon": parada["lon"],
                "ruta": ruta
            }

    return indice


def color_por_indice(index):
    colores = [
        "blue",
        "red",
        "green",
        "purple",
        "orange"
    ]

    return colores[index % len(colores)]


def generar_geojson_camino(camino):
    indice_paradas = cargar_indice_paradas()

    features = []

    if not camino or len(camino) < 2:
        return None

    segmento_actual = []
    linea_actual = obtener_linea_parada(camino[0])
    color_index = 0

    for nombre_parada in camino:
        datos = indice_paradas.get(nombre_parada)

        if not datos:
            continue

        linea = obtener_linea_parada(nombre_parada)

        coordenada = [
            datos["lon"],
            datos["lat"]
        ]

        if linea != linea_actual and len(segmento_actual) >= 2:
            features.append({
                "type": "Feature",
                "properties": {
                    "tipo": "ruta_dijkstra",
                    "linea": linea_actual,
                    "color": color_por_indice(color_index)
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": segmento_actual
                }
            })

            color_index += 1
            segmento_actual = [coordenada]
            linea_actual = linea

        else:
            segmento_actual.append(coordenada)

    if len(segmento_actual) >= 2:
        features.append({
            "type": "Feature",
            "properties": {
                "tipo": "ruta_dijkstra",
                "linea": linea_actual,
                "color": color_por_indice(color_index)
            },
            "geometry": {
                "type": "LineString",
                "coordinates": segmento_actual
            }
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }