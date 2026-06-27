from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

from database.db import db
from models.user_model import User

user_bp = Blueprint("user_bp", __name__)


@user_bp.route("/perfil/<int:id>", methods=["GET"])
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
        "viajes_consultados": user.viajes_consultados or 0,
        "consultas_ia": user.consultas_ia or 0
    }), 200


@user_bp.route("/perfil/<int:id>", methods=["PUT"])
def editar_perfil(id):

    user = User.query.get(id)

    if not user:
        return jsonify({
            "error": "Usuario no encontrado"
        }), 404

    data = request.get_json()

    nombre = data.get("nombre")
    email = data.get("email")

    if not nombre or not email:
        return jsonify({
            "error": "Nombre y correo son obligatorios"
        }), 400

    user.nombre = nombre
    user.email = email

    db.session.commit()

    return jsonify({
        "mensaje": "Perfil actualizado correctamente",
        "usuario": {
            "id": user.id,
            "nombre": user.nombre,
            "email": user.email
        }
    }), 200

@user_bp.route(
"/perfil/<int:id>/password",
methods=["PUT"]
)
def cambiar_password(id):

    usuario = User.query.get(id)

    if not usuario:

        return jsonify({

            "mensaje":

            "Usuario no encontrado"

        }),404

    data = request.get_json()

    actual = data.get(

        "password_actual"

    )

    nueva = data.get(

        "password_nueva"

    )

    if not actual or not nueva:

        return jsonify({

            "mensaje":

            "Todos los campos son obligatorios"

        }),400

    if not bcrypt.check_password_hash(

        usuario.password,

        actual

    ):

        return jsonify({

            "mensaje":

            "Contraseña incorrecta"

        }),400

    usuario.password = (

        bcrypt.generate_password_hash(

            nueva

        ).decode(

            "utf-8"

        )

    )

    db.session.commit()

    return jsonify({

        "mensaje":

        "Contraseña actualizada"

    }),200