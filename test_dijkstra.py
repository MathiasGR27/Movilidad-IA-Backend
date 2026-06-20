from services.dijkstra_service import buscar_ruta_optima

origen = {
    "lat": -0.2492437,
    "lon": -79.1616835
}

destino = {
    "lat": -0.3020,
    "lon": -79.1450
}

ruta = buscar_ruta_optima(
    origen,
    destino
)

print("\nLINEAS")
print(ruta["lineas_utilizadas"])

print("\nTRANSBORDOS")
print(ruta["cantidad_transbordos"])

print("\nSEGMENTOS")

for s in ruta["segmentos"]:
    print(s)