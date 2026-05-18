import os
from flask import Blueprint, jsonify, send_from_directory

geojson_bp = Blueprint("geojson_bp", __name__)

CARPETA_GEOJSON = os.path.join(os.getcwd(), "data", "geojson")

@geojson_bp.route("/rutas", methods=["GET"])
def listar_rutas():
    archivos = []

    for archivo in os.listdir(CARPETA_GEOJSON):
        if archivo.endswith(".geojson"):
            archivos.append(archivo)

    return jsonify(archivos)


@geojson_bp.route("/rutas/<nombre_archivo>", methods=["GET"])
def obtener_ruta(nombre_archivo):
    return send_from_directory(CARPETA_GEOJSON, nombre_archivo)