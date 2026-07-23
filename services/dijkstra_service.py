import logging

import networkx as nx

from services.caminata_service import (
    calcular_distancias_caminata_batch,
    generar_caminata,
)
from services.geojson_dijkstra_service import generar_geojson_camino
from services.grafo_service import construir_grafo, obtener_datos_parada
from services.paradas_service import obtener_mejores_paradas

logger = logging.getLogger(__name__)

# =====================================================
# GRAFO GLOBAL
# =====================================================

G = construir_grafo()

# =====================================================
# COSTOS
# =====================================================

PENALIZACION_TRANSBORDO = 50000
PENALIZACION_MULTIPLES_TRANSBORDOS = 80000
PENALIZACION_CAMINATA = 10

# =====================================================
# LINEAS INTERPROVINCIALES
# =====================================================

LINEAS_INTERPROVINCIALES = [
    "RUTA_23_INTERPROVINCIAL_IDA",
    "RUTA_23_INTERPROVINCIAL_REGRESO",
    "RUTA_23_INTERPROVINCIAL",
]

DESTINOS_PERMITIDOS_INTERPROVINCIAL = [
    "luz de america",
    "espe",
    "universidad espe",
    "escuela superior politecnica del ejercito",
]


# =====================================================
# FUNCIONES AUXILIARES
# =====================================================


def obtener_linea_parada(nombre):
    if not nombre:
        return ""

    if " - " in nombre:
        return nombre.split(" - ")[0]

    return nombre


def destino_permite_interprovincial(destino):
    if not destino:
        return False

    texto = (
        destino.get("nombre", "").lower()
        + " "
        + " ".join(destino.get("alias", [])).lower()
    )

    for permitido in DESTINOS_PERMITIDOS_INTERPROVINCIAL:
        if permitido in texto:
            return True

    return False


def crear_segmento(linea, inicio, fin):
    ini = obtener_datos_parada(inicio)
    final = obtener_datos_parada(fin)

    return {
        "linea": linea,
        "inicio": inicio,
        "fin": fin,
        "inicio_coordenadas": (
            {
                "lat": float(ini["lat"]),
                "lon": float(ini["lon"]),
            }
            if ini
            else None
        ),
        "fin_coordenadas": (
            {
                "lat": float(final["lat"]),
                "lon": float(final["lon"]),
            }
            if final
            else None
        ),
    }


# =====================================================
# ANALIZAR CAMINO
# =====================================================


def analizar_camino(camino):
    if not camino:
        return {
            "lineas": [],
            "transbordos": 0,
            "segmentos": [],
        }

    lineas = []
    segmentos = []

    linea_actual = obtener_linea_parada(camino[0])
    inicio_segmento = camino[0]
    lineas.append(linea_actual)

    transbordos = 0

    for i in range(1, len(camino)):
        linea_nueva = obtener_linea_parada(camino[i])

        if linea_nueva != linea_actual:
            edge = G.get_edge_data(camino[i - 1], camino[i])

            if edge and edge.get("tipo") == "transbordo":
                segmentos.append(
                    crear_segmento(
                        linea_actual,
                        inicio_segmento,
                        camino[i - 1],
                    )
                )

                transbordos += 1
                linea_actual = linea_nueva
                inicio_segmento = camino[i]

                if linea_nueva not in lineas:
                    lineas.append(linea_nueva)

    segmentos.append(
        crear_segmento(
            linea_actual,
            inicio_segmento,
            camino[-1],
        )
    )

    return {
        "lineas": lineas,
        "transbordos": transbordos,
        "segmentos": segmentos,
    }


# =====================================================
# CALCULAR CAMINATAS (2 peticiones HTTP en vez de 40)
# =====================================================


def _calcular_caminatas_candidatas(origen, destino, paradas_origen, paradas_destino):
    puntos_origen = [{"lat": p["lat"], "lon": p["lon"]} for p in paradas_origen]
    distancias_origen = calcular_distancias_caminata_batch(
        origen, puntos_origen, punto_fijo_es_origen=True
    )

    for parada, distancia in zip(paradas_origen, distancias_origen):
        parada["caminata_real"] = (
            distancia if distancia != 999999 else parada["distancia_m"]
        )

    puntos_destino = [{"lat": p["lat"], "lon": p["lon"]} for p in paradas_destino]
    distancias_destino = calcular_distancias_caminata_batch(
        destino, puntos_destino, punto_fijo_es_origen=False
    )

    for parada, distancia in zip(paradas_destino, distancias_destino):
        parada["caminata_real"] = (
            distancia if distancia != 999999 else parada["distancia_m"]
        )


