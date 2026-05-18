from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from models.user_model import User
from database.db import db

import jwt
import datetime
import os

auth_bp = Blueprint("auth_bp", __name__)
bcrypt = Bcrypt()

SECRET_KEY = os.getenv("SECRET_KEY")


# =========================
# REGISTRO
# =========================

@auth_bp.route("/register", methods=["POST"])
def register():

    data = request.get_json()

    nombre = data.get("nombre")
    email = data.get("email")
    password = data.get("password")

    # Validación básica
    if not nombre or not email or not password:
        return jsonify({
            "mensaje": "Todos los campos son obligatorios"
        }), 400

    # Verificar si ya existe
    usuario_existente = User.query.filter_by(email=email).first()

    if usuario_existente:
        return jsonify({
            "mensaje": "El correo ya está registrado"
        }), 409

    # Encriptar contraseña
    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    # Crear usuario
    nuevo_usuario = User(
        nombre=nombre,
        email=email,
        password=password_hash
    )

    db.session.add(nuevo_usuario)
    db.session.commit()

    return jsonify({
        "mensaje": "Usuario registrado correctamente"
    }), 201


# =========================
# LOGIN
# =========================

@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    usuario = User.query.filter_by(email=email).first()

    if not usuario:
        return jsonify({
            "mensaje": "Credenciales incorrectas"
        }), 401

    # Comparar contraseña
    if not bcrypt.check_password_hash(usuario.password, password):

        return jsonify({
            "mensaje": "Credenciales incorrectas"
        }), 401

    # Crear token JWT
    token = jwt.encode(
        {
            "id": usuario.id,
            "email": usuario.email,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=4)
        },
        SECRET_KEY,
        algorithm="HS256"
    )

    return jsonify({

        "mensaje": "Inicio de sesión correcto",

        "token": token,

        "usuario": {
            "id": usuario.id,
            "nombre": usuario.nombre,
            "email": usuario.email
        }

    }), 200