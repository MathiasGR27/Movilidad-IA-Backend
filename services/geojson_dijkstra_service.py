import json
import os


# ==========================================
# CONFIGURACIÓN
# ==========================================

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

CARPETA_GEOJSON = os.path.join(
    BASE_DIR,
    "data",
    "geojson"
)


# ==========================================
# OBTENER LÍNEA DE UNA PARADA
# ==========================================

def obtener_linea_parada(
    nombre_parada
):
    """
    Ejemplo:

    LINEA13_IDA - Parada 4

    Devuelve:

    LINEA13_IDA
    """

    if not nombre_parada:
        return None

    return nombre_parada.split(
        " - "
    )[0]


# ==========================================
# CARGAR ÍNDICE DE PARADAS
# ==========================================

def cargar_indice_paradas():
    """
    Convierte paradas.json en un diccionario
    para buscar rápidamente cualquier parada.
    """

    with open(
        RUTA_PARADAS,
        encoding="utf-8"
    ) as archivo:

        paradas = json.load(
            archivo
        )

    indice = {}

    for ruta, lista_paradas in (
        paradas.items()
    ):

        for parada in lista_paradas:

            indice[
                parada["nombre"]
            ] = {
                "lat":
                    float(
                        parada["lat"]
                    ),

                "lon":
                    float(
                        parada["lon"]
                    ),

                "ruta":
                    ruta
            }

    return indice


# ==========================================
# COLORES
# ==========================================

def color_por_indice(
    indice
):
    colores = [
        "#2474b5",
        "#ef4444",
        "#16a34a",
        "#7c3aed",
        "#f59e0b",
        "#0891b2",
        "#db2777"
    ]

    return colores[
        indice % len(colores)
    ]


# ==========================================
# CARGAR GEOJSON DE UNA LÍNEA
# ==========================================

def cargar_geojson_linea(
    nombre_linea
):
    """
    Busca el archivo GeoJSON correspondiente
    a una línea dentro de data/geojson.
    """

    nombres_posibles = [
        f"{nombre_linea}.geojson",
        f"{nombre_linea}.json"
    ]

    for nombre_archivo in (
        nombres_posibles
    ):

        ruta_archivo = os.path.join(
            CARPETA_GEOJSON,
            nombre_archivo
        )

        if not os.path.exists(
            ruta_archivo
        ):
            continue

        try:
            with open(
                ruta_archivo,
                encoding="utf-8"
            ) as archivo:

                return json.load(
                    archivo
                )

        except (
            OSError,
            json.JSONDecodeError
        ) as error:

            print(
                "Error leyendo GeoJSON:",
                ruta_archivo
            )

            print(
                str(error)
            )

            return None

    print(
        "No se encontró GeoJSON para:",
        nombre_linea
    )

    return None


# ==========================================
# EXTRAER COORDENADAS DE UNA GEOMETRÍA
# ==========================================

def extraer_coordenadas_geometria(
    geometria
):
    if not geometria:
        return []

    tipo = geometria.get(
        "type"
    )

    coordenadas = geometria.get(
        "coordinates",
        []
    )

    if tipo == "LineString":
        return coordenadas

    if tipo == "MultiLineString":

        resultado = []

        for tramo in coordenadas:

            if (
                resultado
                and
                tramo
                and
                resultado[-1]
                ==
                tramo[0]
            ):
                resultado.extend(
                    tramo[1:]
                )

            else:
                resultado.extend(
                    tramo
                )

        return resultado

    if tipo == "GeometryCollection":

        resultado = []

        for subgeometria in geometria.get(
            "geometries",
            []
        ):
            resultado.extend(
                extraer_coordenadas_geometria(
                    subgeometria
                )
            )

        return resultado

    return []


# ==========================================
# EXTRAER COORDENADAS DE UN GEOJSON
# ==========================================

def extraer_coordenadas_geojson(
    geojson
):
    if not geojson:
        return []

    tipo = geojson.get(
        "type"
    )

    if tipo == "FeatureCollection":

        resultado = []

        for feature in geojson.get(
            "features",
            []
        ):

            geometria = feature.get(
                "geometry",
                {}
            )

            coordenadas = (
                extraer_coordenadas_geometria(
                    geometria
                )
            )

            if (
                resultado
                and
                coordenadas
                and
                resultado[-1]
                ==
                coordenadas[0]
            ):
                resultado.extend(
                    coordenadas[1:]
                )

            else:
                resultado.extend(
                    coordenadas
                )

        return resultado

    if tipo == "Feature":

        return extraer_coordenadas_geometria(
            geojson.get(
                "geometry",
                {}
            )
        )

    return extraer_coordenadas_geometria(
        geojson
    )


# ==========================================
# DISTANCIA SIMPLE ENTRE COORDENADAS
# ==========================================

def distancia_simple(
    coordenada_a,
    coordenada_b
):
    """
    Se usa únicamente para ubicar el punto
    más cercano dentro del GeoJSON.
    """

    lon_a = float(
        coordenada_a[0]
    )

    lat_a = float(
        coordenada_a[1]
    )

    lon_b = float(
        coordenada_b[0]
    )

    lat_b = float(
        coordenada_b[1]
    )

    return (
        (
            lon_a - lon_b
        ) ** 2
        +
        (
            lat_a - lat_b
        ) ** 2
    )


# ==========================================
# BUSCAR PUNTO MÁS CERCANO
# ==========================================

