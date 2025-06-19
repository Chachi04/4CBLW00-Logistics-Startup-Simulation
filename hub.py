import simpy
import numpy as np
import networkx as nx
from datetime import timedelta
import random

from parcel import Parcel
from cargobike import CargoBike
from res import Results

LOGGING = False

class LogisticsHub:
    def __init__(self, env, hub_id, location_node, city_network: nx.DiGraph, serviced_nodes: np.ndarray, distance_matrix: np.ndarray, results: Results):
        self.env = env
        self.id = hub_id
        self.location = location_node
        self.city_network = city_network
        self.serviced_nodes = serviced_nodes
        self.distance_matrix = distance_matrix
        self.parcel_queue = {str(timedelta(hours=float(key))): [] for key in np.arange(9, 19, 0.5)}
        self.vehicle_pool = simpy.Resource(env, capacity=5)
        self.starting_time = 9 # 9 AM
        self.closing_time = 19 # 7 PM
        self.available_bikes = 7
        self.bikes_resource = simpy.Resource(self.env, capacity=self.available_bikes)
        self.batteries = [Battery() for _ in range(5)]
        self.charging_stations = simpy.Resource(self.env, capacity=2)
        self.env.process(self.monitor_parcels())
        # self.serviced_nodes = self._get_reachable_nodes()
        self.dummy_hub_parcel = Parcel(destination=self.location, delivery_window=timedelta(hours=0))  # Dummy parcel for bulk delivery
        self.timeslots = [timedelta(hours=float(key)) for key in np.arange(9, 19, 0.5)] + [timedelta(days=1, hours=float(key)) for key in np.arange(9, 19, 0.5)]

        self._node_id_to_matrix_idx = {node_id: i for i, node_id in enumerate(self.serviced_nodes)}

        self.results = results

    # def _get_reachable_nodes(self):
    #     travel_times = nx.single_source_dijkstra_path_length(self.city_network, self.location, cutoff=900, weight='travel_time')
    #     return list(travel_times.keys())

    def add_parcels(self, n):
        for _ in range(n):
            delivery_window = self.choose_delivery_window()
            destination = random.choice(self.serviced_nodes)
            parcel = Parcel(destination=destination, delivery_window=delivery_window)
            if str(parcel.delivery_window) not in self.parcel_queue:
                self.parcel_queue[str(parcel.delivery_window)] = []
            self.parcel_queue[str(parcel.delivery_window)].append(parcel)

    def choose_delivery_window(self):
        choices = self.available_timeslots(self.env.now)
        return random.choice(choices)

    def available_timeslots(self, current_time):
        i = 0
        while True:
            if current_time < 9 * 60 + i * 30:
                return self.timeslots[i:]  # Return all slots from the first available one
            i+=1

    def monitor_parcels(self):
        yield self.env.timeout(self.starting_time * 60) # Wait until 9 AM
        while True:
            if self.env.now >= self.closing_time * 60:
                break
            parcels = self.parcel_queue[str(timedelta(minutes=self.env.now))].copy()
            self.parcel_queue[str(timedelta(minutes=self.env.now))] = []
            # print(len(parcels))
            bulks = self.bulk_parcels(parcels)
            # print(len(bulks))

            for bulk in bulks:
                if bulk:
                    with self.bikes_resource.request() as req:
                        yield req
                        if LOGGING:
                            print(f"Hub {self.id}: Dispatching bike with {len(bulk)} parcels at {self.env.now:.2f} minutes.")
                        CargoBike(self.env, self.location, bulk, self.city_network, self.serviced_nodes, self.distance_matrix, self.results)
                        self.results.register_dispatch(self.env.now, len(bulk))

                # self.available_bikes -= 1
                # self.available_bikes += 1

            yield self.env.timeout(30) # Check every 30 minutes

    def _cluster_destinations_kmedoids(self, dest_nodes: list, num_clusters: int, max_iter=50) -> list[list[int]]:
        """
        K-medoids clustering using Lloyd's algorithm with a distance matrix.
        dest_nodes: List of unique destination node IDs to cluster.
        k: Target number of clusters.
        Returns: List of k lists, each containing node IDs for a cluster.
        """
        if not dest_nodes or num_clusters <= 0:
            return [[] for _ in range(num_clusters)]
            
        num_unique_nodes = len(dest_nodes)
        num_clusters = min(num_clusters, num_unique_nodes) # Cannot have more clusters than unique nodes

        if num_clusters == 0:
            return [[] for _ in range(num_clusters)]

        # Initialize medoids: random sample of unique node IDs
        # Ensure medoids are part of the dest_nodes that are in _node_id_to_matrix_idx
        medoids = random.sample(dest_nodes, num_clusters)
        if not medoids and num_clusters > 0 : # Fallback if sampling failed (e.g. no nodes in map)
            return [[] for _ in range(num_clusters)]

        # Stores assignments as a list of lists of node IDs
        final_cluster_assignments = [[] for _ in range(num_clusters)]

        for _iteration in range(max_iter):
            current_cluster_assignments = [[] for _ in range(num_clusters)]
            
            # Assignment step: assign each node to the closest medoid
            for node_id in dest_nodes:
                node_matrix_idx = self._node_id_to_matrix_idx[node_id]
                min_sq_dist = float('inf')
                closest_medoid_cluster_idx = 0 # Default assignment
                
                for i, medoid_node_id in enumerate(medoids):
                    medoid_matrix_idx = self._node_id_to_matrix_idx[medoid_node_id]
                    dist = self.distance_matrix[node_matrix_idx, medoid_matrix_idx]
                    sq_dist = dist * dist 
                    
                    if sq_dist < min_sq_dist:
                        min_sq_dist = sq_dist
                        closest_medoid_cluster_idx = i
                
                current_cluster_assignments[closest_medoid_cluster_idx].append(node_id)
            
            # Update step: find new medoid for each cluster
            new_medoids = []
            medoids_changed = False
            for i in range(num_clusters):
                nodes_in_cluster_i = current_cluster_assignments[i]
                
                if not nodes_in_cluster_i:
                    # If cluster is empty, keep old medoid.
                    new_medoids.append(medoids[i] if i < len(medoids) else random.choice(dest_nodes)) # Keep old or random
                    continue

                min_total_sum_sq_dist = float('inf')
                best_new_medoid_for_cluster = nodes_in_cluster_i[0] # Default
                
                for potential_medoid_node_id in nodes_in_cluster_i:
                    # potential_medoid_node_id must be in _node_id_to_matrix_idx as it came from dest_nodes
                    potential_medoid_matrix_idx = self._node_id_to_matrix_idx[potential_medoid_node_id]
                    current_sum_sq_dist = 0
                    for member_node_id in nodes_in_cluster_i:
                        member_matrix_idx = self._node_id_to_matrix_idx[member_node_id]
                        dist = self.distance_matrix[member_matrix_idx, potential_medoid_matrix_idx]
                        current_sum_sq_dist += (dist * dist)
                    
                    if current_sum_sq_dist < min_total_sum_sq_dist:
                        min_total_sum_sq_dist = current_sum_sq_dist
                        best_new_medoid_for_cluster = potential_medoid_node_id
                
                new_medoids.append(best_new_medoid_for_cluster)
                if i >= len(medoids) or best_new_medoid_for_cluster != medoids[i]:
                    medoids_changed = True
            
            final_cluster_assignments = current_cluster_assignments # Store current assignments
            if not medoids_changed and _iteration > 0: # Check for convergence
                break 
            medoids = new_medoids
        
        # Pad with empty lists if actual_k < k (original target)
        while len(final_cluster_assignments) < num_clusters:
            final_cluster_assignments.append([])
            
        return final_cluster_assignments

    def bulk_parcels(self, parcels: list[Parcel]) -> list[list[Parcel]]:
        """
        Clusters parcels into bulks for available bikes using K-medoids.
        """
        if not parcels or self.available_bikes <= 0:
            return [[] for _ in range(self.available_bikes if self.available_bikes > 0 else 0)]

        dest_node_ids_to_cluster = set([p.destination for p in parcels])  # Unique destination node IDs
        
        if not dest_node_ids_to_cluster:
            return [[] for _ in range(self.available_bikes)]

        # 2. Perform K-medoids clustering on the unique destination node IDs
        # This helper returns list of lists of node IDs
        clustered_node_id_groups = self._cluster_destinations_kmedoids(
            list(dest_node_ids_to_cluster), 
            min(self.available_bikes, len(dest_node_ids_to_cluster)) # Use the calculated target
        ) # max_iter default is 50

        # 3. Map clustered node IDs back to Parcel objects
        parcels_by_dest_map = {} # Quick lookup: dest_id -> list of parcels
        for p in parcels:
            parcels_by_dest_map.setdefault(p.destination, []).append(p)

        # Initialize for all available bikes, some might remain empty
        final_parcel_clusters = [[] for _ in range(self.available_bikes)] 

        for i, node_id_group in enumerate(clustered_node_id_groups):
            # clustered_node_id_groups has num_clusters_target lists.
            # Populate the first num_clusters_target slots in final_parcel_clusters.
            if i < self.available_bikes: # Ensure we don't exceed bike list (shouldn't due to num_clusters_target)
                for node_id in node_id_group:
                    if node_id in parcels_by_dest_map:
                        final_parcel_clusters[i].extend(parcels_by_dest_map[node_id])
            else: # Should not be reached if num_clusters_target <= self.available_bikes
                break
        
        if LOGGING:
            print(f"Hub {self.id}: Clustered {len(parcels)} parcels into {len(final_parcel_clusters)} bulks (bikes). Sizes: {[len(b) for b in final_parcel_clusters]}")
        return final_parcel_clusters


