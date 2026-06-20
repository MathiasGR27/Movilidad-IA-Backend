import os
import json

from shapely.geometry import shape
from shapely.ops import linemerge, transform
from pyproj import Transformer


CARPETA_GEOJSON = "data/geojson"
ARCHIVO_SALIDA = "data/paradas.json"

DISTANCIA_ENTRE_PARADAS = 300  # metros


transformer = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:32717",
    always_xy=True
)

transformer_inverse = Transformer.from_crs(
    "EPSG:32717",
    "EPSG:4326",
    always_xy=True
)


def convertir_a_metros(geom):
    return transform(transformer.transform, geom)


def convertir_a_geo(geom):
    return transform(transformer_inverse.transform, geom)


paradas = {}

for archivo in os.listdir(CARPETA_GEOJSON):

    if not archivo.endswith(".geojson"):
        continue

    ruta = os.path.join(CARPETA_GEOJSON, archivo)

    try:

        with open(ruta, encoding="utf-8") as f:
            geojson = json.load(f)

        geometrias = []

        for feature in geojson["features"]:
            geometrias.append(
                shape(feature["geometry"])
            )

        linea = linemerge(geometrias)

        if linea.geom_type == "MultiLineString":
            linea = max(
                linea.geoms,
                key=lambda x: x.length
            )

        linea_metros = convertir_a_metros(linea)

        longitud_total = linea_metros.length

        lista_paradas = []

        distancia = 0
        contador = 1

        while distancia <= longitud_total:

            punto_metros = linea_metros.interpolate(
                distancia
            )

            punto_geo = convertir_a_geo(
                punto_metros
            )

            lista_paradas.append({
                "nombre": f"{archivo.replace('.geojson','')} - Parada {contador}",
                "lat": punto_geo.y,
                "lon": punto_geo.x
            })

            contador += 1
            distancia += DISTANCIA_ENTRE_PARADAS

        paradas[
            archivo.replace(".geojson", "")
        ] = lista_paradas

        print(
            f" {archivo}: {len(lista_paradas)} paradas"
        )

    except Exception as e:
        print(
            f" Error en {archivo}: {e}"
        )


with open(
    ARCHIVO_SALIDA,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        paradas,
        f,
        ensure_ascii=False,
        indent=4
    )

print("\nArchivo generado:")
print(ARCHIVO_SALIDA)