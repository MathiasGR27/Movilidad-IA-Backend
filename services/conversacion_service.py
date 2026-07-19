from database.db import db
from models.conversacion_model import Conversacion
from models.historial_model import HistorialRuta


def crear_conversacion(usuario_id):

    conversacion = Conversacion(
        usuario_id=usuario_id
    )

    db.session.add(conversacion)
    db.session.commit()

    return conversacion


def obtener_conversacion(
    conversacion_id
):

    mensajes = HistorialRuta.query.filter_by(
        conversacion_id=conversacion_id
    ).order_by(
        HistorialRuta.fecha.asc()
    ).all()

    resultado = []

    for mensaje in mensajes:

        resultado.append({
            "tipo": "user",
            "texto": mensaje.consulta
        })

        datos_disponibles = (
            mensaje.segmentos is not None
            and len(mensaje.segmentos) > 0
        )

        if datos_disponibles:

            resultado.append({
                "tipo": "bot",

                "texto":
                    mensaje.respuesta,

                "tipoRespuesta":
                    "ruta",

                "datosRuta": {
                    "origen_texto":
                        mensaje.origen_texto,

                    "destino_texto":
                        mensaje.destino_texto,

                    "segmentos":
                        mensaje.segmentos or [],

                    "transbordos":
                        mensaje.transbordos or 0,

                    "tramo_geojson":
                        mensaje.tramo_geojson,

                    "transbordos_info":
                        mensaje.transbordos_info or [],

                    "caminata_inicio":
                        mensaje.caminata_inicio,

                    "caminata_fin":
                        mensaje.caminata_fin
                }
            })

        else:

            # Compatibilidad con registros antiguos.
            resultado.append({
                "tipo": "bot",
                "texto": mensaje.respuesta
            })

    return resultado


def obtener_conversaciones_usuario(
    usuario_id
):

    conversaciones = Conversacion.query.filter_by(
        usuario_id=usuario_id
    ).order_by(
        Conversacion.fecha.desc()
    ).all()

    resultado = []

    for conversacion in conversaciones:

        primer_historial = (
            HistorialRuta.query.filter_by(
                conversacion_id=
                    conversacion.id
            )
            .order_by(
                HistorialRuta.fecha.asc()
            )
            .first()
        )

        texto_consulta = (
            primer_historial.consulta
            if primer_historial
            else "Sin consultas"
        )

        resultado.append({
            "id": conversacion.id,

            "fecha":
                conversacion.fecha.strftime(
                    "%Y-%m-%d"
                ),

            "titulo": texto_consulta
        })

    return resultado


def eliminar_conversacion(
    conversacion_id
):

    HistorialRuta.query.filter_by(
        conversacion_id=conversacion_id
    ).delete()

    Conversacion.query.filter_by(
        id=conversacion_id
    ).delete()

    db.session.commit()

    return True