from flask import Blueprint, request, jsonify

from services.conversacion_service import (
    crear_conversacion,
    obtener_conversaciones_usuario,
    obtener_conversacion,
    eliminar_conversacion
)

from models.user_model import User


conversacion_bp = Blueprint(
    "conversacion_bp",
    __name__
)


@conversacion_bp.route(
    "/conversaciones",
    methods=["POST"]
)
def crear():

    data = request.get_json() or {}

    usuario_id = data.get("usuario_id")

    if not usuario_id:
        return jsonify({
            "mensaje": "Debe enviar el id del usuario"
        }), 400

    usuario = User.query.get(usuario_id)

    if not usuario:
        return jsonify({
            "mensaje": "Usuario no encontrado"
        }), 404

    conversacion = crear_conversacion(
        usuario_id=usuario_id
    )

    return jsonify({
        "id": conversacion.id,
        "usuario_id": conversacion.usuario_id,
        "mensaje": "Conversación creada correctamente"
    }), 201


@conversacion_bp.route(
    "/conversaciones/<int:usuario_id>",
    methods=["GET"]
)
def listar(usuario_id):

    conversaciones = obtener_conversaciones_usuario(
        usuario_id
    )

    return jsonify(conversaciones), 200


@conversacion_bp.route(
    "/conversacion/<int:id>",
    methods=["GET"]
)
def detalle(id):

    mensajes = obtener_conversacion(id)

    return jsonify(mensajes), 200


@conversacion_bp.route(
    "/conversaciones/<int:id>",
    methods=["DELETE"]
)
def borrar_conversacion(id):

    eliminar_conversacion(id)

    return jsonify({
        "mensaje": "Conversación eliminada"
    }), 200