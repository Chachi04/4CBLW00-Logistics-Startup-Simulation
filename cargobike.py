import streamlit as st
import scipy.stats as stats

from res import Results
# from utils import absolute_time, log
import networkx as nx

LOGGING = False

class CargoBike:
    def __init__(self, env, source, parcels, city_network):
        self.env = env
        self.source = source
        self.load_left = 200
        self.volume_left = 2100
        self.max_speed = 25
        self.max_speed_road = 40
        self.city_network = city_network
        self.current_location = source

        self.battery_capacity = 100 
        self.parcels = parcels
        self.env.process(self.deliver())


    def deliver(self):
        """
        Find route
        Check battery
        Dispatch
        """
        while self.parcels:
            parcel_to_deliver = self.parcels.pop(0)
            length = nx.shortest_path_length(self.city_network, source=self.current_location, target=parcel_to_deliver.destination, weight='length')
            # length = 1
            travel_time = self.sampleLinkTravelTime(length, self.max_speed)
            yield self.env.timeout(travel_time) 

            Results.register_delivery(
                self.env.now,
                parcel_to_deliver
                # f"Delivering parcel {parcel.id} from {self.source} at {absolute_time(self.env.now)}. Time taken: {time_delivered:.2f} minutes."
            )
            if LOGGING:
                print(f"Delivered parcel at {self.env.now}")

    def sampleLinkTravelTime(self, link_length, v_max):
        """
        Given a link length (in meters) and a maximum speed (km/h), sample a travel time.
        Travel time is modeled as normally distributed with:
          mu = (length in km) / v_max, and sigma = mu/20.
        Returns: travel time in minutes.
        """
        if link_length == float("inf"):
            print("ERRROROR")
            exit()
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


