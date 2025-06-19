import streamlit as st
import scipy.stats as stats

from res import Results
# from utils import absolute_time, log
import networkx as nx
import fast_tsp
import numpy as np

LOGGING = False

class CargoBike:
    def __init__(self, env, source, parcels: list, city_network, serviced_nodes: np.ndarray, distance_matrix: np.ndarray, results: Results):
        self.env = env
        self.source = source
        self.load_left = 200
        self.volume_left = 2100
        self.max_speed = 25
        self.max_speed_road = 40
        self.city_network = city_network
        self.nodes = serviced_nodes
        self.dist_matrix = distance_matrix
        self.current_location = source

        self.battery_capacity = 100
        self.parcels = parcels
        self.env.process(self.deliver())
        self.results = results

    def construct_route(self):
        """
        Construct a route based on the parcels to be delivered.
        The route starts at the source, visits each parcel's destination, and returns to the source.
        """
        
        node_id_to_matrix_idx_map = {node_id: i for i, node_id in enumerate(self.nodes)}
        
        # Create a list of parcel destination nodes
        ids = [parcel.destination for parcel in self.parcels]
        ids.append(self.source)
        local_dist_matrix = [[0] * len(ids) for _ in range(len(ids))]

        # Populate the sub-distance matrix
        for i, node_id_i in enumerate(ids):
            for j, node_id_j in enumerate(ids):
                if i == j: continue
                matrix_idx_i = node_id_to_matrix_idx_map[node_id_i]
                matrix_idx_j = node_id_to_matrix_idx_map[node_id_j]
                local_dist_matrix[i][j] = int(self.dist_matrix[matrix_idx_i, matrix_idx_j])
        
        tour = [ids[i] for i in fast_tsp.find_tour(local_dist_matrix)] # compute the tour, then replace IDs of indices with original IDs
        while tour[0] != self.source:
            tour.append(tour.pop(0))
        tour.append(self.source)  # Ensure the route ends at the source
        return tour
    
    def deliver(self):
        """
        Find route
        Check battery
        Dispatch
        """
        route = self.construct_route()
        # Create a list of parcels in the order they will be delivered
        ordered_parcels = []
        for node in route[1:-1]:
            for parcel in self.parcels:
                if parcel.destination == node:
                    ordered_parcels.append(parcel)
                    break
                
        # print(route, len(self.parcels), len(ordered_parcels))
        
        for i in range(len(route) - 1):
            if LOGGING:
                print(f"Traveling from {route[i]} to {route[i+1]} at time {self.env.now}")
            travel_time = self.sampleLinkTravelTime(route[i], route[i+1], self.max_speed)
            yield self.env.timeout(travel_time)
            if(len(ordered_parcels) > 0):
                self.results.register_delivery(
                    self.env.now,
                    ordered_parcels.pop(0),
                    # f"Delivering parcel {parcel.id} from {self.source} at {absolute_time(self.env.now)}. Time taken: {time_delivered:.2f} minutes."
                )
            self.current_location = route[i+1]
            if LOGGING:
                print(f"Arrived at {self.current_location} at time {self.env.now}")
        
        self.results.register_bike_route(route)
        
        # while self.parcels:
        #     parcel_to_deliver = self.parcels.pop(0)
        #     # length = nx.shortest_path_length(self.city_network, source=self.current_location, target=parcel_to_deliver.destination, weight='length')
        #     # length = 1
        #     travel_time = self.sampleLinkTravelTime(self.current_location, parcel_to_deliver.destination, self.max_speed)
        #     yield self.env.timeout(travel_time)

            
        #     if LOGGING:
        #         print(f"Delivered parcel at {self.env.now}")

    def sampleLinkTravelTime(self, node_a, node_b, v_max):
        """
        Given indices of 2 nodes on the map and a maximum speed (km/h), 
        sample a travel time between them.
        Travel time is modeled as normally distributed with:
          mu = (length in km) / v_max, and sigma = mu/20.
        Returns: travel time in minutes.
        """
        index_a = np.where(self.nodes == node_a)[0][0]
        index_b = np.where(self.nodes == node_b)[0][0]
        link_length = self.dist_matrix[index_a, index_b]  # length in meters
        length_km = link_length / 1000.0
        mu = length_km / v_max  # travel time in hours
        sigma = mu / 20.0
        dist = stats.norm(mu, sigma)
        t = dist.rvs()
        return t * 60 

    # def travel(self, time):
    #     """ Simulate travel time and battery consumption."""
    #     self.battery_capacity -= travel_time * constant # TODO: Calculate battery consumption based on distance and speed
    #     yield self.env.timeout(time)

    # def check_battery_enough(self, route):
    #     pass

    # def find_route(self):
    #     ids = [parcel.destination for parcel in self.parcels]
    #     self.source
    #     # DO MAGIC
    #     ids.insert(0, self.source)
    #     ids.append(self.source)
    #     return ids # [ hub_id , first_parcel_id, ... , last_parcel_id, hub_id ]


