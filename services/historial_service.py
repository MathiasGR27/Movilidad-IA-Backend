from database.db import db
from models.historial_model import HistorialRuta

def guardar_historial(
    usuario_id,
    conversacion_id,
    consulta,
    origen,
    destino,
    respuesta,
    transbordos
):

    historial = HistorialRuta(
        usuario_id=usuario_id,
        conversacion_id=conversacion_id,
        consulta=consulta,
        origen_texto=origen,
        destino_texto=destino,
        respuesta=respuesta,
        transbordos=transbordos
    )

    db.session.add(historial)
    db.session.commit()

    return historial


def obtener_historial_usuario(usuario_id):

    historial = HistorialRuta.query.filter_by(
        usuario_id=usuario_id
    ).order_by(
        HistorialRuta.fecha.desc()
    ).all()

    return [
        {
            "id": h.id,
            "consulta": h.consulta,
            "origen": h.origen_texto,
            "destino": h.destino_texto,
            "respuesta": h.respuesta,
            "transbordos": h.transbordos,
            "es_favorito": h.es_favorito,
            "fecha": h.fecha.strftime("%Y-%m-%d %H:%M:%S")
        }
        for h in historial
    ]