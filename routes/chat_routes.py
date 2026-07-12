from flask import (
    Blueprint,
    request,
    jsonify
)

from services.gemini_service import (
    extraer_origen_destino
)

from services.nominatim_service import (
    buscar_lugar
)

from services.historial_service import (
    guardar_historial
)

from services.dijkstra_service import (
    buscar_ruta_optima
)

from models.user_model import User

from models.conversacion_model import (
    Conversacion
)

from database.db import db


chat_bp = Blueprint(
    "chat_bp",
    __name__
)


# ==========================================
# VALIDAR UBICACIÓN ACTUAL
# ==========================================

def validar_ubicacion_actual(
    ubicacion_actual
):
    if not isinstance(
        ubicacion_actual,
        dict
    ):
        return None

    latitud = ubicacion_actual.get(
        "lat"
    )

    longitud = ubicacion_actual.get(
        "lon"
    )

    if (
        latitud is None
        or
        longitud is None
    ):
        return None

    try:
        latitud = float(
            latitud
        )

        longitud = float(
            longitud
        )

    except (TypeError, ValueError):

        return None

    if not (
        -90 <= latitud <= 90
    ):
        return None

    if not (
        -180 <= longitud <= 180
    ):
        return None

    return {
        "lat":
            latitud,

        "lon":
            longitud,

        "nombre":
            ubicacion_actual.get(
                "nombre",
                "Mi ubicación actual"
            )
    }


# ==========================================
# ENDPOINT DEL CHAT
# ==========================================

