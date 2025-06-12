import simpy
import osmnx as ox
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt

import random

from hub import LogisticsHub

import cProfile

LOGGING = False

lambdas = [0.5,1.5,1.0,0.5]

max_lambda = max(lambdas) / 60 / 3
dist_arrival = stats.expon(scale=1/max_lambda)

lb, ub = 100, 200
loc, scale = lb, ub - lb
dist_packages = stats.uniform(loc, scale)

def lambda_t(t):
    """
    Returns the lambda value for the given time t.
    """
    if t < 6 * 60:
        return lambdas[0] / 3
    elif t < 12 * 60:
        return lambdas[1] / 3
    elif t < 18 * 60:
        return lambdas[2] / 3 
    else:
        return lambdas[3] / 3

end_time = 24 * 60

import time
start_time = time.time()
G = ox.load_graphml("eindhoven_bike_scc_simplified.graphml")
city_network = ox.convert.to_digraph(G, weight='length')
print(f"Graph loaded in {time.time() - start_time:.2f} seconds")

env = simpy.Environment()

start_time = time.time()
hubs = [
    LogisticsHub(env, "A", 12102009949, city_network, np.load("utils/nodesA.npy"), np.load("utils/distance_matrixA.npy")),
    # LogisticsHub(env, "B", 42622874, city_network),
    # LogisticsHub(env, "C", 42656333, city_network),
    # "A","B","C"
]
print(f"Hubs loaded in {time.time() - start_time:.2f} seconds")

def source(env):
    while True:
        interarrival_time = dist_arrival.rvs()
        next_time = env.now + interarrival_time
        if next_time > end_time:
            break
        yield env.timeout(interarrival_time)
        if random.random() < lambda_t(next_time) / max_lambda:
            num_packages = int(dist_packages.rvs())
            hub = random.choice(hubs)

            if LOGGING:
                print(f"Trucked arrived at {env.now} with {num_packages} packages at Hub {hub.id}")
            hub.add_parcels(num_packages)

start_time = time.time()
env.process(source(env))
env.run(until=end_time)
print(f"Simulation ran in {time.time() - start_time:.2f} seconds")

from res import Results
# Print results
if LOGGING:
    Results.print()
fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(10, 8))

# ax[0].boxplot(Results.delivery_times["delay"])
ax.hist(Results.delivery_times["delay"], bins=30, edgecolor='black')
ax.set_title("Delivery Delays")
ax.set_xlabel("Delay (minutes)")
ax.set_ylabel("Frequency")


plt.show()

# import cProfile
# import pstats
#
# cProfile.run('env.run(until=600)', 'hub_simulation.prof')
#
# # Print profiling results
# with open('hub_simulation_stats.txt', 'w') as f:
#     stats = pstats.Stats('hub_simulation.prof', stream=f)
#     stats.sort_stats('cumulative').print_stats()
#
