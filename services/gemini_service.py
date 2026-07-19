import json
import re
from google import genai
from config import Config

client = genai.Client(api_key=Config.GEMINI_API_KEY)


def limpiar_texto(texto):
    texto = texto.lower().strip()

    reemplazos = [
        "quiero ir",
        "cómo llego",
        "como llego",
        "para ir",
        "me voy",
        "voy",
        "desde",
        "de",
        "el",
        "la",
        "los",
        "las"
    ]
    for palabra in reemplazos:
        texto = texto.replace(palabra, "")
    return texto.strip()


def extraer_local(mensaje):
    mensaje_limpio = mensaje.lower().strip()
    patrones = [
        # desde X hasta Y
        (
            r"desde\s+(.*?)\s+hasta\s+(.*)",
            "origen_destino"
        ),
        # desde X hacia Y
        (
            r"desde\s+(.*?)\s+hacia\s+(.*)",
            "origen_destino"
        ),
        # desde X a Y
        (
            r"desde\s+(.*?)\s+a\s+(.*)",
            "origen_destino"
        ),
        # quiero ir hasta Y
        (
            r"quiero\s+ir\s+hasta\s+(.*)",
            "solo_destino"
        ),
        # quiero ir al Y
        (
            r"quiero\s+ir\s+al\s+(.*)",
            "solo_destino"
        ),
        # quiero ir a la Y
        (
            r"quiero\s+ir\s+a\s+la\s+(.*)",
            "solo_destino"
        ),
        # quiero ir a Y
        (
            r"quiero\s+ir\s+a\s+(.*)",
            "solo_destino"
        ),
        # hasta Y
        (
            r"hasta\s+(.*)",
            "solo_destino"
        ),
        # hacia Y
        (
            r"hacia\s+(.*)",
            "solo_destino"
        )
    ]
    for patron, tipo in patrones:
        coincidencia = re.search(
            patron,
            mensaje_limpio
        )
        if coincidencia:
            if tipo == "origen_destino":
                return {
                    "origen":
                        coincidencia.group(1).strip(),
                    "destino":
                        coincidencia.group(2).strip()
                }
            if tipo == "solo_destino":
                return {
                    "origen":
                        None,
                    "destino":
                        coincidencia.group(1).strip()
                }
    return None


def extraer_origen_destino(mensaje):
    local = extraer_local(mensaje)

    if local:
        return local

    try:
        prompt = f"""
        Extrae el origen y destino del siguiente mensaje.
        Responde SOLO en JSON válido.

        Formato:
        {{
            "origen": "...",
            "destino": "..."
        }}

        Mensaje:
        {mensaje}
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        texto = response.text.strip()
        texto = texto.replace("```json", "")
        texto = texto.replace("```", "")
        texto = texto.strip()

        return json.loads(texto)

    except Exception:
        return {
            "origen": None,
            "destino": None
        }