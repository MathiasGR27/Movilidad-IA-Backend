from services.dijkstra_service import buscar_ruta_optima

origen = {
    "lat": -0.2492437,
    "lon": -79.1616835
}

destino = {
    "lat": -0.285869,
    "lon": -79.182571
}

ruta = buscar_ruta_optima(
    origen,
    destino
)

if not ruta:
    print("No se encontró ruta")
    exit()

print("\nLINEAS")
print(ruta["lineas_utilizadas"])

print("\nTRANSBORDOS")
print(ruta["cantidad_transbordos"])

print("\nTOTAL PARADAS")
print(ruta["total_paradas"])

print("\nSEGMENTOS")

for s in ruta["segmentos"]:
    print(s)

print("\nCAMINO COMPLETO")

for nodo in ruta["camino"]:
    print(nodo)

print("\nPARADA ORIGEN")
print(ruta["parada_origen"])

print("\nPARADA DESTINO")
print(ruta["parada_destino"])

print("\nGEOJSON")

print(
    ruta["geojson"]
)

print("\nTRANSBORDOS INFO")
print(ruta["transbordos_info"])