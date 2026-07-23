import requests

OSRM_BASE_URL = "https://router.project-osrm.org"
TIMEOUT = 10

# Valor centinela cuando OSRM no puede calcular una ruta
DISTANCIA_NO_DISPONIBLE = 999999


# ==========================================
# GENERAR CAMINATA REAL POR CALLES
# ==========================================

def generar_caminata(origen, destino):
    """
    Devuelve la geometría (lista de coordenadas [lon, lat]) de la
    caminata real entre origen y destino, siguiendo calles.
    Se usa solo para dibujar la línea en el mapa (un par a la vez).
    """
    try:
        url = (
            f"{OSRM_BASE_URL}/route/v1/foot/"
            f"{origen['lon']},{origen['lat']};"
            f"{destino['lon']},{destino['lat']}"
            "?overview=full"
            "&geometries=geojson"
        )

        respuesta = requests.get(url, timeout=TIMEOUT)
        datos = respuesta.json()

        if "routes" not in datos or not datos["routes"]:
            return []

        return datos["routes"][0]["geometry"]["coordinates"]

    except Exception as error:
        print("Error generando caminata:", error)
        return []


# ==========================================
# DISTANCIA REAL DE CAMINATA (UN SOLO PAR)
# ==========================================

def calcular_distancia_caminata(origen, destino):
    """
    Devuelve la distancia caminando (en metros) entre un origen
    y un destino puntual. Mantiene la firma original para no romper
    otros usos existentes, pero para múltiples paradas es preferible
    usar calcular_distancias_caminata_batch (una sola petición HTTP).
    """
    try:
        url = (
            f"{OSRM_BASE_URL}/route/v1/foot/"
            f"{origen['lon']},{origen['lat']};"
            f"{destino['lon']},{destino['lat']}"
            "?overview=false"
        )

        respuesta = requests.get(url, timeout=TIMEOUT)
        datos = respuesta.json()

        if "routes" not in datos or not datos["routes"]:
            return DISTANCIA_NO_DISPONIBLE

        return datos["routes"][0]["distance"]

    except Exception as error:
        print("Error calculando caminata:", error)
        return DISTANCIA_NO_DISPONIBLE


# ==========================================
# DISTANCIAS DE CAMINATA EN LOTE (MATRIZ OSRM)
# ==========================================
#
# En vez de hacer N peticiones HTTP (una por cada parada candidata),
# se hace UNA sola petición al endpoint /table de OSRM, que calcula
# la distancia desde un punto fijo hacia una lista de puntos
# (o viceversa) en una sola llamada.
#
# Esto es lo que se debe usar en buscar_ruta_optima en vez de llamar
# calcular_distancia_caminata en un loop.
# ==========================================

def calcular_distancias_caminata_batch(punto_fijo, lista_puntos, punto_fijo_es_origen=True):
    """
    Calcula, en una sola petición HTTP, las distancias caminando entre
    un punto fijo (origen o destino real del usuario) y una lista de
    puntos candidatos (paradas de bus).

    Args:
        punto_fijo: dict {"lat": ..., "lon": ...} -> el origen o destino real.
        lista_puntos: lista de dicts {"lat": ..., "lon": ...} -> paradas candidatas.
        punto_fijo_es_origen: True si punto_fijo es el origen del viaje
            (se calculan distancias DESDE punto_fijo HACIA cada parada).
            False si punto_fijo es el destino del viaje (se calculan
            distancias DESDE cada parada HACIA punto_fijo).

    Returns:
        Lista de distancias en metros (misma longitud y orden que
        lista_puntos). Si OSRM no puede calcular una distancia
        específica, se devuelve DISTANCIA_NO_DISPONIBLE en esa posición.
    """
    if not lista_puntos:
        return []

    try:
        # El punto fijo siempre va en el índice 0
        coords = [f"{punto_fijo['lon']},{punto_fijo['lat']}"]
        coords += [f"{p['lon']},{p['lat']}" for p in lista_puntos]
        coords_str = ";".join(coords)

        indices_puntos = ";".join(str(i) for i in range(1, len(coords)))

        if punto_fijo_es_origen:
            sources = "0"
            destinations = indices_puntos
        else:
            sources = indices_puntos
            destinations = "0"

        url = (
            f"{OSRM_BASE_URL}/table/v1/foot/{coords_str}"
            f"?sources={sources}&destinations={destinations}"
            "&annotations=distance"
        )

        respuesta = requests.get(url, timeout=TIMEOUT)
        datos = respuesta.json()

        if datos.get("code") != "Ok" or "distances" not in datos:
            return [DISTANCIA_NO_DISPONIBLE] * len(lista_puntos)

        matriz = datos["distances"]

        if punto_fijo_es_origen:
            # Una sola fuente (el punto fijo) -> una sola fila con N distancias
            fila = matriz[0] if matriz else []
        else:
            # Un solo destino (el punto fijo) -> N filas con 1 columna cada una
            fila = [f[0] for f in matriz] if matriz else []

        # Normalizar longitud y reemplazar None por el centinela
        resultado = []
        for i in range(len(lista_puntos)):
            valor = fila[i] if i < len(fila) else None
            resultado.append(valor if valor is not None else DISTANCIA_NO_DISPONIBLE)

        return resultado

    except Exception as error:
        print("Error calculando matriz de caminata:", error)
        return [DISTANCIA_NO_DISPONIBLE] * len(lista_puntos)