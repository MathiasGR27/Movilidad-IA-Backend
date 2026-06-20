import json
import os
import networkx as nx
from math import radians, sin, cos, sqrt, atan2

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

RUTA_PARADAS = os.path.join(
    BASE_DIR,
    "data",
    "paradas.json"
)

DISTANCIA_MAX_TRANSBORDO = 50
PENALIZACION_TRANSBORDO = 5000


def calcular_distancia(lat1, lon1, lat2, lon2):

    R = 6371000

    lat1 = radians(lat1)
    lon1 = radians(lon1)

    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2 +
        cos(lat1) *
        cos(lat2) *
        sin(dlon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return R * c


def calcular_peso_ruta(
    parada_a,
    parada_b
):
    return calcular_distancia(
        parada_a["lat"],
        parada_a["lon"],
        parada_b["lat"],
        parada_b["lon"]
    )


def construir_grafo():

    with open(
        RUTA_PARADAS,
        encoding="utf-8"
    ) as f:

        paradas = json.load(f)

    G = nx.Graph()

    todas_las_paradas = []

    # ==================================
    # CREAR NODOS Y CONEXIONES DE RUTA
    # ==================================

    for ruta, lista_paradas in paradas.items():

        for i in range(len(lista_paradas)):

            parada = lista_paradas[i]

            nodo_actual = parada["nombre"]

            G.add_node(
                nodo_actual,
                ruta=ruta,
                lat=parada["lat"],
                lon=parada["lon"]
            )

            todas_las_paradas.append({
                "nombre": nodo_actual,
                "ruta": ruta,
                "lat": parada["lat"],
                "lon": parada["lon"]
            })

            if i > 0:

                parada_anterior = lista_paradas[i - 1]

                nodo_anterior = parada_anterior["nombre"]

                distancia_real = calcular_peso_ruta(
                    parada_anterior,
                    parada
                )

                G.add_edge(
                    nodo_anterior,
                    nodo_actual,
                    peso=distancia_real,
                    tipo="ruta",
                    ruta=ruta,
                    distancia_m=round(
                        distancia_real,
                        2
                    )
                )

    # ==================================
    # CREAR TRANSBORDOS AUTOMÁTICOS
    # ==================================

    transbordos_creados = 0

    for i in range(len(todas_las_paradas)):

        parada_a = todas_las_paradas[i]

        for j in range(i + 1, len(todas_las_paradas)):

            parada_b = todas_las_paradas[j]

            if parada_a["ruta"] == parada_b["ruta"]:
                continue

            distancia = calcular_distancia(
                parada_a["lat"],
                parada_a["lon"],
                parada_b["lat"],
                parada_b["lon"]
            )

            if distancia <= DISTANCIA_MAX_TRANSBORDO:

                peso_transbordo = (
                    distancia +
                    PENALIZACION_TRANSBORDO
                )

                G.add_edge(
                    parada_a["nombre"],
                    parada_b["nombre"],
                    peso=peso_transbordo,
                    tipo="transbordo",
                    distancia_m=round(
                        distancia,
                        2
                    )
                )

                transbordos_creados += 1

    print(
        f"Transbordos creados: {transbordos_creados}"
    )

    print(
        f"Nodos: {G.number_of_nodes()}"
    )

    print(
        f"Aristas: {G.number_of_edges()}"
    )

    return G