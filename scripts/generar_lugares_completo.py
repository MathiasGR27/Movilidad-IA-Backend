import os
import json
import re
import unicodedata
from collections import defaultdict


CARPETA_GEOJSON = "data/geojson"

ARCHIVO_SALIDA = "data/lugares_final.json"


# =====================================
# NORMALIZAR TEXTO
# =====================================

def normalizar(texto):

    if not texto:
        return ""


    texto = texto.lower()


    texto = unicodedata.normalize(
        "NFD",
        texto
    )


    texto = "".join(
        c for c in texto
        if unicodedata.category(c) != "Mn"
    )


    texto = texto.replace("_"," ")

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )


    return texto.strip()



# =====================================
# LIMPIAR NOMBRE
# =====================================

def limpiar_nombre(nombre):

    nombre = nombre.replace(
        "_",
        " "
    )


    return nombre.strip().title()



# =====================================
# CREAR ALIAS
# =====================================

def generar_alias(nombre):

    normal = normalizar(
        nombre
    )


    alias = [

        normal

    ]


    palabras = normal.split()


    if len(palabras)>1:

        alias.append(
            palabras[-1]
        )


    reemplazos = {

        "cooperativa":"coop",

        "avenida":"av",

        "calle":"calle"

    }


    corto = normal


    for a,b in reemplazos.items():

        corto = corto.replace(
            a,
            b
        )


    alias.append(
        corto
    )


    return list(
        set(alias)
    )



# =====================================
# VALIDAR
# =====================================

def valido(nombre):


    if not nombre:

        return False


    texto = normalizar(
        nombre
    )


    prohibidos=[

        "linea",
        "ruta",
        "ida",
        "retorno",
        "regreso"

    ]


    for p in prohibidos:

        if texto.startswith(p):

            return False



    return len(texto)>3



# =====================================
# BUSCAR COORDENADA REPRESENTATIVA
# =====================================

def obtener_coordenada(geometry):


    coords = geometry.get(
        "coordinates",
        []
    )


    if not coords:

        return None



    # tomamos punto medio del recorrido

    mitad = len(coords)//2


    punto = coords[mitad]


    return {

        "lat": punto[1],

        "lon": punto[0]

    }



# =====================================
# PROCESAMIENTO
# =====================================


lugares_temporales = defaultdict(list)



for archivo in os.listdir(
    CARPETA_GEOJSON
):


    if not archivo.endswith(
        ".geojson"
    ):

        continue



    ruta = os.path.join(
        CARPETA_GEOJSON,
        archivo
    )


    with open(
        ruta,
        encoding="utf-8"
    ) as f:

        geojson=json.load(f)



    for feature in geojson.get(
        "features",
        []
    ):


        props = feature.get(
            "properties",
            {}
        )


        geometry = feature.get(
            "geometry"
        )


        if not geometry:

            continue



        coordenada = obtener_coordenada(
            geometry
        )


        if not coordenada:

            continue



        posibles=[

            props.get(
                "Punto_de_P"
            ),

            props.get(
                "Punto_de_L"
            ),

            props.get(
                "Punto_part"
            ),

            props.get(
                "Punto_lleg"
            )

        ]



        for nombre in posibles:


            if not valido(nombre):

                continue



            nombre_limpio = limpiar_nombre(
                nombre
            )


            clave = normalizar(
                nombre_limpio
            )



            lugares_temporales[clave].append({

                "nombre":nombre_limpio,

                "lat":coordenada["lat"],

                "lon":coordenada["lon"]

            })



    print(
        "Procesado:",
        archivo
    )



# =====================================
# UNIFICAR RESULTADOS
# =====================================


lugares={}



for clave, lista in lugares_temporales.items():


    elemento = lista[0]


    lugares[clave]={

        "nombre":
        elemento["nombre"],


        "alias":
        generar_alias(
            elemento["nombre"]
        ),


        "prioridad":
        len(lista),


        "lat":
        elemento["lat"],


        "lon":
        elemento["lon"]

    }



# =====================================
# AGREGAR PRIORIDADES MANUALES
# =====================================


PRIORIDAD_ALTA=[

    "terminal",

    "paseo shopping",

    "hospital gustavo dominguez",

    "parque zaracay",

    "municipio",

    "universidad espe",

    "coop juan eulogio"

]



for clave in lugares:

    if clave in PRIORIDAD_ALTA:

        lugares[clave]["prioridad"]=100



# =====================================
# GUARDAR
# =====================================


with open(
    ARCHIVO_SALIDA,
    "w",
    encoding="utf-8"
) as f:


    json.dump(

        lugares,

        f,

        ensure_ascii=False,

        indent=4

    )


print("==============================")

print(
    "Archivo generado:",
    ARCHIVO_SALIDA
)

print(
    "Cantidad:",
    len(lugares)
)

print("==============================")