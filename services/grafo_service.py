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

DISTANCIA_MAX_TRANSBORDO = 30
PENALIZACION_TRANSBORDO = 5000


# ==========================================
# CALCULAR DISTANCIA ENTRE DOS COORDENADAS
# ==========================================

def calcular_distancia(
    lat2,
    lon2,
    lat1,
    lon1
):
    """
    Calcula la distancia en metros entre
    dos coordenadas usando Haversine.
    """

    radio_tierra = 6371000

    lat1 = radians(
        float(lat1)
    )

    lon1 = radians(
        float(lon1)
    )

    lat2 = radians(
        float(lat2)
    )

    lon2 = radians(
        float(lon2)
    )

    diferencia_latitud = (
        lat2 - lat1
    )

    diferencia_longitud = (
        lon2 - lon1
    )

    valor_a = (
        sin(
            diferencia_latitud / 2
        ) ** 2
        +
        cos(lat1)
        *
        cos(lat2)
        *
        sin(
            diferencia_longitud / 2
        ) ** 2
    )

    valor_c = 2 * atan2(
        sqrt(valor_a),
        sqrt(1 - valor_a)
    )

    return (
        radio_tierra * valor_c
    )


# ==========================================
# CALCULAR PESO ENTRE PARADAS
# ==========================================

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


# ==========================================
# CARGAR PARADAS
# ==========================================

def cargar_paradas():
    """
    Carga y devuelve el archivo paradas.json.
    """

    with open(
        RUTA_PARADAS,
        encoding="utf-8"
    ) as archivo:

        return json.load(
            archivo
        )


# ==========================================
# CONSTRUIR GRAFO
# ==========================================

def construir_grafo():

    paradas = cargar_paradas()

    # Grafo dirigido:
    # respeta el orden de las paradas.
    grafo = nx.DiGraph()

    todas_las_paradas = []

    # ======================================
    # CREAR NODOS Y CONEXIONES DE RUTA
    # ======================================

    for ruta, lista_paradas in (
        paradas.items()
    ):

        for indice, parada in enumerate(
            lista_paradas
        ):

            nodo_actual = parada[
                "nombre"
            ]

            grafo.add_node(
                nodo_actual,
                ruta=ruta,
                lat=float(
                    parada["lat"]
                ),
                lon=float(
                    parada["lon"]
                )
            )

            todas_las_paradas.append({
                "nombre":
                    nodo_actual,

                "ruta":
                    ruta,

                "lat":
                    float(
                        parada["lat"]
                    ),

                "lon":
                    float(
                        parada["lon"]
                    )
            })

            if indice > 0:

                parada_anterior = (
                    lista_paradas[
                        indice - 1
                    ]
                )

                nodo_anterior = (
                    parada_anterior[
                        "nombre"
                    ]
                )

                distancia_real = (
                    calcular_peso_ruta(
                        parada_anterior,
                        parada
                    )
                )

                # Al utilizar DiGraph, esta
                # conexión solo funciona desde
                # la parada anterior hacia la actual.
                grafo.add_edge(
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

    # ======================================
    # CREAR TRANSBORDOS AUTOMÁTICOS
    # ======================================

    transbordos_creados = 0

    for indice_a in range(
        len(todas_las_paradas)
    ):

        parada_a = (
            todas_las_paradas[
                indice_a
            ]
        )

        for indice_b in range(
            indice_a + 1,
            len(todas_las_paradas)
        ):

            parada_b = (
                todas_las_paradas[
                    indice_b
                ]
            )

            if (
                parada_a["ruta"]
                ==
                parada_b["ruta"]
            ):
                continue

            distancia = calcular_distancia(
                parada_a["lat"],
                parada_a["lon"],
                parada_b["lat"],
                parada_b["lon"]
            )

            if (
                distancia
                <=
                DISTANCIA_MAX_TRANSBORDO
            ):

                peso_transbordo = (
                    distancia
                    +
                    PENALIZACION_TRANSBORDO
                )

                # A → B
                grafo.add_edge(
                    parada_a["nombre"],
                    parada_b["nombre"],
                    peso=peso_transbordo,
                    tipo="transbordo",
                    distancia_m=round(
                        distancia,
                        2
                    )
                )

                # B → A
                grafo.add_edge(
                    parada_b["nombre"],
                    parada_a["nombre"],
                    peso=peso_transbordo,
                    tipo="transbordo",
                    distancia_m=round(
                        distancia,
                        2
                    )
                )
    
                lineas_revisar = {
                    parada_a["ruta"],
                    parada_b["ruta"]
                }

    

                transbordos_creados += 1

    print(
        f"Transbordos creados: "
        f"{transbordos_creados}"
    )

    print(
        f"Nodos: "
        f"{grafo.number_of_nodes()}"
    )

    print(
        f"Aristas dirigidas: "
        f"{grafo.number_of_edges()}"
    )

    return grafo


# ==========================================
# OBTENER DATOS DE UNA PARADA
# ==========================================

def obtener_datos_parada(
    nombre_parada
):

    paradas = cargar_paradas()

    for ruta, lista_paradas in (
        paradas.items()
    ):

        for parada in lista_paradas:

            if (
                parada["nombre"]
                ==
                nombre_parada
            ):

                return {
                    "ruta":
                        ruta,

                    "nombre":
                        parada[
                            "nombre"
                        ],

                    "lat":
                        float(
                            parada["lat"]
                        ),

                    "lon":
                        float(
                            parada["lon"]
                        )
                }

    return None


# ==========================================
# OBTENER PARADA MÁS CERCANA
# ==========================================

def obtener_parada_mas_cercana(
    latitud,
    longitud
):
    """
    Busca la parada más cercana a una
    coordenada determinada.
    """

    try:
        latitud = float(
            latitud
        )

        longitud = float(
            longitud
        )

    except (TypeError, ValueError):

        return None

    paradas = cargar_paradas()

    parada_mas_cercana = None

    distancia_minima = float(
        "inf"
    )

    for ruta, lista_paradas in (
        paradas.items()
    ):

        for parada in lista_paradas:

            distancia = calcular_distancia(
                latitud,
                longitud,
                parada["lat"],
                parada["lon"]
            )

            if (
                distancia
                <
                distancia_minima
            ):

                distancia_minima = distancia

                parada_mas_cercana = {
                    "ruta":
                        ruta,

                    "nombre":
                        parada[
                            "nombre"
                        ],

                    "lat":
                        float(
                            parada["lat"]
                        ),

                    "lon":
                        float(
                            parada["lon"]
                        ),

                    "distancia_m":
                        round(
                            distancia,
                            2
                        )
                }

    return parada_mas_cercana