import json
import re

from config import Config
from google import genai

client = genai.Client(api_key=Config.GEMINI_API_KEY)


# =====================================================
# LIMPIAR ARTÍCULOS
# =====================================================

def limpiar_articulos(texto):
    if not texto:
        return texto

    texto = texto.lower().strip()
    articulos = ["el ", "la ", "los ", "las "]

    for articulo in articulos:
        if texto.startswith(articulo):
            texto = texto[len(articulo):]
            break

    return texto.strip()


# =====================================================
# LIMPIAR REFERENCIAS
# =====================================================

def limpiar_referencias(texto):
    if not texto:
        return ""

    texto = texto.lower()
    referencias = [
        "conocido como",
        "conocida como",
        "ubicado en",
        "ubicada en",
        "se encuentra en",
        "se encuentra por",
        "queda en",
        "queda por",
        "esta en",
        "está en",
        "cerca de",
        "junto a",
        "frente a",
        "por el sector de",
        "por el sector"
    ]

    for palabra in referencias:
        texto = texto.replace(palabra, " ")

    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


# =====================================================
# EXTRAER UBICACIÓN RELEVANTE
# =====================================================

def extraer_ubicacion_relevante(texto):
    if not texto:
        return texto

    texto = texto.lower().strip()

    patrones = [
        # km 7 via quevedo
        r"(km\s*\d+\s*(?:via|vía)?\s*[a-z\s]*)",
        # cooperativas
        r"(cooperativa\s+[a-z\s]+)",
        # coop
        r"(coop\s+[a-z\s]+)",
        # avenidas
        r"(avenida\s+[a-z\s]+)",
        # av
        r"(av\s+[a-z\s]+)",
        # calles
        r"(calle\s+[a-z\s]+)",
        # vias
        r"(via\s+[a-z\s]+)"
    ]

    for patron in patrones:
        resultado = re.search(patron, texto)
        if resultado:
            return resultado.group(1).strip()

    return texto.strip()


# =====================================================
# EXTRACCIÓN POR REGLAS
# =====================================================

def extraer_local(mensaje):
    mensaje_limpio = mensaje.lower().strip()

    patrones = [
        # ---------------------------------
        # Estoy en X y necesito llegar a Y
        # ---------------------------------
        (
            r"estoy\s+en\s+(.*?)\s+y\s+(?:necesito|quiero)\s+llegar\s+(?:a|al|a la)?\s*(.*)",
            "origen_destino"
        ),
        # ---------------------------------
        # Me encuentro en X y voy a Y
        # ---------------------------------
        (
            r"me\s+encuentro\s+en\s+(.*?)\s+y\s+(?:voy|quiero\s+ir)\s+(?:a|al|a la)?\s*(.*)",
            "origen_destino"
        ),
        # ---------------------------------
        # Estoy ubicado en X hacia Y
        # ---------------------------------
        (
            r"estoy\s+ubicado\s+en\s+(.*?)\s+hacia\s+(.*)",
            "origen_destino"
        ),
        # ---------------------------------
        # Desde X hasta Y
        # ---------------------------------
        (
            r"desde\s+(.*?)\s+hasta\s+(.*)",
            "origen_destino"
        ),
        (
            r"desde\s+(.*?)\s+hacia\s+(.*)",
            "origen_destino"
        ),
        (
            r"desde\s+(.*?)\s+a\s+(.*)",
            "origen_destino"
        ),
        # ---------------------------------
        # Solo destino
        # ---------------------------------
        (
            r"(?:quiero\s+ir|llevame|llévame|llevarme|quiero\s+llegar|llegar)\s+(?:a|al|a la|hasta|hacia)\s+(.*)",
            "solo_destino"
        ),
        (
            r"me\s+voy\s+para\s+(.*)",
            "solo_destino"
        ),
        (
            r"voy\s+para\s+(.*)",
            "solo_destino"
        ),
        (
            r"voy\s+hacia\s+(.*)",
            "solo_destino"
        )
    ]

    for patron, tipo in patrones:
        resultado = re.search(patron, mensaje_limpio)
        if resultado:
            if tipo == "origen_destino":
                return {
                    "origen": resultado.group(1).strip(),
                    "destino": resultado.group(2).strip()
                }

            if tipo == "solo_destino":
                return {
                    "origen": None,
                    "destino": resultado.group(1).strip()
                }

    return None


# =====================================================
# GEMINI
# =====================================================

def extraer_origen_destino(mensaje):
    local = extraer_local(mensaje)

    if local:
        if local.get("origen"):
            local["origen"] = limpiar_articulos(
                extraer_ubicacion_relevante(local["origen"])
            )

        if local.get("destino"):
            local["destino"] = limpiar_articulos(
                extraer_ubicacion_relevante(local["destino"])
            )

        return local

    try:
        prompt = f"""
Eres un asistente de rutas de transporte público de Santo Domingo Ecuador.

Extrae únicamente origen y destino.

Reglas:

Si dice:
"Estoy en X y necesito llegar a Y"

entonces:

origen = X
destino = Y


Ejemplos:

Mensaje:
Estoy en el Parque Zaracay y necesito llegar al Proletariado

Respuesta:

{{
"origen":"Parque Zaracay",
"destino":"Proletariado"
}}



Mensaje:
Quiero ir al KM 7 vía Quevedo

Respuesta:

{{
"origen":null,
"destino":"KM 7 vía Quevedo"
}}



Mensaje:
Como llego desde el Shopping hasta Juan Eulogio

Respuesta:

{{
"origen":"Shopping",
"destino":"Juan Eulogio"
}}



Responde SOLO JSON válido.


Mensaje:
{mensaje}
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        texto = response.text.strip()
        texto = texto.replace("```json", "").replace("```", "").strip()

        resultado = json.loads(texto)

        if resultado.get("origen"):
            resultado["origen"] = limpiar_articulos(
                extraer_ubicacion_relevante(resultado["origen"])
            )

        if resultado.get("destino"):
            resultado["destino"] = limpiar_articulos(
                extraer_ubicacion_relevante(resultado["destino"])
            )

        return resultado

    except Exception as error:
        print("Error Gemini:", error)
        return {
            "origen": None,
            "destino": None
        }