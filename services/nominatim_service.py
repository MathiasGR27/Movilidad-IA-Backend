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

    ALIAS_LUGARES = {
        "proletariado": "Cooperativa Proletariado, Santo Domingo, Ecuador",
        "ciudad verde": "Ciudad Verde, Santo Domingo, Ecuador",
        "shopping": "Paseo Shopping, Santo Domingo, Ecuador",
        "terminal": "Terminal Terrestre Santo Domingo, Ecuador",
        "porton": "Urbanización El Portón, Santo Domingo, Ecuador",
        "chorrera": "La Chorrera, Santo Domingo, Ecuador"
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