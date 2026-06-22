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
    return nombre_parada.split(" - ")[0]


def analizar_camino(camino):

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

            segmentos.append({
                "linea": linea_actual,
                "inicio": inicio_segmento,
                "fin": camino[i - 1]
            })

            transbordos += 1

            linea_actual = linea_siguiente
            inicio_segmento = camino[i]

            if linea_actual not in lineas:
                lineas.append(
                    linea_actual
                )

    segmentos.append({
        "linea": linea_actual,
        "inicio": inicio_segmento,
        "fin": camino[-1]
    })

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
    Prioriza menos transbordos.
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

            except nx.NetworkXNoPath:
                continue

    # ==========================================
    # ANALIZAR TRANSBORDOS DE LA MEJOR RUTA
    # ==========================================

    if mejor_ruta:

        print("\nPARADAS DE TRANSBORDO")

        mejor_camino = mejor_ruta["camino"]

        transbordos_info = []

        for i in range(len(mejor_camino) - 1):

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

                distancia = calcular_distancia(
                    parada_a["lat"],
                    parada_a["lon"],
                    parada_b["lat"],
                    parada_b["lon"]
                )

                transbordos_info.append({

                    "linea_origen": linea_a,
                    "linea_destino": linea_b,

                    "parada_salida": mejor_camino[i],
                    "parada_llegada": mejor_camino[i + 1],

                    "lat": parada_a["lat"],
                    "lon": parada_a["lon"],

                    "lat_salida": parada_a["lat"],
                    "lon_salida": parada_a["lon"],

                    "lat_llegada": parada_b["lat"],
                    "lon_llegada": parada_b["lon"],

                    "distancia": round(
                        distancia,
                        2
                    )
                })

                print(
                    f"\nCambio de {linea_a} -> {linea_b}"
                )

                print(
                    f"Última parada: {mejor_camino[i]}"
                )

                print(
                    f"Primera parada: {mejor_camino[i + 1]}"
                )

                print(
                    f"Distancia: {round(distancia, 2)} m"
                )

        mejor_ruta["transbordos_info"] = (
            transbordos_info
        )

    return mejor_ruta