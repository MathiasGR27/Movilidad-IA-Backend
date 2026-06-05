from flask import Blueprint, request, jsonify
from services.gemini_service import extraer_origen_destino
from services.nominatim_service import buscar_lugar
from services.route_match_service import recomendar_linea
from services.route_segment_service import obtener_tramo_ruta
from services.transbordo_service import buscar_transbordo

chat_bp = Blueprint("chat_bp", __name__)


@chat_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    mensaje = data.get("mensaje")

    if not mensaje:
        return jsonify({"mensaje": "Debe enviar una consulta"}), 400

    try:
        datos = extraer_origen_destino(mensaje)

        origen_texto = datos.get("origen")
        destino_texto = datos.get("destino")

        if not origen_texto or not destino_texto:
            return jsonify({
                "respuesta": "No pude identificar claramente el origen y destino. Intenta escribir: quiero ir desde el Portón hasta la Av. Lorena."
            }), 400

        origen = buscar_lugar(origen_texto)
        destino = buscar_lugar(destino_texto)

        if not origen:
            return jsonify({
                "respuesta": f"No pude encontrar el origen: {origen_texto}. Intenta escribirlo con más detalle."
            }), 404

        if not destino:
            return jsonify({
                "respuesta": f"No pude encontrar el destino: {destino_texto}. Intenta escribirlo con más detalle."
            }), 404

        # 1. PRIMERO BUSCAR RUTA DIRECTA
        recomendacion = recomendar_linea(origen, destino)

        if recomendacion:
            tramo_geojson = obtener_tramo_ruta(
                recomendacion["linea"],
                origen,
                destino
            )

            respuesta = f"""
Encontré una ruta directa para ti.

Puedes tomar la {recomendacion['linea']} desde una parada cercana a {origen_texto} y bajarte cerca de {destino_texto}.

El recorrido aproximado se muestra en el mapa.
"""

            return jsonify({
                "respuesta": respuesta.strip(),
                "origen_texto": origen_texto,
                "destino_texto": destino_texto,
                "origen": origen,
                "destino": destino,
                "recomendacion": {
                    "tipo": "directa",
                    "linea": recomendacion["linea"]
                },
                "tramo_geojson": tramo_geojson
            }), 200

        # 2. SOLO SI NO HAY DIRECTA, BUSCAR TRANSBORDO
        transbordo = buscar_transbordo(origen, destino)

        if transbordo:
            respuesta = f"""
Encontré una alternativa con transbordo para tu viaje.

1. Camina hasta una parada cercana a {origen_texto}.
2. Toma la {transbordo['linea_1']}.
3. Baja en el punto de transbordo aproximado.
4. Luego toma la {transbordo['linea_2']}.
5. Finalmente, baja cerca de {destino_texto}.

El recorrido aproximado se muestra en el mapa.
"""

            return jsonify({
                "respuesta": respuesta.strip(),
                "origen_texto": origen_texto,
                "destino_texto": destino_texto,
                "origen": origen,
                "destino": destino,
                "transbordo": transbordo["transbordo"],
                "recomendacion": {
                    "tipo": "transbordo",
                    "linea_1": transbordo["linea_1"],
                    "linea_2": transbordo["linea_2"]
                },
                "tramo_geojson": transbordo["tramos_geojson"]
            }), 200

        return jsonify({
            "respuesta": "No encontré una ruta directa ni una alternativa con transbordo para ese trayecto."
        }), 404

    except Exception as e:
        return jsonify({
            "mensaje": "No pude procesar la consulta",
            "error": str(e)
        }), 500