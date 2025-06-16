import simpy
import osmnx as ox
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt

import random
import threading as Threading
from res import Results

from hub import LogisticsHub

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

END_TIME = 24 * 60

import time
start_time = time.time()
G = ox.load_graphml("eindhoven_bike_scc_simplified.graphml")
CITY_NETWORK = ox.convert.to_digraph(G, weight='length')
print(f"Graph loaded in {time.time() - start_time:.2f} seconds")

HUB_CONFIG = {
    'id': 'A',
    "location_node": 12102009949,
}


start_time = time.time()
try:
    HUB_CONFIG["serviced_nodes"] = np.load("utils/nodesA.npy")
    HUB_CONFIG["distance_matrix"] = np.load("utils/distance_matrixA.npy")
except FileNotFoundError as e:
    print(f"ERROR: Data file not found: {e}. Exiting.")
    exit()
print(f"Hub loaded in {time.time() - start_time:.2f} seconds")


def run_single_sim(sim_id: int):
    """
    Runs a single instance of the logistics simulation.
    Each simulation run needs its own SimPy environment and random generators for independence.
    """
    if LOGGING:
        print(f"[Sim {sim_id}] Starting simulation run.")
    
    env = simpy.Environment()
    current_results = Results()
    hub = LogisticsHub(env, HUB_CONFIG['id'], HUB_CONFIG["location_node"], CITY_NETWORK,
                       HUB_CONFIG["serviced_nodes"], HUB_CONFIG["distance_matrix"],
                       current_results)
    def source(env, hub):
        # print(hub)
        while True:
            interarrival_time = dist_arrival.rvs()
            next_time = env.now + interarrival_time
            if next_time > END_TIME:
                break
            yield env.timeout(interarrival_time)
            if random.random() < lambda_t(next_time) / max_lambda:
                num_packages = int(dist_packages.rvs())

                if LOGGING:
                    print(f"Trucked arrived at {env.now} with {num_packages} packages at Hub {hub.id}")
                hub.add_parcels(num_packages)
                
    start_time = time.time()
    env.process(source(env, hub))
    env.run(until=END_TIME)
    if LOGGING:
        print(f"[Sim {sim_id}] Simulation run completed in {time.time() - start_time:.2f} minutes.")
    return current_results

if __name__ == "__main__":
    NUM_SIMULATIONS = 1
    all_results = []
    threads = []

    print(f"Starting {NUM_SIMULATIONS} simulation runs using threads...")
    overall_start_time = time.time()

    for sim_id in range(NUM_SIMULATIONS):
        thread = Threading.Thread(target=lambda: all_results.append(run_single_sim(sim_id)))
        threads.append(thread)
        thread.start()
    
    for thread_idx, thread in enumerate(threads):
        if LOGGING: print(f"Waiting for thread {thread_idx} to complete...")
        thread.join()
        if LOGGING: print(f"Thread {thread_idx} completed.")
    
    print(f"All simulations completed in {time.time() - overall_start_time:.2f} seconds.")
    
    if not all_results:
        print("No results collected from simulations.")
    else:
        print(f"Aggregating results from {len(all_results)} runs...")
        # Use the static method from Results class to aggregate
        aggregated_deliveries, aggregated_routes = Results.aggregate_results(all_results)
        
        print(f"Total deliveries logged: {len(aggregated_deliveries['time'])}")
        print(f"Total bike routes logged: {len(aggregated_routes)}")

        # Now plot the aggregated results
        if aggregated_deliveries["delay"]:
            fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(10, 8))
            n, bins, _ = ax.hist(aggregated_deliveries["delay"], bins=50, edgecolor='black') # Increased bins for more data
            ax.set_title(f"Aggregated Delivery Delays ({NUM_SIMULATIONS} runs)")
            ax.set_xlabel("Delay (minutes)")
            ax.set_ylabel("Frequency")
            
            for i in range(len(n)):
                ax.text(bins[i] + (bins[1]-bins[0])/2, n[i], str(int(n[i])), ha='center', va='bottom')

            plt.show()
        else:
            print("No delivery delays recorded to plot.")

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
