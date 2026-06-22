from services.paradas_service import obtener_mejores_rutas

rutas = obtener_mejores_rutas(
    -0.285869,
    -79.182571,
    limite=10
)

for r in rutas:
    print(r)