@chat_bp.route(
    "/chat",
    methods=["POST"]
)
def chat():

    data = request.get_json(
        silent=True
    ) or {}

    mensaje = str(
        data.get(
            "mensaje",
            ""
        )
    ).strip()

    ubicacion_actual = (
        validar_ubicacion_actual(
            data.get(
                "ubicacion_actual"
            )
        )
    )

    conversacion_id = data.get(
        "conversacion_id"
    )

    usuario_id = data.get(
        "usuario_id"
    )

    # ======================================
    # VALIDACIONES INICIALES
    # ======================================

    if not mensaje:

        return jsonify({
            "mensaje":
                "Debe enviar una consulta"
        }), 400

    if not conversacion_id:

        return jsonify({
            "mensaje":
                "Debe enviar el ID de la conversación"
        }), 400

    if not usuario_id:

        return jsonify({
            "mensaje":
                "Debe enviar el ID del usuario"
        }), 400

    try:
        usuario_id = int(
            usuario_id
        )

        conversacion_id = int(
            conversacion_id
        )

    except (TypeError, ValueError):

        return jsonify({
            "mensaje":
                "El ID del usuario o conversación no es válido"
        }), 400

    # ======================================
    # COMPROBAR USUARIO
    # ======================================

    usuario = db.session.get(
        User,
        usuario_id
    )

    if not usuario:

        return jsonify({
            "mensaje":
                "Usuario no encontrado"
        }), 404

    # ======================================
    # COMPROBAR CONVERSACIÓN
    # ======================================

    conversacion = (
        Conversacion.query.filter_by(
            id=conversacion_id,
            usuario_id=usuario_id
        ).first()
    )

    if not conversacion:

        return jsonify({
            "mensaje":
                "La conversación no existe "
                "o no pertenece al usuario"
        }), 404

    try:

        print(
            "\n===================================="
        )

        print(
            "MENSAJE RECIBIDO:",
            mensaje
        )

        print(
            "USUARIO ID:",
            usuario_id
        )

        print(
            "CONVERSACIÓN ID:",
            conversacion_id
        )

        print(
            "UBICACIÓN ACTUAL:",
            ubicacion_actual
        )

        print(
            "===================================="
        )

        # ==================================
        # EXTRAER ORIGEN Y DESTINO CON IA
        # ==================================

        datos_ia = extraer_origen_destino(
            mensaje
        ) or {}

        origen_texto = datos_ia.get(
            "origen"
        )

        destino_texto = datos_ia.get(
            "destino"
        )

        # ==================================
        # CUANDO SE USA UBICACIÓN ACTUAL
        # ==================================

        if ubicacion_actual:

            origen_texto = (
                "Mi ubicación actual"
            )

            origen = {
                "lat":
                    ubicacion_actual[
                        "lat"
                    ],

                "lon":
                    ubicacion_actual[
                        "lon"
                    ],

                "nombre":
                    "Mi ubicación actual"
            }

            # Si Gemini interpreta el único
            # lugar mencionado como origen,
            # se utiliza como destino.
            if (
                not destino_texto
                and
                datos_ia.get("origen")
            ):
                destino_texto = (
                    datos_ia.get(
                        "origen"
                    )
                )

            if not destino_texto:

                return jsonify({
                    "respuesta":
                        "Ya tengo tu ubicación actual, "
                        "pero no pude identificar el destino. "
                        "Escribe, por ejemplo: "
                        "quiero ir hasta Ciudad Verde."
                }), 400

        # ==================================
        # CUANDO EL ORIGEN ES ESCRITO
        # ==================================

        else:

            if (
                not origen_texto
                or
                not destino_texto
            ):

                return jsonify({
                    "respuesta":
                        "No pude identificar claramente "
                        "el origen y el destino. "
                        "Intenta escribir: quiero ir "
                        "desde el Portón hasta la "
                        "avenida La Lorena."
                }), 400

            origen = buscar_lugar(
                origen_texto
            )

        # ==================================
        # BUSCAR DESTINO
        # ==================================

        destino = buscar_lugar(
            destino_texto
        )

        print(
            "\nORIGEN TEXTO:"
        )

        print(
            origen_texto
        )

        print(
            "\nDESTINO TEXTO:"
        )

        print(
            destino_texto
        )

        print(
            "\nORIGEN ENCONTRADO:"
        )

        print(
            origen
        )

        print(
            "\nDESTINO ENCONTRADO:"
        )

        print(
            destino
        )

        if not origen:

            return jsonify({
                "respuesta":
                    f"No pude encontrar el origen: "
                    f"{origen_texto}. "
                    "Intenta escribirlo con más detalle."
            }), 404

        if not destino:

            return jsonify({
                "respuesta":
                    f"No pude encontrar el destino: "
                    f"{destino_texto}. "
                    "Intenta escribirlo con más detalle."
            }), 404

        # ==================================
        # CALCULAR RUTA CON DIJKSTRA
        # ==================================

        ruta_optima = buscar_ruta_optima(
            origen,
            destino
        )

        print(
            "\nRUTA ÓPTIMA:"
        )

        print(
            ruta_optima
        )

        if not ruta_optima:

            return jsonify({
                "respuesta":
                    "No encontré una ruta válida "
                    "para ese recorrido."
            }), 404

        segmentos = ruta_optima.get(
            "segmentos",
            []
        )

        transbordos = ruta_optima.get(
            "cantidad_transbordos",
            0
        )

        caminata_inicio = (
            ruta_optima.get(
                "caminata_inicio"
            )
        )

        caminata_fin = (
            ruta_optima.get(
                "caminata_fin"
            )
        )

        transbordos_info = (
            ruta_optima.get(
                "transbordos_info",
                []
            )
        )

        tramo_geojson = (
            ruta_optima.get(
                "geojson"
            )
        )

        # ==================================
        # CONSTRUIR RESPUESTA
        # ==================================

        mensaje_respuesta = (
            f"Encontré una ruta desde "
            f"{origen_texto} hasta "
            f"{destino_texto}.\n\n"
        )

        mensaje_respuesta += (
            "1. Camina hasta la parada "
            "más cercana.\n\n"
        )

        paso = 2

        for indice, segmento in enumerate(
            segmentos
        ):

            inicio = segmento.get(
                "inicio",
                "Parada no disponible"
            )

            fin = segmento.get(
                "fin",
                "Parada no disponible"
            )

            linea = segmento.get(
                "linea",
                "Línea no disponible"
            )

            mensaje_respuesta += (
                f"{paso}. Toma la "
                f"{linea}.\n"
                f"   Desde:\n"
                f"   {inicio}\n\n"
                f"   Hasta:\n"
                f"   {fin}\n\n"
            )

            paso += 1

            if (
                indice
                <
                len(segmentos) - 1
            ):

                mensaje_respuesta += (
                    f"{paso}. Realiza un "
                    "transbordo.\n\n"
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

        # ==================================
        # GUARDAR HISTORIAL
        # ==================================

        historial_guardado = (
            guardar_historial(
                usuario_id=
                    usuario_id,

                conversacion_id=
                    conversacion_id,

                consulta=
                    mensaje,

                origen=
                    origen_texto,

                destino=
                    destino_texto,

                respuesta=
                    mensaje_respuesta,

                transbordos=
                    transbordos,

                segmentos=
                    segmentos,

                tramo_geojson=
                    tramo_geojson,

                transbordos_info=
                    transbordos_info,

                caminata_inicio=
                    caminata_inicio,

                caminata_fin=
                    caminata_fin
            )
        )

        print(
            "\nCONSULTA GUARDADA CON ID:",
            historial_guardado.id
        )

        # ==================================
        # ACTUALIZAR ESTADÍSTICAS
        # ==================================

        usuario.viajes_consultados = (
            usuario.viajes_consultados
            or 0
        ) + 1

        usuario.consultas_ia = (
            usuario.consultas_ia
            or 0
        ) + 1

        db.session.commit()

        # ==================================
        # RESPUESTA AL FRONTEND
        # ==================================

        return jsonify({
            "respuesta":
                mensaje_respuesta,

            "origen_texto":
                origen_texto,

            "destino_texto":
                destino_texto,

            "origen":
                origen,

            "destino":
                destino,

            "lineas":
                ruta_optima.get(
                    "lineas_utilizadas",
                    []
                ),

            "transbordos":
                transbordos,

            "segmentos":
                segmentos,

            "tramo_geojson":
                tramo_geojson,

            "transbordos_info":
                transbordos_info,

            "caminata_inicio":
                caminata_inicio,

            "caminata_fin":
                caminata_fin,

            "historial_id":
                historial_guardado.id,

            "conversacion_id":
                conversacion_id,

            "usuario_id":
                usuario_id,

            "uso_ubicacion_actual":
                bool(
                    ubicacion_actual
                ),

            "tipo":
                "dijkstra"

        }), 200

    except Exception as error:

        db.session.rollback()

        print(
            "\nERROR EN CHAT:",
            str(error)
        )

        return jsonify({
            "mensaje":
                "No pude procesar la consulta",

            "error":
                str(error)
        }), 500