class Battery:
    def __init__(self):
        self.charge = 100  # Battery starts fully charged

    def use(self, amount):
        self.charge -= amount
        if self.charge < 0:
            self.charge = 0

    def charge_battery(self, amount):
        self.charge += amount
        if self.charge > 100:
            self.charge = 100

if __name__ == "__main__":
    pass
    # hub = LogisticsHub("dummy", "dummy", 12102009949, "dummy_network")
    # print(hub.available_timeslots(8 * 60))  # Before opening time
    # print(hub.available_timeslots(10 * 60))
    # print(hub.available_timeslots(11.5 * 60))

    # def bulk_parcels_old_old(self, parcels) -> list[list[Parcel]]:
    #     bulk = [[self.dummy_hub_parcel] for _ in range(self.available_bikes)]
    #     while parcels:
    #         for i in range(self.available_bikes):
    #             if not parcels:
    #                 break
    #             closest_parcel = min(parcels, key=lambda p: nx.shortest_path_length(self.city_network, bulk[i][-1].destination, p.destination, weight='length'))
    #             bulk[i].append(closest_parcel)
    #             parcels.remove(closest_parcel)
    #     for i in range(self.available_bikes):
    #         bulk[i].pop(0)
    #     return bulk
    #
    # def bulk_parcels_old(self, parcels) -> list[list[Parcel]]:
    #     bulk = [[self.dummy_hub_parcel] for _ in range(self.available_bikes)]
    #     dist_from_hub = {p: nx.shortest_path_length(self.city_network, self.location, 
    #                    p.destination, weight='length') for p in parcels}
    #
    #     # Initial assignment of closest-to-hub parcels
    #     for i in range(self.available_bikes):
    #         if parcels:
    #             closest = min(parcels, key=lambda p: dist_from_hub[p])
    #             bulk[i].append(closest)
    #             parcels.remove(closest)
    #
    #     # Assign remaining parcels using last-mile optimization
    #     while parcels:
    #         for i in range(self.available_bikes):
    #             if not parcels: break
    #             last_pos = bulk[i][-1].destination
    #             closest = min(parcels, key=lambda p: 
    #                         nx.shortest_path_length(self.city_network, 
    #                         last_pos, p.destination, weight='length'))
    #             bulk[i].append(closest)
    #             parcels.remove(closest)
    #     
    #     return [route[1:] for route in bulk]
