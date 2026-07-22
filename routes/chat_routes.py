from flask import Blueprint, jsonify, request

from database.db import db
from models.conversacion_model import Conversacion
from models.user_model import User
from services.dijkstra_service import buscar_ruta_optima
from services.gemini_service import extraer_origen_destino
from services.historial_service import guardar_historial
from services.lugares_service import buscar_lugar_local
from services.nominatim_service import buscar_lugar

chat_bp = Blueprint("chat_bp", __name__)


# =====================================================
# BUSCADOR HÍBRIDO DE LUGARES
# =====================================================

def resolver_lugar(texto):
    if not texto:
        return None

    lugar = buscar_lugar_local(texto)
    if lugar:
        return lugar

    lugar = buscar_lugar(texto)
    return lugar


# =====================================================
# LIMPIAR REFERENCIAS HUMANAS
# =====================================================

def limpiar_referencia_lugar(texto):
    if not texto:
        return None

    texto = texto.lower().strip()
    referencias = [
        "estoy en ",
        "estoy por ",
        "me encuentro en ",
        "me encuentro por ",
        "ubicado en ",
        "ubicada en ",
        "queda en ",
        "queda por ",
        "desde ",
        "hasta "
    ]

    for referencia in referencias:
        if texto.startswith(referencia):
            texto = texto.replace(referencia, "", 1)
            break

    return texto.strip()


# =====================================================
# VALIDAR GPS
# =====================================================

def validar_ubicacion_actual(ubicacion_actual):
    if not isinstance(ubicacion_actual, dict):
        return None

    lat = ubicacion_actual.get("lat")
    lon = ubicacion_actual.get("lon")

    if lat is None or lon is None:
        return None

    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return None

    if not (-90 <= lat <= 90):
        return None

    if not (-180 <= lon <= 180):
        return None

    return {
        "lat": lat,
        "lon": lon,
        "nombre": ubicacion_actual.get("nombre", "Mi ubicación actual")
    }


# =====================================================
# CHAT PRINCIPAL
# =====================================================

@chat_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}

    mensaje = str(data.get("mensaje", "")).strip()
    usuario_id = data.get("usuario_id")
    conversacion_id = data.get("conversacion_id")
    ubicacion_actual = validar_ubicacion_actual(data.get("ubicacion_actual"))

    # ---------------------------------
    # VALIDACIONES
    # ---------------------------------

    if not mensaje:
        return jsonify({"mensaje": "Debe enviar una consulta"}), 400

    if not usuario_id:
        return jsonify({"mensaje": "Debe enviar usuario_id"}), 400

    if not conversacion_id:
        return jsonify({"mensaje": "Debe enviar conversacion_id"}), 400

    try:
        usuario_id = int(usuario_id)
        conversacion_id = int(conversacion_id)
    except (TypeError, ValueError):
        return jsonify({"mensaje": "IDs inválidos"}), 400

    usuario = db.session.get(User, usuario_id)
    if not usuario:
        return jsonify({"mensaje": "Usuario no encontrado"}), 404

    conversacion = Conversacion.query.filter_by(
        id=conversacion_id,
        usuario_id=usuario_id
    ).first()

    if not conversacion:
        return jsonify({
            "mensaje": "La conversación no existe o no pertenece al usuario"
        }), 404

    try:
        print("\n====================================")
        print("MENSAJE:", mensaje)
        print("GPS:", ubicacion_actual)
        print("====================================")

        # =====================================
        # EXTRAER ORIGEN DESTINO
        # =====================================

        datos_ia = extraer_origen_destino(mensaje) or {}
        origen_texto = limpiar_referencia_lugar(datos_ia.get("origen"))
        destino_texto = limpiar_referencia_lugar(datos_ia.get("destino"))

        print("IA ORIGEN:", origen_texto)
        print("IA DESTINO:", destino_texto)

        # =====================================
        # RESOLVER ORIGEN
        # =====================================

        origen = None
        if origen_texto:
            origen = resolver_lugar(origen_texto)

        # =====================================
        # SI HAY GPS Y NO HAY ORIGEN
        # =====================================

        if not origen and ubicacion_actual:
            origen_texto = "Mi ubicación actual"
            origen = {
                "lat": ubicacion_actual["lat"],
                "lon": ubicacion_actual["lon"],
                "nombre": "Mi ubicación actual"
            }

        # =====================================
        # SI SOLO ESCRIBIÓ DESTINO
        # =====================================

        if not destino_texto:
            posible_destino = datos_ia.get("destino") or datos_ia.get("origen")
            destino_texto = limpiar_referencia_lugar(posible_destino)

        if not origen:
            return jsonify({
                "respuesta": "No pude identificar el origen. Activa tu ubicación o escribe desde dónde sales."
            }), 400

        if not destino_texto:
            return jsonify({"respuesta": "No pude identificar el destino."}), 400

        destino = resolver_lugar(destino_texto)

        print("ORIGEN:", origen)
        print("DESTINO:", destino)

        if not destino:
            return jsonify({
                "respuesta": f"No encontré el destino {destino_texto}"
            }), 404

        # =====================================
        # CALCULAR RUTA ÓPTIMA
        # =====================================

        ruta_optima = buscar_ruta_optima(origen, destino)
        print("\nRUTA ENCONTRADA:", ruta_optima)

        if not ruta_optima:
            return jsonify({
                "respuesta": "No encontré una ruta disponible para ese recorrido."
            }), 404

        # =====================================
        # DATOS DE LA RUTA
        # =====================================

        segmentos = ruta_optima.get("segmentos", [])
        transbordos = ruta_optima.get("cantidad_transbordos", 0)
        caminata_inicio = ruta_optima.get("caminata_inicio")
        caminata_fin = ruta_optima.get("caminata_fin")
        transbordos_info = ruta_optima.get("transbordos_info", [])
        geojson = ruta_optima.get("geojson")

        # =====================================
        # CREAR RESPUESTA TEXTO
        # =====================================

        respuesta = f"Encontré una ruta desde {origen_texto} hasta {destino_texto}.\n\n"
        respuesta += "Debes dirigirte a la parada más cercana para iniciar el recorrido.\n\n"

        paso = 1
        for indice, segmento in enumerate(segmentos):
            linea = segmento.get("linea", "línea desconocida")
            inicio = segmento.get("inicio", "")
            fin = segmento.get("fin", "")

            respuesta += (
                f"{paso}. Toma la {linea}.\n"
                f"   Desde: {inicio}\n"
                f"   Hasta: {fin}\n\n"
            )
            paso += 1

            if indice < len(segmentos) - 1:
                respuesta += f"{paso}. Realiza transbordo.\n\n"
                paso += 1

        respuesta += f"Transbordos necesarios: {transbordos}"

        # =====================================
        # GUARDAR HISTORIAL
        # =====================================

        historial = guardar_historial(
            usuario_id=usuario_id,
            conversacion_id=conversacion_id,
            consulta=mensaje,
            origen=origen_texto,
            destino=destino_texto,
            respuesta=respuesta,
            transbordos=transbordos,
            segmentos=segmentos,
            tramo_geojson=geojson,
            transbordos_info=transbordos_info,
            caminata_inicio=caminata_inicio,
            caminata_fin=caminata_fin,
            origen_coordenadas={
                "lat": origen["lat"],
                "lon": origen["lon"]
            },
            destino_coordenadas={
                "lat": destino["lat"],
                "lon": destino["lon"]
            }
        )

        print("\nHISTORIAL GUARDADO ID:", historial.id)

        # =====================================
        # ACTUALIZAR ESTADÍSTICAS USUARIO
        # =====================================

        usuario.viajes_consultados = (usuario.viajes_consultados or 0) + 1
        usuario.consultas_ia = (usuario.consultas_ia or 0) + 1

        db.session.commit()

        # =====================================
        # RESPUESTA FRONTEND
        # =====================================

        return jsonify({
            "respuesta": respuesta,
            "origen_texto": origen_texto,
            "destino_texto": destino_texto,
            "origen": origen,
            "destino": destino,
            "lineas": ruta_optima.get("lineas_utilizadas", []),
            "transbordos": transbordos,
            "segmentos": segmentos,
            "tramo_geojson": geojson,
            "transbordos_info": transbordos_info,
            "caminata_inicio": caminata_inicio,
            "caminata_fin": caminata_fin,
            "historial_id": historial.id,
            "conversacion_id": conversacion_id,
            "usuario_id": usuario_id,
            "uso_ubicacion_actual": bool(ubicacion_actual),
            "tipo": "dijkstra"
        }), 200

    except Exception as error:
        db.session.rollback()
        print("\nERROR CHAT:", error)
        return jsonify({
            "mensaje": "Error procesando la consulta",
            "error": str(error)
        }), 500