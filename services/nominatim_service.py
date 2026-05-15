import requests
import time

def buscar_lugar(nombre):
    time.sleep(1)

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": f"{nombre}, Santo Domingo de los Tsáchilas, Ecuador",
        "format": "json",
        "limit": 1
    }

    headers = {
        "User-Agent": "movilidad-ia-santo-domingo/1.0"
    }

    response = requests.get(url, params=params, headers=headers)
    data = response.json()

    if not data:
        return None

    return {
        "nombre": data[0]["display_name"],
        "lat": float(data[0]["lat"]),
        "lon": float(data[0]["lon"])
    }