import json
import os
from math import atan2, cos, radians, sin, sqrt

# =====================================================
# CONFIGURACIÓN
# =====================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_PARADAS = os.path.join(BASE_DIR, "data", "paradas.json")

with open(RUTA_PARADAS, encoding="utf-8") as archivo:
    PARADAS = json.load(archivo)


# =====================================================
# DISTANCIA HAVERSINE
# =====================================================

def calcular_distancia(lat1, lon1, lat2, lon2):
    R = 6371000

    lat1 = radians(float(lat1))
    lon1 = radians(float(lon1))
    lat2 = radians(float(lat2))
    lon2 = radians(float(lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


# =====================================================
# OBTENER PARADAS DE UNA LINEA
# =====================================================

def obtener_paradas_ruta(nombre_ruta):
    return PARADAS.get(nombre_ruta, [])


# =====================================================
# PARADA MAS CERCANA
# =====================================================

def buscar_parada_mas_cercana(lat, lon):
    mejor = None
    menor = float("inf")

    for ruta, lista in PARADAS.items():
        for parada in lista:
            distancia = calcular_distancia(
                lat, lon, parada["lat"], parada["lon"]
            )

            if distancia < menor:
                menor = distancia
                mejor = {
                    "ruta": ruta,
                    "nombre": parada["nombre"],
                    "lat": float(parada["lat"]),
                    "lon": float(parada["lon"]),
                    "distancia_m": round(distancia, 2),
                }

    return mejor


# =====================================================
# PARADAS CERCANAS
# =====================================================

def buscar_paradas_cercanas(lat, lon, radio_metros=700):
    resultado = []

    for ruta, lista in PARADAS.items():
        for parada in lista:
            distancia = calcular_distancia(
                lat, lon, parada["lat"], parada["lon"]
            )

            if distancia <= radio_metros:
                resultado.append({
                    "ruta": ruta,
                    "nombre": parada["nombre"],
                    "lat": float(parada["lat"]),
                    "lon": float(parada["lon"]),
                    "distancia_m": round(distancia, 2),
                })

    resultado.sort(key=lambda x: x["distancia_m"])
    return resultado


# =====================================================
# RUTAS CERCANAS
# =====================================================

def obtener_rutas_cercanas(lat, lon, radio_metros=700):
    rutas = set()
    paradas = buscar_paradas_cercanas(lat, lon, radio_metros)

    for parada in paradas:
        rutas.add(parada["ruta"])

    return list(rutas)


# =====================================================
# MEJORES RUTAS
# =====================================================

def obtener_mejores_rutas(lat, lon, limite=5):
    resultado = []

    for ruta, lista in PARADAS.items():
        menor = float("inf")

        for parada in lista:
            distancia = calcular_distancia(
                lat, lon, parada["lat"], parada["lon"]
            )

            if distancia < menor:
                menor = distancia

        resultado.append({
            "ruta": ruta,
            "distancia_m": round(menor, 2),
        })

    resultado.sort(key=lambda x: x["distancia_m"])
    return resultado[:limite]


# =====================================================
# FUNCION PRINCIPAL PARA DIJKSTRA
# =====================================================

def obtener_mejores_paradas(lat, lon, limite=50, distancia_maxima=1000):
    """
    Devuelve candidatos de subida.

    IMPORTANTE:
    NO selecciona la parada final.
    Solo entrega opciones para que
    Dijkstra evalúe la mejor ruta.
    """
    resultado = []

    for ruta, lista in PARADAS.items():
        for parada in lista:
            distancia = calcular_distancia(
                lat, lon, parada["lat"], parada["lon"]
            )

            if distancia <= distancia_maxima:
                resultado.append({
                    "ruta": ruta,
                    "nombre": parada["nombre"],
                    "lat": float(parada["lat"]),
                    "lon": float(parada["lon"]),
                    "distancia_m": round(distancia, 2),
                })

    # Primero las cercanas
    resultado.sort(key=lambda x: x["distancia_m"])
    return resultado[:limite]


# =====================================================
# MEJORES PARADAS POR RUTA
# =====================================================

def obtener_mejores_paradas_por_ruta(lat, lon, limite_rutas=10):
    resultado = []

    for ruta, lista in PARADAS.items():
        for parada in lista:
            distancia = calcular_distancia(
                lat, lon, parada["lat"], parada["lon"]
            )

            resultado.append({
                "ruta": ruta,
                "nombre": parada["nombre"],
                "lat": float(parada["lat"]),
                "lon": float(parada["lon"]),
                "distancia_m": round(distancia, 2),
            })

    resultado.sort(key=lambda x: x["distancia_m"])
    return resultado[:limite_rutas]
