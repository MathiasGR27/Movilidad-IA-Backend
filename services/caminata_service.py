import requests


# ==========================================
# GENERAR CAMINATA REAL POR CALLES
# ==========================================

def generar_caminata(origen, destino):
    try:
        url = (
            "https://router.project-osrm.org/"
            "route/v1/foot/"
            f"{origen['lon']},{origen['lat']};"
            f"{destino['lon']},{destino['lat']}"
            "?overview=full"
            "&geometries=geojson"
        )

        respuesta = requests.get(url, timeout=10)
        datos = respuesta.json()

        if "routes" not in datos or len(datos["routes"]) == 0:
            return []

        geometria = datos["routes"][0]["geometry"]
        return geometria["coordinates"]

    except Exception as error:
        print("Error generando caminata:", error)
        return []