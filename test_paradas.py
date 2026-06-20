from services.paradas_service import (
    buscar_parada_mas_cercana,
    buscar_paradas_cercanas,
    obtener_mejores_rutas,
    obtener_rutas_cercanas
)

print("\nPARADA MÁS CERCANA")
print(
    buscar_parada_mas_cercana(
        -0.2492437,
        -79.1616835
    )
)

print("\nPARADAS CERCANAS")
print(
    buscar_paradas_cercanas(
        -0.2492437,
        -79.1616835
    )[:5]
)

print("\nRUTAS CERCANAS")
print(
    obtener_rutas_cercanas(
        -0.2492437,
        -79.1616835
    )
)

print("\nMEJORES RUTAS")

print(
    obtener_mejores_rutas(
        -0.2492437,
        -79.1616835
    )
)