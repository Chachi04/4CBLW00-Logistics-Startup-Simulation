class Results:
    """
    A class to handle the results of the simulation.
    """
    delivery_times = {
        "time": [],
        "parcel_id": [],
        "delay": [],
        "delivery timeslot": []
    }

    bike_routes = [

    ]
    @staticmethod
    def register_delivery(time, parcel):
        """
        Log the delivery of a parcel.
        """
        Results.delivery_times["time"].append(time)
        Results.delivery_times["parcel_id"].append(parcel.id)
        Results.delivery_times["delivery timeslot"].append(parcel.delivery_window)
        Results.delivery_times["delay"].append(max(0, time - (parcel.delivery_window.total_seconds() / 60)))  # Delay in minutes

    @staticmethod
    def register_bike_route(route):
        """
        Log the route taken by a bike.
        """
        Results.bike_routes.append(route)

