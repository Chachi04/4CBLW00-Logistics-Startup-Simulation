import simpy
import numpy as np
import networkx as nx
import osmnx as ox
from datetime import timedelta
import random
import math

from parcel import Parcel
from cargobike import CargoBike

LOGGING = False

class LogisticsHub:
    def __init__(self, env, hub_id, location_node, city_network: nx.MultiDiGraph):
        self.env = env
        self.id = hub_id
        self.location = location_node
        self.city_network = city_network
        self.parcel_queue = {str(timedelta(hours=float(key))): [] for key in np.arange(9, 19, 0.5)}
        self.vehicle_pool = simpy.Resource(env, capacity=5)
        self.starting_time = 9 # 9 AM
        self.closing_time = 19 # 7 PM
        self.available_bikes = 10
        self.bikes_resource = simpy.Resource(self.env, capacity=self.available_bikes)
        self.batteries = [Battery() for _ in range(5)]
        self.charging_stations = simpy.Resource(self.env, capacity=2)
        self.env.process(self.monitor_parcels())
        self.serviced_nodes = self._get_reachable_nodes()
        self.dummy_hub_parcel = Parcel(destination=self.location, delivery_window=timedelta(hours=0))  # Dummy parcel for bulk delivery
        self.timeslots = [timedelta(hours=float(key)) for key in np.arange(9, 19, 0.5)] + [timedelta(days=1, hours=float(key)) for key in np.arange(9, 19, 0.5)]

    def _get_reachable_nodes(self):
        travel_times = nx.single_source_dijkstra_path_length(self.city_network, self.location, cutoff=900, weight='travel_time')
        return list(travel_times.keys())

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
                            print(f"Dispatching {bulks} bulks at Hub {self.id} at {self.env.now}")
                        CargoBike(self.env, self.location, bulk, self.city_network)

                # self.available_bikes -= 1
                # self.available_bikes += 1

            yield self.env.timeout(30) # Check every 30 minutes



    def bulk_parcels(self, parcels) -> list[list[Parcel]]:
        # Fast distance-from-hub precomputation
        hub_distances = {
            p: nx.shortest_path_length(self.city_network, self.location, 
                                    p.destination, weight='length')
            for p in parcels
        }
        
        # Sort all parcels by distance from hub (ascending)
        sorted_parcels = sorted(parcels, key=lambda p: hub_distances[p])
        
        # Simple round-robin distribution to bikes
        bike_routes = [[] for _ in range(self.available_bikes)]
        for i, parcel in enumerate(sorted_parcels):
            bike_routes[i % self.available_bikes].append(parcel)
        
        # Fast nearest-neighbor ordering within each bike's parcels
        for i in range(self.available_bikes):
            route = bike_routes[i]
            if not route:
                continue
                
            # Start from hub
            current_node = self.location
            ordered_route = []
            
            while route:
                # Find next closest parcel to current position
                next_parcel = min(route, key=lambda p: 
                    nx.shortest_path_length(self.city_network, current_node,
                                        p.destination, weight='length'))
                ordered_route.append(next_parcel)
                route.remove(next_parcel)
                current_node = next_parcel.destination
                
            bike_routes[i] = ordered_route
        
        return bike_routes


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
    hub = LogisticsHub("dummy", "dummy", 12102009949, "dummy_network")
    print(hub.available_timeslots(8 * 60))  # Before opening time
    print(hub.available_timeslots(10 * 60))
    print(hub.available_timeslots(11.5 * 60))

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

