import requests

from services.lugares_service import buscar_lugar_local


def buscar_lugar(nombre):

    lugar_local = buscar_lugar_local(nombre)

    if lugar_local:
        return lugar_local

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": f"{nombre}, Santo Domingo de los Tsáchilas, Ecuador",
        "format": "json",
        "limit": 1
    }

    headers = {
        "User-Agent": "movilidad-ia-santo-domingo/1.0"
    }

    try:

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=5
        )

        data = response.json()

        if not data:
            return None

        return {
            "nombre": data[0]["display_name"],
            "lat": float(data[0]["lat"]),
            "lon": float(data[0]["lon"])
        }

    except Exception:
        return None