# =====================================================
# BUSCAR RUTA OPTIMA
# =====================================================


def buscar_ruta_optima(origen, destino):
    # ==========================================
    # OBTENER CANDIDATAS
    # ==========================================

    paradas_origen = obtener_mejores_paradas(
        origen["lat"],
        origen["lon"],
        limite=20,
        distancia_maxima=800,
    )

    paradas_destino = obtener_mejores_paradas(
        destino["lat"],
        destino["lon"],
        limite=20,
        distancia_maxima=800,
    )

    logger.debug("Paradas candidatas origen: %s", paradas_origen)

    if not paradas_origen or not paradas_destino:
        return None

    # ==========================================
    # CALCULAR CAMINATAS (2 peticiones en total)
    # ==========================================

    _calcular_caminatas_candidatas(origen, destino, paradas_origen, paradas_destino)

    # ==========================================
    # DIJKSTRA
    # ==========================================
    #
    # En vez de correr dijkstra_path para cada combinacion
    # (origen x destino = hasta 400 corridas), se corre UNA
    # sola vez single_source_dijkstra por cada parada de origen
    # (maximo 20 corridas), obteniendo de una vez los caminos
    # hacia TODOS los nodos del grafo. De ahi se extrae el
    # camino hacia cada parada de destino candidata.
    # ==========================================

    mejor = None
    mejor_puntaje = float("inf")
    mejor_camino = None
    usar_23 = destino_permite_interprovincial(destino)

    for inicio in paradas_origen:
        try:
            _, caminos = nx.single_source_dijkstra(
                G, inicio["nombre"], weight="peso"
            )
        except nx.NodeNotFound:
            continue

        for fin in paradas_destino:
            camino = caminos.get(fin["nombre"])

            if camino is None:
                continue

            analisis = analizar_camino(camino)
            lineas = analisis["lineas"]

            if not usar_23:
                if any(linea in LINEAS_INTERPROVINCIALES for linea in lineas):
                    continue

            distancia_bus = 0
            for i in range(len(camino) - 1):
                edge = G.get_edge_data(camino[i], camino[i + 1])
                if edge:
                    distancia_bus += edge.get("distancia", 0)

            caminata = inicio["caminata_real"] + fin["caminata_real"]

            puntaje = (
                distancia_bus
                + (analisis["transbordos"] * PENALIZACION_TRANSBORDO)
                + (caminata * PENALIZACION_CAMINATA)
            )

            if analisis["transbordos"] >= 2:
                puntaje += PENALIZACION_MULTIPLES_TRANSBORDOS

            if puntaje < mejor_puntaje:
                mejor_puntaje = puntaje
                mejor_camino = camino

                logger.debug(
                    "Nueva mejor ruta: lineas=%s subida=%s bajada=%s "
                    "caminata=%s bus=%s puntaje=%s",
                    lineas,
                    inicio["nombre"],
                    fin["nombre"],
                    caminata,
                    distancia_bus,
                    puntaje,
                )

                mejor = {
                    "parada_origen": inicio,
                    "parada_destino": fin,
                    "camino": camino,
                    "total_paradas": len(camino),
                    "lineas_utilizadas": lineas,
                    "cantidad_transbordos": analisis["transbordos"],
                    "segmentos": analisis["segmentos"],
                    "puntaje": puntaje,
                }

    if not mejor:
        return None

    # Solo se genera el geojson UNA vez, para la ruta ganadora
    mejor["geojson"] = generar_geojson_camino(mejor_camino)

    # ==========================================
    # GENERAR LINEAS CAMINANDO PARA MAPA
    # ==========================================

    if mejor["segmentos"]:
        inicio_bus = mejor["segmentos"][0]["inicio_coordenadas"]
        fin_bus = mejor["segmentos"][-1]["fin_coordenadas"]

        caminar_inicio = generar_caminata(origen, inicio_bus)
        caminar_fin = generar_caminata(fin_bus, destino)

        mejor["caminata_inicio"] = {
            "geojson": {
                "type": "LineString",
                "coordinates": caminar_inicio,
            }
        }

        mejor["caminata_fin"] = {
            "geojson": {
                "type": "LineString",
                "coordinates": caminar_fin,
            }
        }

    return mejor
