import json
import os
import re
import unicodedata

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

RUTA_LUGARES = os.path.join(
    BASE_DIR,
    "data",
    "lugares_final.json"
)
RUTA_INTERSECCIONES = os.path.join(
    BASE_DIR,
    "data",
    "intersecciones.json"
)

# ==================================
# CARGAR LUGARES
# ==================================
with open(
    RUTA_LUGARES,
    encoding="utf-8"
) as archivo:

    LUGARES_LOCALES = json.load(
        archivo
    )
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

# ==================================
# NORMALIZAR TEXTO
# ==================================
def normalizar_texto(texto):
    if not texto:
        return ""

    texto = texto.lower().strip()
    texto = unicodedata.normalize(
        "NFD",
        texto
    )
    texto = "".join(
        letra
        for letra in texto
        if unicodedata.category(letra) != "Mn"
    )
    texto = re.sub(
        r"[^a-z0-9\s]",
        "",
        texto
    )
    reemplazos = {
        "cooperativa": "coop",
        "avenida": "av",
        "avenida.": "av",
        "av.": "av"
    }
    for original,nuevo in reemplazos.items():
        texto = texto.replace(
            original,
            nuevo
        )
    texto = re.sub(
        r"\s+",
        " ",
        texto
    )
    return texto.strip()

# ==================================
# LIMPIAR CONSULTA DEL USUARIO
# ==================================
def limpiar_consulta_lugar(texto):
    texto = normalizar_texto(
        texto
    )

    palabras_eliminar = [
        "quiero",
        "ir",
        "llegar",
        "llevame",
        "llevarme",
        "como",
        "llego",
        "llegar",
        "hasta",
        "hacia",
        "ubicado",
        "ubicada",
        "conocido",
        "conocida",
        "por",
        "favor"
    ]

    palabras = texto.split()

    resultado=[]

    for palabra in palabras:
        if palabra not in palabras_eliminar:
            resultado.append(
                palabra
            )
    return " ".join(resultado)

# ==================================
# BUSCAR LUGAR
# ==================================
def buscar_lugar_local(texto):
    if not texto:
        return None
    texto_normalizado = limpiar_consulta_lugar(
        texto
    )
    mejor_resultado=None
    mayor_puntaje=0

    for clave,lugar in LUGARES_LOCALES.items():
        candidatos=[]

        candidatos.append(
            clave
        )

        candidatos.append(
            lugar.get(
                "nombre",
                ""
            )
        )

        candidatos.extend(
            lugar.get(
                "alias",
                []
            )
        )
        prioridad = lugar.get(
            "prioridad",
            0
        )

        for candidato in candidatos:
            candidato_normalizado = normalizar_texto(
                candidato
            )
            puntaje=0

            if texto_normalizado == candidato_normalizado:
                puntaje=100
            elif texto_normalizado in candidato_normalizado:
                puntaje=80
            elif candidato_normalizado in texto_normalizado:
                puntaje=75
            else:
                palabras_usuario=set(
                    texto_normalizado.split()
                )
                palabras_lugar=set(
                    candidato_normalizado.split()
                )
                coincidencias=len(
                    palabras_usuario &
                    palabras_lugar
                )

                if coincidencias:
                    puntaje=50 + coincidencias*10

            # sumar prioridad
            puntaje += prioridad
            if puntaje > mayor_puntaje:
                mayor_puntaje=puntaje
                mejor_resultado=lugar

    if mayor_puntaje >= 50:
        return mejor_resultado

    if texto_normalizado in INTERSECCIONES:
        return INTERSECCIONES[
            texto_normalizado
        ]
    return None