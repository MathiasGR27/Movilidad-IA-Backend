from database.db import db
from datetime import datetime


class Conversacion(db.Model):

    __tablename__ = "conversaciones"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )

    fecha = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )