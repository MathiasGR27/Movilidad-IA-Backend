from flask import Blueprint, request, jsonify
from services.gemini_service import extraer_origen_destino
from services.nominatim_service import buscar_lugar
from services.route_match_service import recomendar_linea
from services.route_segment_service import obtener_tramo_ruta

chat_bp = Blueprint("chat_bp", __name__)

@chat_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    mensaje = data.get("mensaje")

    if not mensaje:
        return jsonify({
            "mensaje": "Debe enviar una consulta"
        }), 400

    try:
        datos = extraer_origen_destino(mensaje)

        origen_texto = datos.get("origen")
        destino_texto = datos.get("destino")

        origen = buscar_lugar(origen_texto)
        destino = buscar_lugar(destino_texto)

        if not origen_texto or not destino_texto:
            return jsonify({
                "respuesta": "No pude identificar claramente el origen y destino. Intenta escribir: quiero ir desde el Shopping hasta el Parque de la Juventud."
            }), 400

        if not origen:
            return jsonify({
                "respuesta": f"No pude encontrar el origen: {origen_texto}. Intenta escribirlo con más detalle.",
                "origen_texto": origen_texto,
                "destino_texto": destino_texto
            }), 404

        if not destino:
            return jsonify({
                "respuesta": f"No pude encontrar el destino: {destino_texto}. Intenta escribirlo con más detalle.",
                "origen_texto": origen_texto,
                "destino_texto": destino_texto,
                "origen": origen
            }), 404

        recomendacion = recomendar_linea(origen, destino)

        tramo_geojson = obtener_tramo_ruta(
            recomendacion["linea"],
            origen,
            destino
        )

        return jsonify({
            "respuesta": f"Entendí que quieres ir desde {origen_texto} hasta {destino_texto}. Te recomiendo usar la {recomendacion['linea']}.",
            "origen_texto": origen_texto,
            "destino_texto": destino_texto,
            "origen": origen,
            "destino": destino,
            "recomendacion": recomendacion,
            "tramo_geojson": tramo_geojson
        }), 200

    except Exception as e:
        return jsonify({
            "mensaje": "No pude procesar la consulta",
            "error": str(e)
        }), 500