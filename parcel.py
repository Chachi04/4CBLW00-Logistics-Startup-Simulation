import uuid
import scipy.stats as stats

class Parcel:
    def __init__(self, destination, delivery_window):
        self.id = uuid.uuid1()
        self.destination = destination
        self.weight = stats.uniform(1,10).rvs()
        self.dimesions = (10,10,10)
        self.urgent = False
        self.delivery_window = delivery_window

    def __str__(self):
        return f"Parcel(id={self.id}, destination={self.destination}, weight={self.weight}, dimensions={self.dimesions}, urgent={self.urgent}, delivery_window={self.delivery_window})"