def buscar_indice_cercano(
    coordenadas,
    latitud,
    longitud
):
    if not coordenadas:
        return None

    objetivo = [
        float(
            longitud
        ),
        float(
            latitud
        )
    ]

    mejor_indice = None
    mejor_distancia = float(
        "inf"
    )

    for indice, coordenada in enumerate(
        coordenadas
    ):

        if (
            not isinstance(
                coordenada,
                (list, tuple)
            )
            or
            len(coordenada) < 2
        ):
            continue

        try:
            distancia = distancia_simple(
                coordenada,
                objetivo
            )

        except (
            TypeError,
            ValueError
        ):
            continue

        if distancia < mejor_distancia:

            mejor_distancia = (
                distancia
            )

            mejor_indice = (
                indice
            )

    return mejor_indice


# ==========================================
# EXTRAER TRAMO REAL DE UNA LÍNEA
# ==========================================

def extraer_tramo_linea(
    nombre_linea,
    datos_inicio,
    datos_fin
):
    """
    Obtiene todos los vértices del GeoJSON
    comprendidos entre dos paradas.
    """

    geojson = cargar_geojson_linea(
        nombre_linea
    )

    if not geojson:
        return []

    coordenadas = (
        extraer_coordenadas_geojson(
            geojson
        )
    )

    if len(coordenadas) < 2:
        return []

    indice_inicio = buscar_indice_cercano(
        coordenadas,
        datos_inicio["lat"],
        datos_inicio["lon"]
    )

    indice_fin = buscar_indice_cercano(
        coordenadas,
        datos_fin["lat"],
        datos_fin["lon"]
    )

    if (
        indice_inicio is None
        or
        indice_fin is None
    ):
        return []

    if indice_inicio <= indice_fin:

        tramo = coordenadas[
            indice_inicio:
            indice_fin + 1
        ]

    else:

        tramo = coordenadas[
            indice_fin:
            indice_inicio + 1
        ]

        tramo = list(
            reversed(
                tramo
            )
        )

    return tramo


# ==========================================
# DIVIDIR CAMINO POR LÍNEAS
# ==========================================

def dividir_camino_por_lineas(
    camino
):
    """
    Agrupa los nodos consecutivos que
    pertenecen a la misma línea.
    """

    if not camino:
        return []

    grupos = []

    linea_actual = obtener_linea_parada(
        camino[0]
    )

    nodos_actuales = [
        camino[0]
    ]

    for nombre_parada in camino[1:]:

        linea = obtener_linea_parada(
            nombre_parada
        )

        if linea == linea_actual:

            nodos_actuales.append(
                nombre_parada
            )

        else:

            grupos.append({
                "linea":
                    linea_actual,

                "nodos":
                    nodos_actuales
            })

            linea_actual = linea

            nodos_actuales = [
                nombre_parada
            ]

    grupos.append({
        "linea":
            linea_actual,

        "nodos":
            nodos_actuales
    })

    return grupos


# ==========================================
# CREAR TRAMO DE RESPALDO
# ==========================================

def crear_tramo_desde_paradas(
    nodos,
    indice_paradas
):
    """
    Si no existe el GeoJSON original,
    usa las coordenadas de las paradas.
    """

    coordenadas = []

    for nodo in nodos:

        datos = indice_paradas.get(
            nodo
        )

        if not datos:
            continue

        coordenadas.append([
            float(
                datos["lon"]
            ),
            float(
                datos["lat"]
            )
        ])

    return coordenadas


# ==========================================
# GENERAR GEOJSON DEL CAMINO
# ==========================================

def generar_geojson_camino(
    camino
):
    """
    Genera el GeoJSON de la ruta elegida
    siguiendo la geometría real de cada línea.
    """

    if (
        not camino
        or
        len(camino) < 2
    ):
        return {
            "type":
                "FeatureCollection",

            "features":
                []
        }

    indice_paradas = (
        cargar_indice_paradas()
    )

    grupos = dividir_camino_por_lineas(
        camino
    )

    features = []

    color_index = 0

    for grupo in grupos:

        linea = grupo.get(
            "linea"
        )

        nodos = grupo.get(
            "nodos",
            []
        )

        if (
            not linea
            or
            len(nodos) < 2
        ):
            continue

        parada_inicio = nodos[
            0
        ]

        parada_fin = nodos[
            -1
        ]

        datos_inicio = (
            indice_paradas.get(
                parada_inicio
            )
        )

        datos_fin = (
            indice_paradas.get(
                parada_fin
            )
        )

        if (
            not datos_inicio
            or
            not datos_fin
        ):
            continue

        coordenadas = extraer_tramo_linea(
            linea,
            datos_inicio,
            datos_fin
        )

        # Si no encuentra la geometría real,
        # usa las paradas como respaldo.
        if len(coordenadas) < 2:

            print(
                "Usando paradas como respaldo:",
                linea
            )

            coordenadas = (
                crear_tramo_desde_paradas(
                    nodos,
                    indice_paradas
                )
            )

        if len(coordenadas) < 2:
            continue

        features.append({
            "type":
                "Feature",

            "properties": {
                "tipo":
                    "ruta_dijkstra",

                "linea":
                    linea,

                "inicio":
                    parada_inicio,

                "fin":
                    parada_fin,

                "color":
                    color_por_indice(
                        color_index
                    )
            },

            "geometry": {
                "type":
                    "LineString",

                "coordinates":
                    coordenadas
            }
        })

        color_index += 1

    return {
        "type":
            "FeatureCollection",

        "features":
            features
    }
