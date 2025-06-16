class Results:
    """
    A class to handle the results of the simulation.
    """
    def __init__(self):
        self.delivery_times = {
            "time": [],
            "parcel_id": [],
            "delay": [],
            "delivery_timeslot": []
        }
        self.bike_routes = []
        
    def register_delivery(self, time, parcel):
        """
        Log the delivery of a parcel.
        """
        self.delivery_times["time"].append(time)
        self.delivery_times["parcel_id"].append(parcel.id)
        self.delivery_times["delivery_timeslot"].append(parcel.delivery_window)
        self.delivery_times["delay"].append(max(0, time - (parcel.delivery_window.total_seconds() / 60)))  # Delay in minutes

    def register_bike_route(self, route):
        """
        Log the route taken by a bike.
        """
        self.bike_routes.append(route)
    
    def print(self):
        """
        Print the results of the simulation.
        """
        print("Delivery Times:")
        for i in range(len(self.delivery_times["time"])):
            print(f"Parcel {self.delivery_times['parcel_id'][i]} delivered at {self.delivery_times['time'][i]} with delay {self.delivery_times['delay'][i]} minutes.")
        
        print("\nBike Routes:")
        for route in self.bike_routes:
            print(route)
            
    @staticmethod
    def aggregate_results(results_instances: list['Results']):
        """
        Aggregate results from a list of Results instances.
        Returns a tuple: (aggregated_delivery_times_dict, aggregated_bike_routes_list)
        """
        all_delivery_times = {
            "time": [], "parcel_id": [], "delay": [], "delivery timeslot": []
        }
        all_bike_routes = []

        for res_instance in results_instances:
            for key in all_delivery_times:
                all_delivery_times[key].extend(res_instance.delivery_times[key])
            all_bike_routes.extend(res_instance.bike_routes)
        
        return all_delivery_times, all_bike_routes

