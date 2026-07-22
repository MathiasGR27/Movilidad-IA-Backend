import networkx as nx

from services.caminata_service import generar_caminata
from services.geojson_dijkstra_service import generar_geojson_camino
from services.grafo_service import (
    calcular_distancia,
    construir_grafo,
    obtener_datos_parada,
)
from services.paradas_service import obtener_mejores_paradas

# =====================================================
# GRAFO GLOBAL
# =====================================================

G = construir_grafo()

# =====================================================
# COSTOS
# =====================================================

PENALIZACION_TRANSBORDO = 50000
PENALIZACION_MULTIPLES_TRANSBORDOS = 80000
PENALIZACION_CAMINATA = 5

# =====================================================
# LINEAS ESPECIALES
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
# OBTENER LINEA
# =====================================================

def obtener_linea_parada(nombre):
    if not nombre:
        return ""

    if " - " in nombre:
        return nombre.split(" - ")[0]

    return nombre


# =====================================================
# VALIDAR RUTA 23
# =====================================================

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


# =====================================================
# CREAR SEGMENTO
# =====================================================

def crear_segmento(linea, inicio, fin):
    ini = obtener_datos_parada(inicio)
    final = obtener_datos_parada(fin)

    return {
        "linea": linea,
        "inicio": inicio,
        "fin": fin,
        "inicio_coordenadas": (
            {"lat": float(ini["lat"]), "lon": float(ini["lon"])} if ini else None
        ),
        "fin_coordenadas": (
            {"lat": float(final["lat"]), "lon": float(final["lon"])} if final else None
        ),
    }


# =====================================================
# ANALIZAR CAMINO
# =====================================================

def analizar_camino(camino):
    if not camino:
        return {"lineas": [], "transbordos": 0, "segmentos": []}

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
                    crear_segmento(linea_actual, inicio_segmento, camino[i - 1])
                )
                transbordos += 1
                linea_actual = linea_nueva
                inicio_segmento = camino[i]

                if linea_nueva not in lineas:
                    lineas.append(linea_nueva)

    segmentos.append(
        crear_segmento(linea_actual, inicio_segmento, camino[-1])
    )

    return {
        "lineas": lineas,
        "transbordos": transbordos,
        "segmentos": segmentos,
    }


# =====================================================
# PUNTAJE
# =====================================================

def calcular_puntaje(distancia_bus, transbordos, caminata):
    return (
        distancia_bus
        + (transbordos * PENALIZACION_TRANSBORDO)
        + (caminata * PENALIZACION_CAMINATA)
    )


# =====================================================
# BUSCAR RUTA
# =====================================================

def buscar_ruta_optima(origen, destino):
    paradas_origen = obtener_mejores_paradas(
        origen["lat"], origen["lon"], limite=40, distancia_maxima=800
    )

    paradas_destino = obtener_mejores_paradas(
        destino["lat"], destino["lon"], limite=40, distancia_maxima=800
    )

    mejor = None
    mejor_puntaje = float("inf")
    usar_23 = destino_permite_interprovincial(destino)

    for inicio in paradas_origen:
        for fin in paradas_destino:
            try:
                camino = nx.dijkstra_path(
                    G, inicio["nombre"], fin["nombre"], weight="peso"
                )

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

                caminata = inicio["distancia_m"] + fin["distancia_m"]
                puntaje = calcular_puntaje(
                    distancia_bus, analisis["transbordos"], caminata
                )

                if analisis["transbordos"] >= 2:
                    puntaje += PENALIZACION_MULTIPLES_TRANSBORDOS

                if puntaje < mejor_puntaje:
                    mejor_puntaje = puntaje
                    mejor = {
                        "parada_origen": inicio,
                        "parada_destino": fin,
                        "camino": camino,
                        "total_paradas": len(camino),
                        "lineas_utilizadas": lineas,
                        "cantidad_transbordos": analisis["transbordos"],
                        "segmentos": analisis["segmentos"],
                        "puntaje": puntaje,
                        "geojson": generar_geojson_camino(camino),
                    }

            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue

    if not mejor:
        return None

    # =================================================
    # CAMINATAS
    # =================================================
    if mejor["segmentos"]:
        inicio_bus = mejor["segmentos"][0]["inicio_coordenadas"]
        fin_bus = mejor["segmentos"][-1]["fin_coordenadas"]

        caminar_inicio = generar_caminata(origen, inicio_bus)
        caminar_fin = generar_caminata(fin_bus, destino)

        mejor["caminata_inicio"] = {
            "geojson": {"type": "LineString", "coordinates": caminar_inicio}
        }

        mejor["caminata_fin"] = {
            "geojson": {"type": "LineString", "coordinates": caminar_fin}
        }

    return mejor