class Results:
    """
    A class to handle the results of the simulation.
    """

    def __init__(self):
        self.delivery_times = {
            "time": [],
            "parcel_id": [],
            "delay": [],
            "delivery timeslot": []
        }

        self.dispatches = {
            "time": [],
            "number of parcels": []
        }

        self.bike_routes = [

        ]
    # @staticmethod
    def register_delivery(self, time, parcel):
        """
        Register the delivery of a parcel.
        """
        self.delivery_times["time"].append(time)
        self.delivery_times["parcel_id"].append(parcel.id)
        self.delivery_times["delivery timeslot"].append(parcel.delivery_window)
        self.delivery_times["delay"].append(max(0, time - (parcel.delivery_window.total_seconds() / 60)))  # Delay in minutes

    def register_dispatch(self,time, n):
        """
        Register the number of parcels dispatched at a given time.
        """
        self.dispatches["time"].append(time)
        self.dispatches["number of parcels"].append(n)

    def register_bike_route(self,route):
        """
        Register the route taken by a bike.
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

