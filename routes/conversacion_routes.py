from flask import Blueprint, jsonify

from services.conversacion_service import (
    crear_conversacion,
    obtener_conversaciones_usuario,
    obtener_conversacion
)

conversacion_bp = Blueprint(
    "conversacion_bp",
    __name__
)


@conversacion_bp.route(
    "/conversaciones",
    methods=["POST"]
)
def crear():

    conversacion = crear_conversacion(1)

    return jsonify({
        "id": conversacion.id
    }), 201


@conversacion_bp.route(
    "/conversaciones/<int:usuario_id>",
    methods=["GET"]
)
def listar(usuario_id):

    return jsonify(
        obtener_conversaciones_usuario(
            usuario_id
        )
    )


@conversacion_bp.route(
    "/conversacion/<int:id>",
    methods=["GET"]
)
def detalle(id):

    return jsonify(
        obtener_conversacion(id)
    )