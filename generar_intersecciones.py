import json
import math
import os
import re
import time
import unicodedata
from collections import defaultdict

import requests


# ==========================================
# CONFIGURACIÓN
# ==========================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

CARPETA_GEOJSON = os.path.join(
    BASE_DIR,
    "data",
    "geojson"
)

ARCHIVO_SALIDA = os.path.join(
    BASE_DIR,
    "data",
    "intersecciones.json"
)

OVERPASS_URL = (
    "https://overpass-api.de/api/interpreter"
)

USER_AGENT = (
    "voomy-movilidad-santo-domingo/1.0 "
    "(proyecto academico)"
)

# Distancia máxima entre una intersección vial
# y cualquier punto de una ruta de bus.
DISTANCIA_MAXIMA_RUTA_M = 180

# Margen alrededor del conjunto de rutas para
# consultar la red vial de OpenStreetMap.
MARGEN_BBOX_GRADOS = 0.006

# Se incluyen solamente vías que tengan nombre.
# Puedes aumentar este valor si deseas detectar
# más cruces alejados de los puntos GeoJSON.
TIMEOUT_OVERPASS = 180


# ==========================================
# FUNCIONES DE TEXTO
# ==========================================

def quitar_tildes(texto):
    texto = unicodedata.normalize(
        "NFD",
        str(texto)
    )

    return "".join(
        caracter
        for caracter in texto
        if unicodedata.category(
            caracter
        ) != "Mn"
    )


