import simpy
import osmnx as ox
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt

import random

from hub import LogisticsHub
from res import Results
from multiprocessing import Pool

import cProfile

LOGGING = False

import time
start_time = time.time()
G = ox.load_graphml("eindhoven_bike_scc_simplified.graphml")
city_network = ox.convert.to_digraph(G, weight='length')
print(f"Graph loaded in {time.time() - start_time:.2f} seconds")

start_time = time.time()
nodes = np.load("utils/nodesA.npy")
dist_matrix = np.load("utils/distance_matrixA.npy")
print(f"Nodes and distance matrix loaded in {time.time() - start_time:.2f} seconds")

def simulation_run(seed):
    random.seed(seed)
    np.random.seed(seed)
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


    env = simpy.Environment()
    results = Results()
    hubs = [
        LogisticsHub(env, "A", 12102009949, city_network, nodes, dist_matrix, results),
        # LogisticsHub(env, "B", 42622874, city_network),
        # LogisticsHub(env, "C", 42656333, city_network),
        # "A","B","C"
]

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

    # Print results
    if LOGGING:
        results.print()

    return results
if __name__ == "__main__":
    with Pool(processes=4) as pool:
        num_runs = 100
        seeds = [random.SystemRandom().randint(0, 2**32-1) for _ in range(num_runs)]
        all_results = pool.map(simulation_run, seeds)

    all_delays = [delay for res in all_results for delay in res.delivery_times["delay"]]
    num_deliveries = [len(res.delivery_times["delay"]) for res in all_results]
    mean_num_deliveries = sum(num_deliveries) / len(num_deliveries)
    # Create subplots for delivery times and dispatches
    fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(10, 8))

    # ax[0].boxplot(Results.delivery_times["delay"])
    ax[0].hist(all_delays, bins=30, edgecolor='black', label=f"Delivery delays (n = {mean_num_deliveries})", density=True)
    ax[0].set_title("Delivery Delays")
    ax[0].set_xlabel("Delay (minutes)")
    ax[0].set_ylabel("Frequency")
    ax[0].legend(loc='upper right')

    all_dispatches = [num for res in all_results for num in res.dispatches["number of parcels"]]
    ax[1].hist(all_dispatches, bins=30, edgecolor='black', density=True)
    ax[1].set_title("Number of Parcels Dispatched")
    ax[1].set_xlabel("Number of Parcels")
    ax[1].set_ylabel("Frequency")




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
