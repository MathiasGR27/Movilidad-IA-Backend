from database.db import db


class HistorialRuta(db.Model):

    __tablename__ = "historial_rutas"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )

    origen_texto = db.Column(
        db.String(150),
        nullable=False
    )

    destino_texto = db.Column(
        db.String(150),
        nullable=False
    )

    respuesta = db.Column(
        db.Text,
        nullable=False
    )

    transbordos = db.Column(
        db.Integer,
        default=0
    )

    es_favorito = db.Column(
        db.Boolean,
        default=False
    )

    fecha = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    consulta = db.Column(
        db.Text,
        nullable=False
    )

    conversacion_id = db.Column(
        db.Integer,
        db.ForeignKey("conversaciones.id"),
        nullable=True
    )

    # Datos estructurados para reconstruir
    # la tarjeta visual de la ruta.

    segmentos = db.Column(
        db.JSON,
        nullable=True
    )

    tramo_geojson = db.Column(
        db.JSON,
        nullable=True
    )

    transbordos_info = db.Column(
        db.JSON,
        nullable=True
    )

    caminata_inicio = db.Column(
        db.JSON,
        nullable=True
    )

    caminata_fin = db.Column(
        db.JSON,
        nullable=True
    )