def normalizar_clave(texto):
    """
    Normaliza una frase para usarla como clave.

    Ejemplo:
    Avenida Guayaquil y Calle Loja
    -> avenida guayaquil y calle loja
    """

    texto = quitar_tildes(
        texto
    ).lower().strip()

    reemplazos = {
        "av.": "avenida",
        "av ": "avenida ",
        "c/": "calle ",
        "cl.": "calle ",
        "&": " y ",
        "/": " y ",
        " con ": " y "
    }

    for original, nuevo in reemplazos.items():
        texto = texto.replace(
            original,
            nuevo
        )

    texto = re.sub(
        r"[^\w\s]",
        " ",
        texto
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


def nombre_interseccion(
    nombres_vias
):
    """
    Construye un nombre legible y estable.
    """

    nombres = sorted(
        {
            str(nombre).strip()
            for nombre in nombres_vias
            if str(nombre).strip()
        },
        key=lambda valor: quitar_tildes(
            valor
        ).lower()
    )

    return " y ".join(
        nombres
    )


# ==========================================
# DISTANCIA GEOGRÁFICA
# ==========================================

def calcular_distancia(
    lat1,
    lon1,
    lat2,
    lon2
):
    radio_tierra = 6371000

    lat1 = math.radians(
        float(lat1)
    )

    lon1 = math.radians(
        float(lon1)
    )

    lat2 = math.radians(
        float(lat2)
    )

    lon2 = math.radians(
        float(lon2)
    )

    diferencia_latitud = (
        lat2 - lat1
    )

    diferencia_longitud = (
        lon2 - lon1
    )

    valor_a = (
        math.sin(
            diferencia_latitud / 2
        ) ** 2
        +
        math.cos(lat1)
        *
        math.cos(lat2)
        *
        math.sin(
            diferencia_longitud / 2
        ) ** 2
    )

    valor_c = 2 * math.atan2(
        math.sqrt(valor_a),
        math.sqrt(1 - valor_a)
    )

    return (
        radio_tierra * valor_c
    )


# ==========================================
# LEER GEOJSON
# ==========================================

def extraer_coordenadas_geometria(
    geometria
):
    tipo = geometria.get(
        "type"
    )

    coordenadas = geometria.get(
        "coordinates",
        []
    )

    resultado = []

    if tipo == "LineString":
        resultado.extend(
            coordenadas
        )

    elif tipo == "MultiLineString":
        for tramo in coordenadas:
            resultado.extend(
                tramo
            )

    elif tipo == "GeometryCollection":
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


def extraer_coordenadas_geojson(
    contenido
):
    tipo = contenido.get(
        "type"
    )

    coordenadas = []

    if tipo == "FeatureCollection":
        for feature in contenido.get(
            "features",
            []
        ):
            geometria = feature.get(
                "geometry"
            ) or {}

            coordenadas.extend(
                extraer_coordenadas_geometria(
                    geometria
                )
            )

    elif tipo == "Feature":
        geometria = contenido.get(
            "geometry"
        ) or {}

        coordenadas.extend(
            extraer_coordenadas_geometria(
                geometria
            )
        )

    else:
        coordenadas.extend(
            extraer_coordenadas_geometria(
                contenido
            )
        )

    resultado = []

    for coordenada in coordenadas:
        if (
            isinstance(
                coordenada,
                (list, tuple)
            )
            and
            len(coordenada) >= 2
        ):
            try:
                lon = float(
                    coordenada[0]
                )

                lat = float(
                    coordenada[1]
                )

                resultado.append(
                    (
                        lat,
                        lon
                    )
                )

            except (
                TypeError,
                ValueError
            ):
                continue

    return resultado


def cargar_rutas_geojson():
    if not os.path.isdir(
        CARPETA_GEOJSON
    ):
        raise FileNotFoundError(
            "No existe la carpeta: "
            f"{CARPETA_GEOJSON}"
        )

    rutas = {}
    todos_los_puntos = []

    archivos = sorted(
        archivo
        for archivo in os.listdir(
            CARPETA_GEOJSON
        )
        if archivo.lower().endswith(
            (
                ".geojson",
                ".json"
            )
        )
    )

    for nombre_archivo in archivos:
        ruta_archivo = os.path.join(
            CARPETA_GEOJSON,
            nombre_archivo
        )

        try:
            with open(
                ruta_archivo,
                encoding="utf-8"
            ) as archivo:
                contenido = json.load(
                    archivo
                )

            coordenadas = (
                extraer_coordenadas_geojson(
                    contenido
                )
            )

            if not coordenadas:
                print(
                    "Sin coordenadas:",
                    nombre_archivo
                )
                continue

            nombre_ruta = os.path.splitext(
                nombre_archivo
            )[0]

            rutas[
                nombre_ruta
            ] = coordenadas

            todos_los_puntos.extend(
                coordenadas
            )

        except Exception as error:
            print(
                "No se pudo leer",
                nombre_archivo,
                ":",
                error
            )

    if not todos_los_puntos:
        raise RuntimeError(
            "No se encontraron coordenadas "
            "válidas en los GeoJSON."
        )

    print(
        "Archivos de rutas cargados:",
        len(rutas)
    )

    print(
        "Puntos totales de rutas:",
        len(todos_los_puntos)
    )

    return (
        rutas,
        todos_los_puntos
    )


# ==========================================
# CONSULTA OVERPASS
# ==========================================

def calcular_bbox(
    puntos
):
    latitudes = [
        lat
        for lat, _ in puntos
    ]

    longitudes = [
        lon
        for _, lon in puntos
    ]

    sur = (
        min(latitudes)
        -
        MARGEN_BBOX_GRADOS
    )

    norte = (
        max(latitudes)
        +
        MARGEN_BBOX_GRADOS
    )

    oeste = (
        min(longitudes)
        -
        MARGEN_BBOX_GRADOS
    )

    este = (
        max(longitudes)
        +
        MARGEN_BBOX_GRADOS
    )

    return (
        sur,
        oeste,
        norte,
        este
    )


def consultar_vias_osm(
    bbox
):
    sur, oeste, norte, este = bbox

    consulta = f"""
    [out:json][timeout:{TIMEOUT_OVERPASS}];
    way
      ["highway"]
      ["name"]
      ({sur},{oeste},{norte},{este});
    (._;>;);
    out body;
    """

    print(
        "\nConsultando OpenStreetMap..."
    )

    print(
        "Área:",
        bbox
    )

    response = requests.post(
        OVERPASS_URL,
        data={
            "data":
                consulta
        },
        headers={
            "User-Agent":
                USER_AGENT
        },
        timeout=TIMEOUT_OVERPASS + 30
    )

    response.raise_for_status()

    datos = response.json()

    elementos = datos.get(
        "elements",
        []
    )

    print(
        "Elementos OSM recibidos:",
        len(elementos)
    )

    return elementos


# ==========================================
# PROCESAR RED VIAL
# ==========================================

def procesar_elementos_osm(
    elementos
):
    nodos = {}

    vias = []

    for elemento in elementos:
        tipo = elemento.get(
            "type"
        )

        if tipo == "node":
            try:
                nodos[
                    elemento["id"]
                ] = (
                    float(
                        elemento["lat"]
                    ),
                    float(
                        elemento["lon"]
                    )
                )
            except (
                KeyError,
                TypeError,
                ValueError
            ):
                continue

        elif tipo == "way":
            etiquetas = elemento.get(
                "tags",
                {}
            )

            nombre = etiquetas.get(
                "name"
            )

            ids_nodos = elemento.get(
                "nodes",
                []
            )

            if (
                nombre
                and
                len(ids_nodos) >= 2
            ):
                vias.append({
                    "id":
                        elemento.get(
                            "id"
                        ),

                    "nombre":
                        nombre,

                    "highway":
                        etiquetas.get(
                            "highway"
                        ),

                    "nodos":
                        ids_nodos
                })

    nombres_por_nodo = defaultdict(
        set
    )

    vias_por_nodo = defaultdict(
        set
    )

    for via in vias:
        for id_nodo in via[
            "nodos"
        ]:
            nombres_por_nodo[
                id_nodo
            ].add(
                via["nombre"]
            )

            vias_por_nodo[
                id_nodo
            ].add(
                via["id"]
            )

    candidatos = []

    for id_nodo, nombres in (
        nombres_por_nodo.items()
    ):
        # Una intersección útil debe contener
        # al menos dos nombres de vía distintos.
        nombres_limpios = {
            nombre.strip()
            for nombre in nombres
            if nombre
            and nombre.strip()
        }

        if len(
            nombres_limpios
        ) < 2:
            continue

        coordenada = nodos.get(
            id_nodo
        )

        if not coordenada:
            continue

        lat, lon = coordenada

        candidatos.append({
            "osm_node_id":
                id_nodo,

            "lat":
                lat,

            "lon":
                lon,

            "vias":
                sorted(
                    nombres_limpios
                )
        })

    print(
        "Intersecciones OSM candidatas:",
        len(candidatos)
    )

    return candidatos


# ==========================================
# FILTRAR CERCA DE RUTAS
# ==========================================

def crear_indice_espacial_simple(
    puntos,
    tamano_celda=0.001
):
    """
    Crea una cuadrícula sencilla para evitar
    comparar cada intersección con todos los
    puntos de todas las rutas.
    """

    indice = defaultdict(
        list
    )

    for lat, lon, ruta in puntos:
        clave = (
            int(
                lat / tamano_celda
            ),
            int(
                lon / tamano_celda
            )
        )

        indice[
            clave
        ].append(
            (
                lat,
                lon,
                ruta
            )
        )

    return (
        indice,
        tamano_celda
    )


def obtener_puntos_cercanos_indice(
    indice,
    tamano_celda,
    lat,
    lon
):
    centro_lat = int(
        lat / tamano_celda
    )

    centro_lon = int(
        lon / tamano_celda
    )

    resultado = []

    # Se revisan celdas vecinas.
    for desplazamiento_lat in range(
        -2,
        3
    ):
        for desplazamiento_lon in range(
            -2,
            3
        ):
            clave = (
                centro_lat
                +
                desplazamiento_lat,

                centro_lon
                +
                desplazamiento_lon
            )

            resultado.extend(
                indice.get(
                    clave,
                    []
                )
            )

    return resultado


def filtrar_intersecciones_por_rutas(
    candidatos,
    rutas
):
    puntos_con_ruta = []

    for nombre_ruta, puntos in (
        rutas.items()
    ):
        for lat, lon in puntos:
            puntos_con_ruta.append(
                (
                    lat,
                    lon,
                    nombre_ruta
                )
            )

    indice, tamano_celda = (
        crear_indice_espacial_simple(
            puntos_con_ruta
        )
    )

    intersecciones = []

    for candidato in candidatos:
        lat = candidato[
            "lat"
        ]

        lon = candidato[
            "lon"
        ]

        puntos_cercanos = (
            obtener_puntos_cercanos_indice(
                indice,
                tamano_celda,
                lat,
                lon
            )
        )

        distancia_minima = float(
            "inf"
        )

        rutas_cercanas = set()

        for (
            lat_ruta,
            lon_ruta,
            nombre_ruta
        ) in puntos_cercanos:
            distancia = calcular_distancia(
                lat,
                lon,
                lat_ruta,
                lon_ruta
            )

            if distancia < distancia_minima:
                distancia_minima = (
                    distancia
                )

            if (
                distancia
                <=
                DISTANCIA_MAXIMA_RUTA_M
            ):
                rutas_cercanas.add(
                    nombre_ruta
                )

        if not rutas_cercanas:
            continue

        nombre = nombre_interseccion(
            candidato["vias"]
        )

        intersecciones.append({
            "nombre":
                nombre,

            "lat":
                round(
                    lat,
                    7
                ),

            "lon":
                round(
                    lon,
                    7
                ),

            "tipo":
                "interseccion",

            "vias":
                candidato[
                    "vias"
                ],

            "rutas_cercanas":
                sorted(
                    rutas_cercanas
                ),

            "distancia_ruta_m":
                round(
                    distancia_minima,
                    2
                ),

            "osm_node_id":
                candidato[
                    "osm_node_id"
                ]
        })

    print(
        "Intersecciones cercanas a rutas:",
        len(intersecciones)
    )

    return intersecciones


# ==========================================
# ELIMINAR DUPLICADOS
# ==========================================

def eliminar_intersecciones_duplicadas(
    intersecciones
):
    """
    OSM puede representar un mismo cruce con
    varios nodos cercanos. Conserva uno solo
    por combinación de nombres y proximidad.
    """

    agrupadas = defaultdict(
        list
    )

    for interseccion in intersecciones:
        clave = tuple(
            sorted(
                normalizar_clave(
                    via
                )
                for via in interseccion[
                    "vias"
                ]
            )
        )

        agrupadas[
            clave
        ].append(
            interseccion
        )

    resultado = []

    for _, grupo in agrupadas.items():
        grupo = sorted(
            grupo,
            key=lambda item: item[
                "distancia_ruta_m"
            ]
        )

        seleccionadas = []

        for candidata in grupo:
            es_duplicada = False

            for seleccionada in seleccionadas:
                distancia = calcular_distancia(
                    candidata["lat"],
                    candidata["lon"],
                    seleccionada["lat"],
                    seleccionada["lon"]
                )

                if distancia <= 35:
                    es_duplicada = True
                    break

            if not es_duplicada:
                seleccionadas.append(
                    candidata
                )

        resultado.extend(
            seleccionadas
        )

    resultado.sort(
        key=lambda item: (
            quitar_tildes(
                item["nombre"]
            ).lower(),
            item["lat"],
            item["lon"]
        )
    )

    print(
        "Intersecciones sin duplicados:",
        len(resultado)
    )

    return resultado


# ==========================================
# CREAR ALIAS Y GUARDAR
# ==========================================

def crear_alias_interseccion(
    interseccion
):
    vias = interseccion[
        "vias"
    ]

    if len(vias) < 2:
        return []

    # Se usan las dos primeras vías como alias
    # principal. En intersecciones complejas el
    # nombre completo sigue guardado en "nombre".
    via_1 = vias[0]
    via_2 = vias[1]

    variantes = {
        f"{via_1} y {via_2}",
        f"{via_2} y {via_1}",
        f"{via_1} con {via_2}",
        f"{via_2} con {via_1}",
        f"{via_1} / {via_2}",
        f"{via_2} / {via_1}"
    }

    return sorted(
        {
            normalizar_clave(
                variante
            )
            for variante in variantes
        }
    )


def guardar_intersecciones(
    intersecciones
):
    salida = {}

    for interseccion in intersecciones:
        alias = crear_alias_interseccion(
            interseccion
        )

        for clave in alias:
            if not clave:
                continue

            # Si dos cruces comparten el mismo nombre,
            # se conserva el más cercano a una ruta.
            existente = salida.get(
                clave
            )

            if (
                existente
                and
                existente.get(
                    "distancia_ruta_m",
                    float("inf")
                )
                <=
                interseccion[
                    "distancia_ruta_m"
                ]
            ):
                continue

            salida[
                clave
            ] = {
                "nombre":
                    interseccion[
                        "nombre"
                    ],

                "lat":
                    interseccion[
                        "lat"
                    ],

                "lon":
                    interseccion[
                        "lon"
                    ],

                "tipo":
                    "interseccion",

                "vias":
                    interseccion[
                        "vias"
                    ],

                "rutas_cercanas":
                    interseccion[
                        "rutas_cercanas"
                    ],

                "distancia_ruta_m":
                    interseccion[
                        "distancia_ruta_m"
                    ],

                "osm_node_id":
                    interseccion[
                        "osm_node_id"
                    ]
            }

    os.makedirs(
        os.path.dirname(
            ARCHIVO_SALIDA
        ),
        exist_ok=True
    )

    with open(
        ARCHIVO_SALIDA,
        "w",
        encoding="utf-8"
    ) as archivo:
        json.dump(
            salida,
            archivo,
            ensure_ascii=False,
            indent=2
        )

    print(
        "\nArchivo generado:"
    )

    print(
        ARCHIVO_SALIDA
    )

    print(
        "Alias guardados:",
        len(salida)
    )


# ==========================================
# PROGRAMA PRINCIPAL
# ==========================================

def generar_intersecciones():
    rutas, todos_los_puntos = (
        cargar_rutas_geojson()
    )

    bbox = calcular_bbox(
        todos_los_puntos
    )

    elementos_osm = (
        consultar_vias_osm(
            bbox
        )
    )

    candidatos = (
        procesar_elementos_osm(
            elementos_osm
        )
    )

    intersecciones = (
        filtrar_intersecciones_por_rutas(
            candidatos,
            rutas
        )
    )

    intersecciones = (
        eliminar_intersecciones_duplicadas(
            intersecciones
        )
    )

    guardar_intersecciones(
        intersecciones
    )


if __name__ == "__main__":
    try:
        generar_intersecciones()

    except requests.Timeout:
        print(
            "\nLa consulta a Overpass tardó "
            "demasiado. Intenta nuevamente."
        )

    except requests.RequestException as error:
        print(
            "\nError consultando OpenStreetMap:"
        )

        print(
            str(error)
        )

    except Exception as error:
        print(
            "\nNo se pudo generar "
            "intersecciones.json:"
        )

        print(
            str(error)
        )