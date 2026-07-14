import json
import os


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

RUTA_LUGARES = os.path.join(
    BASE_DIR,
    "data",
    "lugares.json"
)

RUTA_INTERSECCIONES = os.path.join(
    BASE_DIR,
    "data",
    "intersecciones.json"
)


# ==============================
# CARGAR LUGARES
# ==============================

with open(
    RUTA_LUGARES,
    encoding="utf-8"
) as archivo:

    LUGARES_LOCALES = json.load(
        archivo
    )


# ==============================
# CARGAR INTERSECCIONES
# ==============================

if os.path.exists(
    RUTA_INTERSECCIONES
):

    with open(
        RUTA_INTERSECCIONES,
        encoding="utf-8"
    ) as archivo:

        INTERSECCIONES = json.load(
            archivo
        )

else:

    INTERSECCIONES = {}


# ==============================
# NORMALIZAR TEXTO
# ==============================

def normalizar_texto(texto):

    texto = texto.lower().strip()

    texto = texto.replace(
        "á",
        "a"
    )

    texto = texto.replace(
        "é",
        "e"
    )

    texto = texto.replace(
        "í",
        "i"
    )

    texto = texto.replace(
        "ó",
        "o"
    )

    texto = texto.replace(
        "ú",
        "u"
    )

    articulos = [
        "el ",
        "la ",
        "los ",
        "las "
    ]

    for articulo in articulos:

        if texto.startswith(
            articulo
        ):

            texto = texto[
                len(articulo):
            ]

            break

    return texto


# ==============================
# BUSCAR LUGAR
# ==============================

def buscar_lugar_local(texto):

    if not texto:

        return None

    texto = normalizar_texto(
        texto
    )

    # Primero busca en lugares fijos
    if texto in LUGARES_LOCALES:

        return LUGARES_LOCALES[
            texto
        ]

    # Luego busca en intersecciones
    if texto in INTERSECCIONES:

        return INTERSECCIONES[
            texto
        ]

    return None