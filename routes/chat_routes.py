from flask import Blueprint, request, jsonify

from services.gemini_service import extraer_origen_destino
from services.nominatim_service import buscar_lugar
from services.historial_service import guardar_historial

from models.user_model import User
from database.db import db

# ALGORITMO NUEVO
from services.dijkstra_service import buscar_ruta_optima

# ALGORITMO ANTIGUO (comentado temporalmente)
# from services.route_match_service import recomendar_linea
# from services.route_segment_service import obtener_tramo_ruta
# from services.transbordo_service import buscar_transbordo


chat_bp = Blueprint("chat_bp", __name__)


@chat_bp.route("/chat", methods=["POST"])
def chat():

    data = request.get_json()

    mensaje = data.get("mensaje")
    conversacion_id = data.get("conversacion_id")

    if not mensaje:
        return jsonify({
            "mensaje": "Debe enviar una consulta"
        }), 400

    if not conversacion_id:
        return jsonify({
            "mensaje": "Debe enviar el id de la conversación"
        }), 400

    try:

        datos = extraer_origen_destino(mensaje)

        origen_texto = datos.get("origen")
        destino_texto = datos.get("destino")

        if not origen_texto or not destino_texto:

            return jsonify({
                "respuesta":
                "No pude identificar claramente el origen y destino. "
                "Intenta escribir: quiero ir desde el Portón hasta la Av. Lorena."
            }), 400

        origen = buscar_lugar(origen_texto)
        destino = buscar_lugar(destino_texto)

        print("\n====================")
        print("ORIGEN TEXTO:")
        print(origen_texto)
        print("DESTINO TEXTO:")
        print(destino_texto)
        print("\nORIGEN ENCONTRADO:")
        print(origen)
        print("\nDESTINO ENCONTRADO:")
        print(destino)
        print("====================")

        if not origen:

            return jsonify({
                "respuesta":
                f"No pude encontrar el origen: {origen_texto}. "
                "Intenta escribirlo con más detalle."
            }), 404

        if not destino:

            return jsonify({
                "respuesta":
                f"No pude encontrar el destino: {destino_texto}. "
                "Intenta escribirlo con más detalle."
            }), 404

        ruta_optima = buscar_ruta_optima(
            origen,
            destino
        )

        print("\nRUTA OPTIMA:")
        print(ruta_optima)

        if ruta_optima:

            segmentos = ruta_optima["segmentos"]
            transbordos = ruta_optima["cantidad_transbordos"]

            mensaje_respuesta = (
                f"Encontré una ruta desde "
                f"{origen_texto} hasta {destino_texto}.\n\n"
            )

            mensaje_respuesta += (
                "1. Camina hasta la parada más cercana.\n\n"
            )

            paso = 2

            for i, segmento in enumerate(segmentos):

                inicio = segmento["inicio"]
                fin = segmento["fin"]

                mensaje_respuesta += (
                    f"{paso}. Toma la "
                    f"{segmento['linea']}.\n"
                )

                mensaje_respuesta += (
                    f"   Desde:\n"
                    f"   {inicio}\n\n"
                    f"   Hasta:\n"
                    f"   {fin}\n\n"
                )

                paso += 1

                if i < len(segmentos) - 1:

                    mensaje_respuesta += (
                        f"{paso}. Realiza un transbordo.\n\n"
                    )

                    paso += 1

            mensaje_respuesta += (
                f"{paso}. Baja cerca de "
                f"{destino_texto}.\n\n"
            )

            mensaje_respuesta += (
                f"Total de transbordos: "
                f"{transbordos}"
            )

            guardar_historial(
                usuario_id=1,
                conversacion_id=conversacion_id,
                consulta=mensaje,
                origen=origen_texto,
                destino=destino_texto,
                respuesta=mensaje_respuesta,
                transbordos=transbordos
            )

            usuario = User.query.get(1)

            if usuario:

                usuario.viajes_consultados = (
                    usuario.viajes_consultados or 0
                ) + 1

                usuario.consultas_ia = (
                    usuario.consultas_ia or 0
                ) + 1

                db.session.commit()

            return jsonify({

                "respuesta": mensaje_respuesta,

                "origen_texto": origen_texto,
                "destino_texto": destino_texto,

                "origen": origen,
                "destino": destino,

                "lineas":
                    ruta_optima["lineas_utilizadas"],

                "transbordos":
                    transbordos,

                "segmentos":
                    segmentos,

                "tramo_geojson":
                    ruta_optima["geojson"],

                "transbordos_info":
                    ruta_optima["transbordos_info"],

                "conversacion_id":
                    conversacion_id,

                "tipo":
                    "dijkstra"

            }), 200

        return jsonify({
            "respuesta":
            "No encontré una ruta válida para ese recorrido."
        }), 404

    except Exception as e:

        return jsonify({
            "mensaje": "No pude procesar la consulta",
            "error": str(e)
        }), 500