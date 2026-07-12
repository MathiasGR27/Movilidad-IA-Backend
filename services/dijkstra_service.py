import networkx as nx

from services.grafo_service import (
    construir_grafo,
    obtener_datos_parada,
    calcular_distancia
)

from services.geojson_dijkstra_service import (
    generar_geojson_camino
)

from services.paradas_service import (
    obtener_mejores_paradas
)


G = construir_grafo()

PENALIZACION_TRANSBORDO = 200


def obtener_linea_parada(nombre_parada):
    """
    Obtiene el nombre de la línea desde el nombre
    completo de una parada.

    Ejemplo:
    LINEA_11A_RETORNO - Parada 13
    devuelve:
    LINEA_11A_RETORNO
    """

    return nombre_parada.split(" - ")[0]


def crear_segmento(
    linea,
    nombre_inicio,
    nombre_fin
):
    """
    Construye un segmento incluyendo los nombres
    y coordenadas de sus paradas inicial y final.
    """

    datos_inicio = obtener_datos_parada(
        nombre_inicio
    )

    datos_fin = obtener_datos_parada(
        nombre_fin
    )

    segmento = {
        "linea": linea,
        "inicio": nombre_inicio,
        "fin": nombre_fin,
        "inicio_coordenadas": None,
        "fin_coordenadas": None
    }

    if datos_inicio:

        segmento["inicio_coordenadas"] = {
            "lat": float(datos_inicio["lat"]),
            "lon": float(datos_inicio["lon"])
        }

    if datos_fin:

        segmento["fin_coordenadas"] = {
            "lat": float(datos_fin["lat"]),
            "lon": float(datos_fin["lon"])
        }

    return segmento


def analizar_camino(camino):
    """
    Divide el camino completo en segmentos por línea
    y determina dónde se realizan los transbordos.
    """

    if not camino:
        return {
            "lineas": [],
            "transbordos": 0,
            "segmentos": []
        }

    lineas = []
    segmentos = []

    linea_actual = obtener_linea_parada(
        camino[0]
    )

    inicio_segmento = camino[0]

    lineas.append(
        linea_actual
    )

    transbordos = 0

    for i in range(1, len(camino)):

        linea_siguiente = obtener_linea_parada(
            camino[i]
        )

        if linea_siguiente != linea_actual:

            segmento = crear_segmento(
                linea=linea_actual,
                nombre_inicio=inicio_segmento,
                nombre_fin=camino[i - 1]
            )

            segmentos.append(
                segmento
            )

            transbordos += 1

            linea_actual = linea_siguiente
            inicio_segmento = camino[i]

            if linea_actual not in lineas:

                lineas.append(
                    linea_actual
                )

    ultimo_segmento = crear_segmento(
        linea=linea_actual,
        nombre_inicio=inicio_segmento,
        nombre_fin=camino[-1]
    )

    segmentos.append(
        ultimo_segmento
    )

    return {
        "lineas": lineas,
        "transbordos": transbordos,
        "segmentos": segmentos
    }


def calcular_puntaje(
    total_paradas,
    transbordos
):
    """
    Prioriza recorridos con menor cantidad de
    transbordos y menor cantidad de paradas.
    """

    return (
        total_paradas
        +
        (
            transbordos
            * PENALIZACION_TRANSBORDO
        )
    )


