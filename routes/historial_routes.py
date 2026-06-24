from flask import Blueprint, jsonify
from database.db import db
from models.historial_model import HistorialRuta

from services.historial_service import (
    obtener_historial_usuario
)

historial_bp = Blueprint("historial_bp", __name__)


@historial_bp.route("/historial/<int:usuario_id>", methods=["GET"])
def historial_usuario(usuario_id):

    historial = obtener_historial_usuario(
        usuario_id
    )

    return jsonify(historial), 200

@historial_bp.route(
    "/favorito/<int:id>",
    methods=["PUT"]
)
def marcar_favorito(id):

    ruta = HistorialRuta.query.get(id)

    if not ruta:

        return jsonify({
            "error": "No existe"
        }), 404

    ruta.es_favorito = True

    db.session.commit()

    return jsonify({
        "mensaje": "Agregado a favoritos"
    }), 200 

@historial_bp.route(
    "/favoritos/<int:usuario_id>",
    methods=["GET"]
)
def obtener_favoritos(usuario_id):

    favoritos = HistorialRuta.query.filter_by(
        usuario_id=usuario_id,
        es_favorito=True
    ).all()

    return jsonify([
        {
            "id": f.id,
            "origen": f.origen_texto,
            "destino": f.destino_texto,
            "fecha": str(f.fecha)
        }
        for f in favoritos
    ]), 200

@historial_bp.route(
    "/historial/detalle/<int:id>",
    methods=["GET"]
)
def obtener_detalle(id):

    ruta = HistorialRuta.query.get(id)

    if not ruta:

        return jsonify({
            "error": "No encontrada"
        }), 404

    return jsonify({

        "id": ruta.id,

        "consulta": ruta.consulta,

        "respuesta": ruta.respuesta,

        "fecha": str(ruta.fecha),

        "origen": ruta.origen_texto,

        "destino": ruta.destino_texto,

        "transbordos": ruta.transbordos

    }), 200