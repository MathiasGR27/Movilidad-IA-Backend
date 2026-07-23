import json
import os
from math import atan2, cos, radians, sin, sqrt

import networkx as nx

# =====================================================
# CONFIGURACIÓN
# =====================================================

DISTANCIA_MAX_TRANSBORDO = 40
COSTO_BASE_TRANSBORDO = 30000

# =====================================================
# CARGA
# =====================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_PARADAS = os.path.join(BASE_DIR, "data", "paradas.json")

with open(RUTA_PARADAS, encoding="utf-8") as archivo:
    PARADAS = json.load(archivo)


# =====================================================
# SENTIDO
# =====================================================


def obtener_sentido(linea):
    linea = linea.upper()

    if "IDA" in linea:
        return "IDA"

    if "RETORNO" in linea or "REGRESO" in linea:
        return "RETORNO"

    return "DESCONOCIDO"


# =====================================================
# INDEXADO
# =====================================================

PARADAS_INDEXADAS = {}

for linea, lista in PARADAS.items():
    for parada in lista:
        PARADAS_INDEXADAS[parada["nombre"]] = {
            "ruta": linea,
            "nombre": parada["nombre"],
            "lat": float(parada["lat"]),
            "lon": float(parada["lon"]),
            "sentido": obtener_sentido(linea),
        }


# =====================================================
# DISTANCIA
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
                sentido=obtener_sentido(linea),
                lat=float(parada["lat"]),
                lon=float(parada["lon"]),
            )


# =====================================================
# CONEXIONES
# =====================================================


def crear_conexiones_lineas(G):
    for linea, lista in PARADAS.items():
        for i in range(len(lista) - 1):
            actual = lista[i]
            siguiente = lista[i + 1]

            origen = actual["nombre"]
            destino = siguiente["nombre"]

            distancia = calcular_distancia(
                actual["lat"],
                actual["lon"],
                siguiente["lat"],
                siguiente["lon"],
            )

            G.add_edge(
                origen,
                destino,
                peso=distancia,
                distancia=distancia,
                tipo="ruta",
                linea=linea,
                sentido=obtener_sentido(linea),
            )


# =====================================================
# TRANSBORDOS
# =====================================================


def crear_transbordos(G):
    nodos = list(G.nodes(data=True))
    cantidad = 0

    for i in range(len(nodos)):
        nodo1, datos1 = nodos[i]

        for j in range(i + 1, len(nodos)):
            nodo2, datos2 = nodos[j]

            if datos1["linea"] == datos2["linea"]:
                continue

            distancia = calcular_distancia(
                datos1["lat"],
                datos1["lon"],
                datos2["lat"],
                datos2["lon"],
            )

            if distancia <= DISTANCIA_MAX_TRANSBORDO:
                peso = distancia + COSTO_BASE_TRANSBORDO

                G.add_edge(
                    nodo1,
                    nodo2,
                    peso=peso,
                    distancia=distancia,
                    tipo="transbordo",
                    linea_origen=datos1["linea"],
                    linea_destino=datos2["linea"],
                )

                G.add_edge(
                    nodo2,
                    nodo1,
                    peso=peso,
                    distancia=distancia,
                    tipo="transbordo",
                    linea_origen=datos2["linea"],
                    linea_destino=datos1["linea"],
                )

                cantidad += 1

    print("Transbordos creados:", cantidad)


# =====================================================
# CONSTRUIR
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
# DATOS PARADA
# =====================================================
def obtener_datos_parada(nombre):
    return PARADAS_INDEXADAS.get(nombre)


grafo = construir_grafo()