import json
import os
import re
import unicodedata

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RUTA_LUGARES = os.path.join(BASE_DIR, "data", "lugares_final.json")
RUTA_INTERSECCIONES = os.path.join(BASE_DIR, "data", "intersecciones.json")

# ==================================
# CARGAR DATOS
# ==================================

with open(RUTA_LUGARES, encoding="utf-8") as archivo:
    LUGARES_LOCALES = json.load(archivo)

if os.path.exists(RUTA_INTERSECCIONES):
    with open(RUTA_INTERSECCIONES, encoding="utf-8") as archivo:
        INTERSECCIONES = json.load(archivo)
else:
    INTERSECCIONES = {}


# ==================================
# PROCESAMIENTO DE TEXTO
# ==================================

def normalizar_texto(texto):
    if not texto:
        return ""

    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(letra for letra in texto if unicodedata.category(letra) != "Mn")
    texto = re.sub(r"[^a-z0-9\s]", "", texto)

    reemplazos = {
        "cooperativa": "coop",
        "avenida": "av",
        "avenida.": "av",
        "av.": "av"
    }

    for original, nuevo in reemplazos.items():
        texto = texto.replace(original, nuevo)

    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def limpiar_consulta_lugar(texto):
    texto = normalizar_texto(texto)
    palabras_eliminar = {
        "quiero", "ir", "llegar", "llevame", "llevarme", "como", "llego", 
        "hasta", "hacia", "ubicado", "ubicada", "conocido", "conocida", 
        "por", "favor", "desde"
    }

    palabras = texto.split()
    resultado = [palabra for palabra in palabras if palabra not in palabras_eliminar]
    return " ".join(resultado)


# ==================================
# BÚSQUEDA DE LUGARES E INTERSECCIONES
# ==================================

def buscar_lugar_local(texto):
    if not texto:
        return None

    texto_normalizado = limpiar_consulta_lugar(texto)
    palabras_usuario = set(texto_normalizado.split())

    mejor_resultado = None
    mayor_puntaje = 0

    # 1. Buscar en lugares locales
    for clave, lugar in LUGARES_LOCALES.items():
        candidatos = [
            clave,
            lugar.get("nombre", "")
        ] + lugar.get("alias", [])

        prioridad = lugar.get("prioridad", 0)

        for candidato in candidatos:
            candidato_normalizado = normalizar_texto(candidato)
            palabras_lugar = set(candidato_normalizado.split())
            puntaje = 0

            # Coincidencia exacta
            if texto_normalizado == candidato_normalizado:
                puntaje = 100

            # Usuario dentro del nombre
            elif len(texto_normalizado) >= 5 and texto_normalizado in candidato_normalizado:
                puntaje = 85

            # Nombre dentro del usuario
            elif len(candidato_normalizado) >= 5 and candidato_normalizado in texto_normalizado:
                puntaje = 80

            # Coincidencia por palabras clave
            else:
                palabras_validas_usuario = [p for p in palabras_usuario if len(p) > 3]
                coincidencias = len(set(palabras_validas_usuario) & palabras_lugar)

                if coincidencias >= 2:
                    puntaje = 50 + (coincidencias * 10)

            puntaje += prioridad

            if puntaje > mayor_puntaje:
                mayor_puntaje = puntaje
                mejor_resultado = lugar

    # Solo aceptar coincidencias confiables
    if mayor_puntaje >= 70:
        return mejor_resultado

    # 2. Buscar en intersecciones exactas
    if texto_normalizado in INTERSECCIONES:
        return INTERSECCIONES[texto_normalizado]

    # 3. Buscar en intersecciones parciales
    for nombre, interseccion in INTERSECCIONES.items():
        nombre_normalizado = normalizar_texto(nombre)
        if texto_normalizado in nombre_normalizado or nombre_normalizado in texto_normalizado:
            return interseccion

    return None