import json
import os
import networkx as nx

from math import (
    radians,
    sin,
    cos,
    sqrt,
    atan2
)


DISTANCIA_MAX_TRANSBORDO = 50


# ==================================================
# CARGA OPTIMIZADA DE PARADAS
# ==================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

RUTA_PARADAS = os.path.join(
    BASE_DIR,
    "data",
    "paradas.json"
)

with open(
    RUTA_PARADAS,
    encoding="utf-8"
) as archivo:
    PARADAS = json.load(
        archivo
    )


# Diccionario rápido de búsqueda
PARADAS_INDEXADAS = {}

for linea, lista_paradas in PARADAS.items():
    for parada in lista_paradas:
        PARADAS_INDEXADAS[
            parada["nombre"]
        ] = {
            "ruta": linea,
            "nombre": parada["nombre"],
            "lat": float(parada["lat"]),
            "lon": float(parada["lon"])
        }


# ==================================================
# CÁLCULO DE DISTANCIA
# ==================================================

def calcular_distancia(
    lat1,
    lon1,
    lat2,
    lon2
):
    R = 6371000

    lat1 = radians(float(lat1))
    lon1 = radians(float(lon1))
    lat2 = radians(float(lat2))
    lon2 = radians(float(lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        +
        cos(lat1)
        *
        cos(lat2)
        *
        sin(dlon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return R * c


# ==================================================
# OBTENER LINEA
# ==================================================

def obtener_linea(nombre):
    if " - " in nombre:
        return nombre.split(" - ")[0]

    return nombre


# ==================================================
# CONSTRUIR GRAFO
# ==================================================

def construir_grafo():

    G = nx.DiGraph()

    for linea, lista_paradas in PARADAS.items():

        for parada in lista_paradas:

            nodo = parada["nombre"]

            G.add_node(
                nodo,
                nombre=nodo,
                lat=float(parada["lat"]),
                lon=float(parada["lon"]),
                linea=linea
            )

    crear_conexiones_lineas(
        G,
        PARADAS
    )

    crear_transbordos(
        G
    )

    print("==============================")
    print("Grafo construido correctamente")
    print("Nodos:", G.number_of_nodes())
    print("Aristas:", G.number_of_edges())
    print("==============================")

    return G


# ==================================================
# CONEXIONES ENTRE PARADAS
# ==================================================

def crear_conexiones_lineas(
    G,
    paradas
):

    for linea, lista in paradas.items():

        for i in range(len(lista) - 1):

            origen = lista[i]
            destino = lista[i + 1]

            nodo_origen = origen["nombre"]
            nodo_destino = destino["nombre"]

            distancia = calcular_distancia(
                origen["lat"],
                origen["lon"],
                destino["lat"],
                destino["lon"]
            )

            G.add_edge(
                nodo_origen,
                nodo_destino,
                peso=distancia,
                tipo="ruta",
                linea=linea,
                distancia=distancia
            )


# ==================================================
# CREAR TRANSBORDOS
# ==================================================

def crear_transbordos(G):

    nodos = list(
        G.nodes(data=True)
    )

    cantidad = 0

    for i in range(len(nodos)):

        nodo1, data1 = nodos[i]

        for j in range(i + 1, len(nodos)):

            nodo2, data2 = nodos[j]

            linea1 = data1["linea"]
            linea2 = data2["linea"]

            if linea1 == linea2:
                continue

            distancia = calcular_distancia(
                data1["lat"],
                data1["lon"],
                data2["lat"],
                data2["lon"]
            )

            if distancia <= DISTANCIA_MAX_TRANSBORDO:

                peso = distancia + 10000

                G.add_edge(
                    nodo1,
                    nodo2,
                    peso=peso,
                    tipo="transbordo",
                    distancia=distancia
                )

                G.add_edge(
                    nodo2,
                    nodo1,
                    peso=peso,
                    tipo="transbordo",
                    distancia=distancia
                )

                cantidad += 1

    print(
        "Transbordos creados:",
        cantidad
    )


# ==================================================
# OBTENER DATOS DE UNA PARADA
# ==================================================

def obtener_datos_parada(
    nombre_parada
):

    return PARADAS_INDEXADAS.get(
        nombre_parada
    )


# ==================================================
# CREAR GRAFO GLOBAL
# ==================================================

grafo = construir_grafo()