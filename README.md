# Logistics Startup Simulator

In order to verify our start-up idea, we made a discrete event stochastic
simulation using python and the SimPy library. The simulation models a
logistics company that receives parcels from partner companies at hubs by
delivery trucks arriving according to an inhomogeneous Poisson process with
different arrival rates throughout the day, stores and manages the parcels, and
sends out bikes to deliver the parcels.

We model the following processes:

- Arrival of delivery trucks at the hub
- Delivery of parcels by cargo bikes

Entities in the simluation include:

- Hub
- Cargo bike

We use the following assumptions:

- The city of Eindhoven is serviced by three hubs, each with a number of cargo bikes.
- The simulation focuses on one hub, assuming identical results for the other hubs.
- The arrival of packages at the hub is modeled as a Poisson process with rates $\lambda_t$ depending on the time of day expressed in the following table

| t     | $\lambda_t$ |
| ----- | ----------- |
| 0-6   | 0.5         |
| 6-12  | 1.0         |
| 12-18 | 1.5         |
| 18-24 | 0.5         |

- The number of packages per truck is normally distributed with mean $\mu_\text{packages}$ and standard deviation $\sigma_\text{packages}$.
- Cargo bikes have no fixed maximum capacity for number of parcels
- Parcels are randomly assigned a "time slot" for delivery,
- Time slots are defined as 30 minute intervals, starting at 8:00 AM and ending at 7:00 PM.
-

## Picked hubs

using the `eindhoven_bike_map_nodes.html` file, the following hubs were selected:

- Hub A: "12102009949"
- Hub B: "42622874"
- Hub C: "42656333"

### Possible hub locations

- Upper hub: 1285015652 / 4243150908 / 42742286
- Center hub: 309682746 (Woensel)
- Lower right hub: 5443883873
- Lower left hub: 392674444 / 8890998755

### Used hub locations:

- Hub A: 309682746
- Lower right hub: 5443883873
- Lower left hub: 392674444

## Delivery truck arrival rates

Trucks from partner companies arrive at the hubs at different rates throughout the day. The arrival rates are defined in $\lambda_t$ as follows

| t     | $\lambda_t$ |
| ----- | ----------- |
| 0-6   | 0.5         |
| 6-12  | 1.0         |
| 12-18 | 1.5         |
| 18-24 | 0.5         |

## Number of packages per truck

The number of packages per truck is normally distributed with mean $\mu_\text{packages}$ and standard deviation $\sigma_\text{packages}$

## To be discussed

- Sending messages to customers about their package arrival, asking for preferred time slot:

  - What are the time slots a customer can pick (based on arrival at hub)?
  - How long can they choose? If they don't respond, what is the default time slot?

  - What is the maximum number of packages per time slot (based on capacity)?
  - What is the maximum number of packages per cargo bike (for simulation)? Fixed maximum number of packages or calculated based on volume?
  - What is the maximum capacity of packages per hub (simulation)? Same as above?

- Tasks to be done:
  - determine nodes serviced by each hub
  - web portal app for customers
  - add simulation of actual delivery process
  - have cargo bikes as a resource
  - have a inter-hub delivery process (when a package is left at hub A, but the destination is serviced by another hub)
  - determine exact boundaries of city, which places are serviced

## Assumptions

- all packages arriving at a hub can be carried by a cargo bike
- inter-hub process:

  - separate queue for inter-hub packages
  - dispatched when no time left or bike is full

- number of bike per hub may change according to hub busyness
- batteries are removable so charging does not require bike to be in the hub
