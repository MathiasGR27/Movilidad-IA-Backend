from database.db import db
from models.historial_model import HistorialRuta

def guardar_historial(
    usuario_id,
    conversacion_id,
    consulta,
    origen,
    destino,
    respuesta,
    transbordos,
    segmentos=None,
    tramo_geojson=None,
    transbordos_info=None,
    caminata_inicio=None,
    caminata_fin=None,
    origen_coordenadas=None,
    destino_coordenadas=None
):
    historial = HistorialRuta(
        usuario_id=usuario_id,
        conversacion_id=conversacion_id,
        consulta=consulta,
        origen_texto=origen,
        destino_texto=destino,
        respuesta=respuesta,
        transbordos=transbordos,
        segmentos=segmentos or [],
        tramo_geojson=tramo_geojson,
        transbordos_info=transbordos_info or [],
        caminata_inicio=caminata_inicio,
        caminata_fin=caminata_fin,
        origen_coordenadas=origen_coordenadas,
        destino_coordenadas=destino_coordenadas
    )

    db.session.add(historial)
    db.session.commit()

    return historial


# ==========================================
# OBTENER HISTORIAL DEL USUARIO
# ==========================================

def obtener_historial_usuario(usuario_id):
    historial = HistorialRuta.query.filter_by(
        usuario_id=usuario_id
    ).order_by(
        HistorialRuta.fecha.desc()
    ).all()

    resultado = []

    for h in historial:
        resultado.append({
            "id": h.id,
            "consulta": h.consulta,
            "origen": h.origen_texto,
            "destino": h.destino_texto,
            "respuesta": h.respuesta,
            "transbordos": h.transbordos,
            "es_favorito": h.es_favorito,
            "fecha": h.fecha.strftime(
                "%Y-%m-%d"
            ),

            # =============================
            # DATOS PARA RECARGAR EL MAPA
            # =============================
            "segmentos": h.segmentos,
            "tramo_geojson": h.tramo_geojson,
            "transbordos_info": h.transbordos_info,
            "caminata_inicio": h.caminata_inicio,
            "caminata_fin": h.caminata_fin,
            "origen_coordenadas": h.origen_coordenadas,
            "destino_coordenadas": h.destino_coordenadas
        })

    return resultado