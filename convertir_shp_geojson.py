import geopandas as gpd
import os
import zipfile

CARPETAS = [
    "data/EJECUTRANS",
    "data/TSACHILA",
    "data/Rutas Rio Toachi",
    "data/EJECUTRANS1",
    "data/EJECUTRANS2",
    "data/TSACHILA1",
    "data/TSACHILA2",
    "data/TRANSMETRO1",
    "data/TRANSMETRO2"
]

CARPETA_SALIDA = "data/geojson"

os.makedirs(CARPETA_SALIDA, exist_ok=True)

# ==========================================
# DESCOMPRIMIR TODOS LOS ZIPS
# ==========================================

for carpeta in CARPETAS:

    for root, dirs, files in os.walk(carpeta):

        for file in files:

            if file.lower().endswith(".zip"):

                zip_path = os.path.join(root, file)

                carpeta_extract = os.path.join(
                    root,
                    os.path.splitext(file)[0]
                )

                if not os.path.exists(carpeta_extract):

                    print(f"Descomprimiendo: {zip_path}")

                    try:

                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            zip_ref.extractall(carpeta_extract)

                        print(f"Extraído en: {carpeta_extract}")

                    except Exception as e:
                        print(f"Error descomprimiendo {file}: {e}")

# ==========================================
# BUSCAR TODOS LOS SHP
# ==========================================

for carpeta in CARPETAS:

    print(f"\nProcesando carpeta: {carpeta}")

    for root, dirs, files in os.walk(carpeta):

        for file in files:

            if file.startswith("._"):
                continue

            if file.lower().endswith(".shp"):

                shp_path = os.path.join(root, file)

                print(f"Convirtiendo: {shp_path}")

                try:

                    gdf = gpd.read_file(shp_path)

                    gdf = gdf.to_crs(epsg=4326)

                    nombre = os.path.splitext(file)[0]

                    salida = os.path.join(
                        CARPETA_SALIDA,
                        f"{nombre}.geojson"
                    )

                    gdf.to_file(
                        salida,
                        driver="GeoJSON"
                    )

                    print(f"Guardado en: {salida}")

                except Exception as e:

                    print(f"Error procesando {file}: {e}")