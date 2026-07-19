import networkx as nx

from services.grafo_service import (
    construir_grafo,
    obtener_datos_parada,
    calcular_distancia
)

from services.geojson_dijkstra_service import (
    generar_geojson_camino
)

from services.paradas_service import (
    obtener_mejores_paradas
)


# Crear grafo global
G = construir_grafo()

PENALIZACION_TRANSBORDO = 10000


# ==========================================
# OBTENER LINEA
# ==========================================

def obtener_linea_parada(nombre):

    if not nombre:
        return ""

    if " - " in nombre:
        return nombre.split(" - ")[0]

    return nombre



# ==========================================
# CREAR SEGMENTO
# ==========================================

def crear_segmento(
    linea,
    inicio,
    fin
):

    datos_inicio = obtener_datos_parada(
        inicio
    )

    datos_fin = obtener_datos_parada(
        fin
    )


    return {

        "linea": linea,

        "inicio": inicio,

        "fin": fin,


        "inicio_coordenadas":
        {
            "lat": float(datos_inicio["lat"]),
            "lon": float(datos_inicio["lon"])
        }
        if datos_inicio else None,


        "fin_coordenadas":
        {
            "lat": float(datos_fin["lat"]),
            "lon": float(datos_fin["lon"])
        }
        if datos_fin else None
    }



# ==========================================
# ANALIZAR CAMINO
# ==========================================

def analizar_camino(camino):

    if not camino:

        return {
            "lineas": [],
            "transbordos": 0,
            "segmentos": []
        }


    lineas = []

    segmentos = []


    linea_actual = obtener_linea_parada(
        camino[0]
    )


    inicio_segmento = camino[0]


    lineas.append(
        linea_actual
    )


    transbordos = 0



    for i in range(1, len(camino)):


        linea_nueva = obtener_linea_parada(
            camino[i]
        )


        if linea_nueva != linea_actual:


            edge = G.get_edge_data(
                camino[i-1],
                camino[i]
            )


            # Solo cuenta si es un transbordo real
            es_transbordo = (
                edge
                and
                edge.get("tipo")
                ==
                "transbordo"
            )


            if es_transbordo:


                segmentos.append(
                    crear_segmento(
                        linea_actual,
                        inicio_segmento,
                        camino[i-1]
                    )
                )


                transbordos += 1


                linea_actual = linea_nueva


                inicio_segmento = camino[i]


                if linea_nueva not in lineas:

                    lineas.append(
                        linea_nueva
                    )



    segmentos.append(
        crear_segmento(
            linea_actual,
            inicio_segmento,
            camino[-1]
        )
    )


    return {

        "lineas": lineas,

        "transbordos": transbordos,

        "segmentos": segmentos

    }




# ==========================================
# PUNTAJE
# ==========================================

def calcular_puntaje(
    distancia,
    transbordos
):

    return (
        distancia
        +
        (
            transbordos
            *
            PENALIZACION_TRANSBORDO
        )
    )



# ==========================================
# BUSCAR RUTA OPTIMA
# ==========================================

def buscar_ruta_optima(
    origen,
    destino
):


    paradas_origen = obtener_mejores_paradas(
        origen["lat"],
        origen["lon"],
        limite=15,
        distancia_maxima=800
    )


    paradas_destino = obtener_mejores_paradas(
        destino["lat"],
        destino["lon"],
        limite=15,
        distancia_maxima=800
    )


    mejor = None

    mejor_puntaje = float("inf")



    for inicio in paradas_origen:


        for fin in paradas_destino:


            try:


                camino = nx.dijkstra_path(

                    G,

                    inicio["nombre"],

                    fin["nombre"],

                    weight="peso"

                )


                analisis = analizar_camino(
                    camino
                )


                distancia_total = 0



                for i in range(
                    len(camino)-1
                ):


                    edge = G.get_edge_data(
                        camino[i],
                        camino[i+1]
                    )


                    if edge:

                        distancia_total += edge.get(
                            "distancia",
                            0
                        )



                puntaje = calcular_puntaje(
                    distancia_total,
                    analisis["transbordos"]
                )


                # Evita transbordos cortos innecesarios
                if (
                    analisis["transbordos"] > 0
                    and
                    distancia_total < 500
                ):

                    puntaje += 5000



                if puntaje < mejor_puntaje:


                    mejor_puntaje = puntaje


                    mejor = {


                        "parada_origen":
                            inicio,


                        "parada_destino":
                            fin,


                        "camino":
                            camino,


                        "total_paradas":
                            len(camino),


                        "lineas_utilizadas":
                            analisis["lineas"],


                        "cantidad_transbordos":
                            analisis["transbordos"],


                        "segmentos":
                            analisis["segmentos"],


                        "puntaje":
                            puntaje,


                        "geojson":
                            generar_geojson_camino(
                                camino
                            )
                    }



            except (
                nx.NetworkXNoPath,
                nx.NodeNotFound
            ):

                continue



    if not mejor:

        return None



    # ==================================
    # INFORMACIÓN TRANSBORDOS
    # ==================================

    transbordos_info = []


    camino = mejor["camino"]



    for i in range(
        len(camino)-1
    ):


        linea_a = obtener_linea_parada(
            camino[i]
        )


        linea_b = obtener_linea_parada(
            camino[i+1]
        )


        if linea_a != linea_b:


            a = obtener_datos_parada(
                camino[i]
            )


            b = obtener_datos_parada(
                camino[i+1]
            )



            if a and b:


                distancia = calcular_distancia(
                    a["lat"],
                    a["lon"],
                    b["lat"],
                    b["lon"]
                )


                transbordos_info.append({

                    "linea_origen":
                        linea_a,

                    "linea_destino":
                        linea_b,


                    "parada_salida":
                        camino[i],


                    "parada_llegada":
                        camino[i+1],


                    "lat":
                        float(a["lat"]),


                    "lon":
                        float(a["lon"]),


                    "distancia":
                        round(distancia,2)

                })



    mejor["transbordos_info"] = transbordos_info



    # ==================================
    # CAMINATA
    # ==================================

    if mejor["segmentos"]:


        mejor["caminata_inicio"] = {

            "origen": {

                "lat": float(origen["lat"]),

                "lon": float(origen["lon"])

            },

            "parada":
                mejor["segmentos"][0]["inicio_coordenadas"]

        }



        mejor["caminata_fin"] = {


            "parada":

                mejor["segmentos"][-1]["fin_coordenadas"],


            "destino": {

                "lat": float(destino["lat"]),

                "lon": float(destino["lon"])

            }

        }



    return mejor