import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RUTA_LUGARES = os.path.join(
    BASE_DIR,
    "data",
    "lugares.json"
)

with open(RUTA_LUGARES, encoding="utf-8") as f:
    LUGARES_LOCALES = json.load(f)


def normalizar_texto(texto):

    texto = texto.lower().strip()

    texto = texto.replace("á", "a")
    texto = texto.replace("é", "e")
    texto = texto.replace("í", "i")
    texto = texto.replace("ó", "o")
    texto = texto.replace("ú", "u")

    articulos = [
        "el ",
        "la ",
        "los ",
        "las "
    ]

    for articulo in articulos:

        if texto.startswith(articulo):

            texto = texto[len(articulo):]
            break

    return texto


def buscar_lugar_local(texto):

    if not texto:
        return None

    texto = normalizar_texto(texto)

    return LUGARES_LOCALES.get(texto)