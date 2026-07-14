import json
import os


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

ARCHIVO_PARADAS = os.path.join(
    BASE_DIR,
    "data",
    "paradas.json"
)

ARCHIVO_IDA = os.path.join(
    BASE_DIR,
    "data",
    "geojson",
    "RUTA_23_INTERPROVINCIAL_IDA.geojson"
)

ARCHIVO_RETORNO = os.path.join(
    BASE_DIR,
    "data",
    "geojson",
    "RUTA_23_INTERPROVINCIAL_RETORNO.geojson"
)

NOMBRE_IDA = (
    "RUTA_23_INTERPROVINCIAL_IDA"
)

NOMBRE_RETORNO = (
    "RUTA_23_INTERPROVINCIAL_RETORNO"
)

# 1 = utilizar todas las coordenadas.
# 2 = utilizar una coordenada de cada dos.
# 3 = utilizar una coordenada de cada tres.
SALTAR_CADA = 1


def cargar_json(ruta_archivo):
    with open(
        ruta_archivo,
        encoding="utf-8"
    ) as archivo:
        return json.load(archivo)


def obtener_coordenadas(
    geojson
):
    coordenadas = []

    tipo_principal = geojson.get(
        "type"
    )

    # Permite leer un Feature individual.
    if tipo_principal == "Feature":
        features = [
            geojson
        ]

    # Permite leer un FeatureCollection.
    elif tipo_principal == "FeatureCollection":
        features = geojson.get(
            "features",
            []
        )

    else:
        features = []

    for feature in features:
        geometria = feature.get(
            "geometry",
            {}
        )

        tipo = geometria.get(
            "type"
        )

        if tipo == "LineString":
            coordenadas.extend(
                geometria.get(
                    "coordinates",
                    []
                )
            )

        elif tipo == "MultiLineString":
            for tramo in geometria.get(
                "coordinates",
                []
            ):
                coordenadas.extend(
                    tramo
                )

    return coordenadas


def eliminar_duplicados_consecutivos(
    coordenadas
):
    resultado = []

    for coordenada in coordenadas:

        if (
            resultado
            and
            resultado[-1]
            ==
            coordenada
        ):
            continue

        resultado.append(
            coordenada
        )

    return resultado


def convertir_a_paradas(
    coordenadas,
    nombre_ruta
):
    coordenadas = (
        eliminar_duplicados_consecutivos(
            coordenadas
        )
    )

    coordenadas_filtradas = (
        coordenadas[
            ::SALTAR_CADA
        ]
    )

    if (
        coordenadas_filtradas
        and
        coordenadas_filtradas[-1]
        !=
        coordenadas[-1]
    ):
        coordenadas_filtradas.append(
            coordenadas[-1]
        )

    lista_paradas = []

    for indice, coordenada in enumerate(
        coordenadas_filtradas,
        start=1
    ):
        if (
            not isinstance(
                coordenada,
                list
            )
            or
            len(coordenada) < 2
        ):
            continue

        longitud = float(
            coordenada[0]
        )

        latitud = float(
            coordenada[1]
        )

        lista_paradas.append({
            "nombre":
                f"{nombre_ruta} - Parada {indice}",

            "lat":
                latitud,

            "lon":
                longitud
        })

    return lista_paradas


def agregar_rutas():
    datos_paradas = cargar_json(
        ARCHIVO_PARADAS
    )

    geojson_ida = cargar_json(
        ARCHIVO_IDA
    )

    geojson_retorno = cargar_json(
        ARCHIVO_RETORNO
    )

    coordenadas_ida = (
        obtener_coordenadas(
            geojson_ida
        )
    )

    coordenadas_retorno = (
        obtener_coordenadas(
            geojson_retorno
        )
    )

    if not coordenadas_ida:
        print(
            "No se encontraron coordenadas "
            "en la ruta de ida."
        )

        return

    if not coordenadas_retorno:
        print(
            "No se encontraron coordenadas "
            "en la ruta de retorno."
        )

        return

    paradas_ida = convertir_a_paradas(
        coordenadas_ida,
        NOMBRE_IDA
    )

    paradas_retorno = convertir_a_paradas(
        coordenadas_retorno,
        NOMBRE_RETORNO
    )

    datos_paradas[
        NOMBRE_IDA
    ] = paradas_ida

    datos_paradas[
        NOMBRE_RETORNO
    ] = paradas_retorno

    with open(
        ARCHIVO_PARADAS,
        "w",
        encoding="utf-8"
    ) as archivo:
        json.dump(
            datos_paradas,
            archivo,
            ensure_ascii=False,
            indent=2
        )

    print(
        "\nRutas agregadas correctamente."
    )

    print(
        NOMBRE_IDA,
        ":",
        len(paradas_ida),
        "paradas"
    )

    print(
        NOMBRE_RETORNO,
        ":",
        len(paradas_retorno),
        "paradas"
    )

    print(
        "\nArchivo actualizado:"
    )

    print(
        ARCHIVO_PARADAS
    )


if __name__ == "__main__":
    agregar_rutas()