import json
import random
from datetime import datetime, timedelta
import heapq


with open('parameters.json', 'r') as file:
    parameters = json.load(file)['Parameters']

with open("arcs_gen/init_arcs.json", "r") as file:
    data = json.load(file)
    cities = list({row['From'] for row in data['arcs']}.union({row['To'] for row in data['arcs']}))
    arcs = data['arcs']

# Create a graph representation from arcs
graph = {}
for arc in arcs:
    from_city = arc['From']
    to_city = arc['To']
    duration = int(arc['Duration'].split()[0])  # duration to minutes

    if from_city not in graph:
        graph[from_city] = []
    if to_city not in graph:
        graph[to_city] = []
    
    graph[from_city].append((to_city, duration))
    graph[to_city].append((from_city, duration))  # bidirectional

def dijkstra(graph, start, end):
    """Compute the shortest path between start and end cities using Dijkstra's algorithm."""
    queue = [(0, start)]
    distances = {city: float('inf') for city in graph}
    distances[start] = 0

    while queue:
        current_distance, current_city = heapq.heappop(queue)

        if current_city == end:
            break

        if current_distance > distances[current_city]:
            continue

        for neighbor, weight in graph[current_city]:
            distance = current_distance + weight

            if distance < distances[neighbor]:
                distances[neighbor] = distance
                heapq.heappush(queue, (distance, neighbor))

    return distances[end]

def random_time_in_range(start, end):
    start_time = datetime.strptime(start, "%H:%M:%S")
    end_time = datetime.strptime(end, "%H:%M:%S")
    random_time = start_time + timedelta(seconds=random.randint(0, int((end_time - start_time).total_seconds())))
    return random_time.strftime("%H:%M:00")

def generate_vehicles(num_vehicles):
    vehicles = []
    for i in range(num_vehicles):
        vehicle = {
            'Name': f'V_{i}',
            'Capacity': random.randint(*parameters['Vehicles']['CapacityRange']),
            'Origin': random.choice(cities),
        }
        vehicles.append(vehicle)
    return vehicles

def generate_requests(num_requests):
    """Generate request data with realistic time windows."""
    requests = []
    for i in range(num_requests):
        origin = random.choice(cities)
        destination = random.choice([city for city in cities if city != origin])

        # Compute shortest travel time between origin and destination
        travel_time = dijkstra(graph, origin, destination)

        # Calculate the maximum allowable pre-departure time
        latest_arrival = parameters['Requests']['LatestArrivalTime']
        max_pre_departure_time = (datetime.strptime(latest_arrival, "%H:%M:%S") - timedelta(minutes=travel_time)).strftime("%H:%M:%S")
        earliest_departure = parameters['Requests']['EarliestDepartureTimeRange']

        # Randomly select a pre-departure time between 08:00:00 and the calculated max_pre_departure_time
        pre_departure_time = random_time_in_range(earliest_departure, max_pre_departure_time)
        
        # Calculate the pre-arrival time based on pre-departure and travel time
        pre_arrival_time = (datetime.strptime(pre_departure_time, "%H:%M:%S") + timedelta(minutes=travel_time)).strftime("%H:%M:%S")
        
        # Adjust pre-departure time if pre-arrival exceeds the latest allowed arrival time
        if datetime.strptime(pre_arrival_time, "%H:%M:%S") > datetime.strptime(latest_arrival, "%H:%M:%S"):
            # Calculate the excess time and adjust pre-departure
            excess_time = datetime.strptime(pre_arrival_time, "%H:%M:%S") - datetime.strptime(latest_arrival, "%H:%M:%S")
            pre_departure_time = (datetime.strptime(pre_departure_time, "%H:%M:%S") - excess_time).strftime("%H:%M:%S")
            pre_arrival_time = latest_arrival  # Set pre-arrival to the latest possible time
        
        request = {
            'Name': f'R_{i}',
            'Earliest': earliest_departure,
            'PreDeparture': pre_departure_time,
            'PreArrival': pre_arrival_time,
            'Latest': latest_arrival,
            'MaxTransfer': random.choice(parameters['Requests']['MaxTransfers']),
            'PartySize': random.randint(*parameters['Requests']['PartySizeRange']),
            'Origin': origin,
            'Destination': destination,
        }
        requests.append(request)
    return requests

def generate_instance(num_vehicles, num_requests):
    vehicles = generate_vehicles(num_vehicles)
    requests = generate_requests(num_requests)
    return {"Vehicles": vehicles, "Requests": requests}

if __name__ == "__main__":
    num_vehicles = 2
    num_requests = 3

    instance = generate_instance(num_vehicles, num_requests)

    print(json.dumps(instance, indent=4))
