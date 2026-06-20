import networkx as nx

from services.grafo_service import construir_grafo
from services.paradas_service import buscar_parada_mas_cercana


G = construir_grafo()


def obtener_linea_parada(nombre_parada):
    return nombre_parada.split(" - ")[0]


def analizar_camino(camino):

    lineas = []
    segmentos = []

    linea_actual = obtener_linea_parada(
        camino[0]
    )

    inicio_segmento = camino[0]

    lineas.append(linea_actual)

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
                lineas.append(linea_actual)

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


def buscar_ruta_optima(origen, destino):

    parada_origen = buscar_parada_mas_cercana(
        origen["lat"],
        origen["lon"]
    )

    parada_destino = buscar_parada_mas_cercana(
        destino["lat"],
        destino["lon"]
    )

    if not parada_origen:
        return None

    if not parada_destino:
        return None

    nodo_inicio = parada_origen["nombre"]
    nodo_fin = parada_destino["nombre"]

    try:

        camino = nx.dijkstra_path(
            G,
            nodo_inicio,
            nodo_fin,
            weight="peso"
        )

        analisis = analizar_camino(
            camino
        )

        return {
            "parada_origen": parada_origen,
            "parada_destino": parada_destino,
            "camino": camino,
            "total_paradas": len(camino),
            "lineas_utilizadas": analisis["lineas"],
            "cantidad_transbordos": analisis["transbordos"],
            "segmentos": analisis["segmentos"]
        }

    except nx.NetworkXNoPath:
        return None