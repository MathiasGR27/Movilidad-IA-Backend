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


from models.historial_model import HistorialRuta


def obtener_conversacion(conversacion_id):

    mensajes = HistorialRuta.query.filter_by(
        conversacion_id=conversacion_id
    ).order_by(
        HistorialRuta.fecha.asc()
    ).all()

    resultado = []

    for m in mensajes:

        resultado.append({
            "tipo": "user",
            "texto": m.consulta
        })

        resultado.append({
            "tipo": "bot",
            "texto": m.respuesta
        })

    return resultado


def obtener_conversaciones_usuario(usuario_id):
    # 1. Obtenemos todas las conversaciones del usuario
    conversaciones = Conversacion.query.filter_by(
        usuario_id=usuario_id
    ).order_by(
        Conversacion.fecha.desc()
    ).all()

    resultado = []
    
    for c in conversaciones:
        primer_historial = HistorialRuta.query.filter_by(
            conversacion_id=c.id
        ).order_by(
            HistorialRuta.fecha.asc() 
        ).first() 

        texto_consulta = primer_historial.consulta if primer_historial else "Sin consultas"

        resultado.append({
            "id": c.id,
            "fecha": c.fecha.strftime("%Y-%m-%d %H:%M"),
            "titulo": texto_consulta
        })

    return resultado

def eliminar_conversacion(conversacion_id):

    HistorialRuta.query.filter_by(

        conversacion_id=conversacion_id

    ).delete()

    Conversacion.query.filter_by(

        id=conversacion_id

    ).delete()

    db.session.commit()

    return True