import osmnx as ox
import folium

# Create the bike network graph for Eindhoven
# G = ox.graph_from_place("Eindhoven, Netherlands", network_type="bike")
G = ox.load_graphml("eindhoven_bike_scc_simplified.graphml")

# Calculate the centroid of the graph nodes for map centering
x_coords = [data['x'] for _, data in G.nodes(data=True)]
y_coords = [data['y'] for _, data in G.nodes(data=True)]
center = (sum(y_coords) / len(y_coords), sum(x_coords) / len(x_coords))

# Create a folium map centered around the graph's centroid
m = folium.Map(location=center, zoom_start=13)

# Add nodes to the map with popups showing the node id
for node, data in G.nodes(data=True):
    folium.CircleMarker(location=(data['y'], data['x']), radius=3, color='red', fill=True,
                        fill_color='red', popup=str(node)).add_to(m)

# Save the map to an HTML file
m.save('eindhoven_bike_network_simplified.html')
