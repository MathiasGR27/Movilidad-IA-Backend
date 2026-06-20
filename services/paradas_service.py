import json
import os
from math import radians, sin, cos, sqrt, atan2


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

RUTA_PARADAS = os.path.join(
    BASE_DIR,
    "data",
    "paradas.json"
)


with open(RUTA_PARADAS, encoding="utf-8") as f:
    PARADAS = json.load(f)


def calcular_distancia(lat1, lon1, lat2, lon2):
    """
    Distancia entre dos coordenadas en metros
    usando fórmula de Haversine
    """

    R = 6371000

    lat1 = radians(lat1)
    lon1 = radians(lon1)

    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return R * c


def obtener_paradas_ruta(nombre_ruta):
    """
    Devuelve todas las paradas de una ruta
    """

    return PARADAS.get(nombre_ruta, [])


def buscar_parada_mas_cercana(lat, lon):
    """
    Busca la parada más cercana
    entre todas las rutas
    """

    mejor_parada = None
    mejor_distancia = float("inf")

    for ruta, paradas in PARADAS.items():

        for parada in paradas:

            distancia = calcular_distancia(
                lat,
                lon,
                parada["lat"],
                parada["lon"]
            )

            if distancia < mejor_distancia:

                mejor_distancia = distancia

                mejor_parada = {
                    "ruta": ruta,
                    "nombre": parada["nombre"],
                    "lat": parada["lat"],
                    "lon": parada["lon"],
                    "distancia_m": round(
                        distancia,
                        2
                    )
                }

    return mejor_parada


def buscar_paradas_cercanas(
    lat,
    lon,
    radio_metros=500
):
    """
    Devuelve todas las paradas
    dentro de un radio determinado
    """

    resultado = []

    for ruta, paradas in PARADAS.items():

        for parada in paradas:

            distancia = calcular_distancia(
                lat,
                lon,
                parada["lat"],
                parada["lon"]
            )

            if distancia <= radio_metros:

                resultado.append({
                    "ruta": ruta,
                    "nombre": parada["nombre"],
                    "lat": parada["lat"],
                    "lon": parada["lon"],
                    "distancia_m": round(
                        distancia,
                        2
                    )
                })

    resultado.sort(
        key=lambda x: x["distancia_m"]
    )

    return resultado


def buscar_paradas_ruta(
    nombre_ruta,
    lat,
    lon,
    radio_metros=500
):
    """
    Busca paradas cercanas
    únicamente dentro de una ruta
    """

    resultado = []

    paradas = obtener_paradas_ruta(
        nombre_ruta
    )

    for parada in paradas:

        distancia = calcular_distancia(
            lat,
            lon,
            parada["lat"],
            parada["lon"]
        )

        if distancia <= radio_metros:

            resultado.append({
                **parada,
                "distancia_m": round(
                    distancia,
                    2
                )
            })

    resultado.sort(
        key=lambda x: x["distancia_m"]
    )

    return resultado


def obtener_rutas_cercanas(
    lat,
    lon,
    radio_metros=500
):
    """
    Devuelve rutas que tienen
    al menos una parada cercana
    """

    rutas = set()

    paradas = buscar_paradas_cercanas(
        lat,
        lon,
        radio_metros
    )

    for parada in paradas:
        rutas.add(
            parada["ruta"]
        )

    return list(rutas)

def obtener_mejores_rutas(
    lat,
    lon,
    limite=5
):
    """
    Devuelve las rutas más cercanas
    al punto indicado.
    """

    mejores = {}

    for ruta, paradas in PARADAS.items():

        menor = float("inf")

        for parada in paradas:

            distancia = calcular_distancia(
                lat,
                lon,
                parada["lat"],
                parada["lon"]
            )

            if distancia < menor:
                menor = distancia

        mejores[ruta] = menor

    rutas_ordenadas = sorted(
        mejores.items(),
        key=lambda x: x[1]
    )

    return [
        {
            "ruta": ruta,
            "distancia_m": round(distancia, 2)
        }
        for ruta, distancia
        in rutas_ordenadas[:limite]
    ]