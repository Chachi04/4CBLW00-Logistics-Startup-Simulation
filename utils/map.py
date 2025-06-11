import osmnx as ox
import networkx as nx

G = ox.graph_from_place("Eindhoven, Netherlands", network_type="bike", simplify=False)
print(len(list(G)))
#
# G = ox.graph_from_place("Eindhoven, Netherlands", network_type="bike", simplify=True)
# print(len(list(G)))
#
# connected_components = nx.strongly_connected_components(G)
# largest_component = max(connected_components, key=len)
# G = G.subgraph(largest_component).copy()
# print(len(list(G)))
#
# ox.save_graphml(G, "eindhoven_bike_scc_simplified.graphml")

