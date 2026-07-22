import json
import os
from math import atan2, cos, radians, sin, sqrt

import networkx as nx

# =====================================================
# CONFIGURACIÓN
# =====================================================

# distancia máxima caminando entre paradas
DISTANCIA_MAX_TRANSBORDO = 40

# costo fuerte de cambiar de bus
COSTO_BASE_TRANSBORDO = 30000


# =====================================================
# CARGA DE PARADAS
# =====================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_PARADAS = os.path.join(BASE_DIR, "data", "paradas.json")

with open(RUTA_PARADAS, encoding="utf-8") as archivo:
    PARADAS = json.load(archivo)


# =====================================================
# INDICE DE PARADAS
# =====================================================

PARADAS_INDEXADAS = {}

for linea, lista in PARADAS.items():
    for parada in lista:
        PARADAS_INDEXADAS[parada["nombre"]] = {
            "ruta": linea,
            "nombre": parada["nombre"],
            "lat": float(parada["lat"]),
            "lon": float(parada["lon"]),
        }


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

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


# =====================================================
# OBTENER LINEA
# =====================================================

def obtener_linea(nombre):
    if " - " in nombre:
        return nombre.split(" - ")[0]
    return nombre


# =====================================================
# CREAR NODOS
# =====================================================

def crear_nodos(G):
    for linea, lista in PARADAS.items():
        for parada in lista:
            nombre = parada["nombre"]
            G.add_node(
                nombre,
                nombre=nombre,
                linea=linea,
                lat=float(parada["lat"]),
                lon=float(parada["lon"]),
            )


# =====================================================
# CONEXIONES MISMA LINEA
# =====================================================

def crear_conexiones_lineas(G):
    for linea, lista in PARADAS.items():
        for i in range(len(lista) - 1):
            actual = lista[i]
            siguiente = lista[i + 1]

            origen = actual["nombre"]
            destino = siguiente["nombre"]

            distancia = calcular_distancia(
                actual["lat"], actual["lon"], siguiente["lat"], siguiente["lon"]
            )

            G.add_edge(
                origen,
                destino,
                peso=distancia,
                distancia=distancia,
                tipo="ruta",
                linea=linea,
            )


# =====================================================
# CREAR TRANSBORDOS
# =====================================================

def crear_transbordos(G):
    nodos = list(G.nodes(data=True))
    cantidad = 0

    for i in range(len(nodos)):
        nodo1, datos1 = nodos[i]

        for j in range(i + 1, len(nodos)):
            nodo2, datos2 = nodos[j]

            linea1 = datos1["linea"]
            linea2 = datos2["linea"]

            # misma línea no cambia
            if linea1 == linea2:
                continue

            distancia = calcular_distancia(
                datos1["lat"], datos1["lon"], datos2["lat"], datos2["lon"]
            )

            if distancia <= DISTANCIA_MAX_TRANSBORDO:
                peso = distancia + COSTO_BASE_TRANSBORDO

                G.add_edge(
                    nodo1,
                    nodo2,
                    peso=peso,
                    distancia=distancia,
                    tipo="transbordo",
                    linea_origen=linea1,
                    linea_destino=linea2,
                )

                G.add_edge(
                    nodo2,
                    nodo1,
                    peso=peso,
                    distancia=distancia,
                    tipo="transbordo",
                    linea_origen=linea2,
                    linea_destino=linea1,
                )

                cantidad += 1

    print("Transbordos creados:", cantidad)


# =====================================================
# CONSTRUIR GRAFO
# =====================================================

def construir_grafo():
    G = nx.DiGraph()

    crear_nodos(G)
    crear_conexiones_lineas(G)
    crear_transbordos(G)

    print("==============================")
    print("Grafo construido correctamente")
    print("Nodos:", G.number_of_nodes())
    print("Aristas:", G.number_of_edges())
    print("==============================")

    return G


# =====================================================
# OBTENER DATOS PARADA
# =====================================================

def obtener_datos_parada(nombre):
    return PARADAS_INDEXADAS.get(nombre)


# =====================================================
# GRAFO GLOBAL
# =====================================================

grafo = construir_grafo()