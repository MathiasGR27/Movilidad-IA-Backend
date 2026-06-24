from flask import Blueprint, jsonify

from models.user_model import User

user_bp = Blueprint(
    "user_bp",
    __name__
)

@user_bp.route(
    "/perfil/<int:id>",
    methods=["GET"]
)
def perfil(id):

    user = User.query.get(id)

    if not user:

        return jsonify({
            "error": "Usuario no encontrado"
        }), 404

    return jsonify({

        "id": user.id,

        "nombre": user.nombre,

        "email": user.email,

        "viajes_consultados":
            user.viajes_consultados,

        "consultas_ia":
            user.consultas_ia

    }), 200