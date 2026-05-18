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
        r"desde\s+(.*?)\s+hasta\s+(.*)",
        r"desde\s+(.*?)\s+al\s+(.*)",
        r"desde\s+(.*?)\s+a\s+(.*)",
        r"del\s+(.*?)\s+al\s+(.*)",
        r"de\s+(.*?)\s+a\s+(.*)",
        r"de\s+(.*?)\s+hasta\s+(.*)"
    ]

    for patron in patrones:
        coincidencia = re.search(patron, mensaje_limpio)

        if coincidencia:
            origen = coincidencia.group(1).strip()
            destino = coincidencia.group(2).strip()

            return {
                "origen": origen,
                "destino": destino
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