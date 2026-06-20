from services.grafo_service import construir_grafo
import networkx as nx

G = construir_grafo()

print("Nodos:", G.number_of_nodes())
print("Aristas:", G.number_of_edges())

componentes = list(
    nx.connected_components(G)
)

print("Componentes:", len(componentes))