def buscar_ruta_optima(
    origen,
    destino
):
    """
    Busca las paradas más cercanas al origen y destino,
    calcula las posibles rutas con Dijkstra y selecciona
    la alternativa con mejor puntaje.
    """

    paradas_origen = obtener_mejores_paradas(
        origen["lat"],
        origen["lon"],
        limite=10,
        distancia_maxima=600
    )

    paradas_destino = obtener_mejores_paradas(
        destino["lat"],
        destino["lon"],
        limite=10,
        distancia_maxima=600
    )

    mejor_ruta = None
    mejor_puntaje = float("inf")

    for parada_origen in paradas_origen:

        for parada_destino in paradas_destino:

            try:

                camino = nx.dijkstra_path(
                    G,
                    parada_origen["nombre"],
                    parada_destino["nombre"],
                    weight="peso"
                )

                analisis = analizar_camino(
                    camino
                )

                total_paradas = len(
                    camino
                )

                transbordos = analisis[
                    "transbordos"
                ]

                puntaje = calcular_puntaje(
                    total_paradas,
                    transbordos
                )

                if puntaje < mejor_puntaje:

                    mejor_puntaje = puntaje

                    geojson = generar_geojson_camino(
                        camino
                    )

                    mejor_ruta = {
                        "parada_origen":
                            parada_origen,

                        "parada_destino":
                            parada_destino,

                        "camino":
                            camino,

                        "total_paradas":
                            total_paradas,

                        "lineas_utilizadas":
                            analisis["lineas"],

                        "cantidad_transbordos":
                            transbordos,

                        "segmentos":
                            analisis["segmentos"],

                        "puntaje":
                            puntaje,

                        "geojson":
                            geojson
                    }

            except (
                nx.NetworkXNoPath,
                nx.NodeNotFound
            ):
                continue

    # ==========================================
    # ANALIZAR TRANSBORDOS DE LA MEJOR RUTA
    # ==========================================

    if mejor_ruta:

        print("\nPARADAS DE TRANSBORDO")

        mejor_camino = mejor_ruta["camino"]

        transbordos_info = []

        for i in range(
            len(mejor_camino) - 1
        ):

            linea_a = obtener_linea_parada(
                mejor_camino[i]
            )

            linea_b = obtener_linea_parada(
                mejor_camino[i + 1]
            )

            if linea_a != linea_b:

                parada_a = obtener_datos_parada(
                    mejor_camino[i]
                )

                parada_b = obtener_datos_parada(
                    mejor_camino[i + 1]
                )

                if not parada_a or not parada_b:
                    continue

                distancia = calcular_distancia(
                    parada_a["lat"],
                    parada_a["lon"],
                    parada_b["lat"],
                    parada_b["lon"]
                )

                transbordos_info.append({
                    "linea_origen":
                        linea_a,

                    "linea_destino":
                        linea_b,

                    "parada_salida":
                        mejor_camino[i],

                    "parada_llegada":
                        mejor_camino[i + 1],

                    "lat":
                        float(parada_a["lat"]),

                    "lon":
                        float(parada_a["lon"]),

                    "lat_salida":
                        float(parada_a["lat"]),

                    "lon_salida":
                        float(parada_a["lon"]),

                    "lat_llegada":
                        float(parada_b["lat"]),

                    "lon_llegada":
                        float(parada_b["lon"]),

                    "distancia":
                        round(distancia, 2)
                })

                print(
                    f"\nCambio de "
                    f"{linea_a} -> {linea_b}"
                )

                print(
                    f"Última parada: "
                    f"{mejor_camino[i]}"
                )

                print(
                    f"Primera parada: "
                    f"{mejor_camino[i + 1]}"
                )

                print(
                    f"Distancia: "
                    f"{round(distancia, 2)} m"
                )

        mejor_ruta["transbordos_info"] = (
            transbordos_info
        )

        # Coordenadas necesarias para dibujar
        # los recorridos caminando.

        segmentos = mejor_ruta.get(
            "segmentos",
            []
        )

        primera_parada = (
            segmentos[0].get(
                "inicio_coordenadas"
            )
            if segmentos
            else None
        )

        ultima_parada = (
            segmentos[-1].get(
                "fin_coordenadas"
            )
            if segmentos
            else None
        )

        mejor_ruta["caminata_inicio"] = {
            "origen": {
                "lat": float(origen["lat"]),
                "lon": float(origen["lon"])
            },
            "parada": primera_parada
        }

        mejor_ruta["caminata_fin"] = {
            "parada": ultima_parada,
            "destino": {
                "lat": float(destino["lat"]),
                "lon": float(destino["lon"])
            }
        }

    return mejor_ruta