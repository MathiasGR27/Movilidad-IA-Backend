from flask import Blueprint, request, jsonify

from services.gemini_service import extraer_origen_destino
from services.nominatim_service import buscar_lugar

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

    if not mensaje:
        return jsonify({
            "mensaje": "Debe enviar una consulta"
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

        # ====================================================
        # NUEVO MOTOR DE RUTAS BASADO EN GRAFOS + DIJKSTRA
        # ====================================================

        ruta_optima = buscar_ruta_optima(
            origen,
            destino
        )

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

                "tipo":
                    "dijkstra"

            }), 200

        return jsonify({
            "respuesta":
            "No encontré una ruta válida para ese recorrido."
        }), 404

        # ====================================================
        # CÓDIGO ANTIGUO (NO BORRAR TODAVÍA)
        # ====================================================

        # recomendacion = recomendar_linea(
        #     origen,
        #     destino
        # )

        # if recomendacion:
        #
        #     tramo_geojson = obtener_tramo_ruta(
        #         recomendacion["linea"],
        #         origen,
        #         destino
        #     )
        #
        #     respuesta = f"""
        # Encontré una ruta directa para ti.
        #
        # Puedes tomar la {recomendacion['linea']}
        # desde una parada cercana a {origen_texto}
        # y bajarte cerca de {destino_texto}.
        #
        # El recorrido aproximado se muestra en el mapa.
        # """
        #
        #     return jsonify({
        #         "respuesta": respuesta.strip(),
        #         "tramo_geojson": tramo_geojson
        #     }), 200

        # transbordo = buscar_transbordo(
        #     origen,
        #     destino
        # )

        # if transbordo:
        #
        #     respuesta = f"""
        # Encontré una alternativa con transbordo.
        #
        # 1. Toma {transbordo['linea_1']}
        # 2. Realiza transbordo
        # 3. Toma {transbordo['linea_2']}
        # """
        #
        #     return jsonify({
        #         "respuesta": respuesta.strip()
        #     }), 200

    except Exception as e:

        return jsonify({
            "mensaje": "No pude procesar la consulta",
            "error": str(e)
        }), 500