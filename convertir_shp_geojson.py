import geopandas as gpd
import os

CARPETAS = [
    "data/EJECUTRANS",
    "data/TSACHILA",
    "data/Rutas Rio Toachi"
]

CARPETA_SALIDA = "data/geojson"

os.makedirs(CARPETA_SALIDA, exist_ok=True)

for carpeta in CARPETAS:
    print(f"\nProcesando carpeta: {carpeta}")

    for root, dirs, files in os.walk(carpeta):
        for file in files:
            if file.endswith(".shp"):
                shp_path = os.path.join(root, file)

                print(f"Convirtiendo: {shp_path}")

                try:
                    gdf = gpd.read_file(shp_path)

                    # Convertir coordenadas a lat/lon para Leaflet
                    gdf = gdf.to_crs(epsg=4326)

                    nombre = os.path.splitext(file)[0]

                    salida = os.path.join(
                        CARPETA_SALIDA,
                        f"{nombre}.geojson"
                    )

                    gdf.to_file(salida, driver="GeoJSON")

                    print(f"Guardado en: {salida}")

                except Exception as e:
                    print(f"Error procesando {file}: {e}")