import networkx as nx
import osmnx as ox

G = ox.load_graphml("eindhoven_bike_scc_simplified.graphml")

distance_dict = dict(nx.all_pairs_dijkstra_path_length(G, weight='length'))

hub_ids = [309682746, 392674444, 5443883873]

hub_id = hub_ids[0]
# Create a subgraph containing only the hubs
travel_times = nx.single_source_dijkstra_path_length(G, hub_id, cutoff=900, weight='travel_time')
reachable_nodes = list(travel_times.keys())

# Create a subgraph with the reachable nodes
subgraph = G.subgraph(reachable_nodes)


import numpy as np

nodes = sorted(subgraph.nodes())
node_index = {n: i for i, n in enumerate(nodes)}
dist_matrix = np.full((len(nodes), len(nodes)), np.inf)

for source in subgraph.nodes():
    for target, d in distance_dict[source].items():
        dist_matrix[node_index[source]][node_index[target]] = d

# Save the distance matrix to a file
np.save("nodesA.npy", np.array(nodes))
np.save("distance_matrixA.npy", dist_matrix)

