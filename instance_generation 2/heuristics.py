import heapq
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict, deque

# Load the arc data

arcs_df = pd.read_csv('instance_generation 2/arcs_gen/arcs.csv')

def get_dynamic_travel_time(origin, destination, current_time):
    """Retrieve the dynamic travel time from the arcs data based on the current time."""
    day = current_time.strftime("%Y-%m-%d")
    time_str = current_time.strftime("%H:%M:%S")
    
    matching_arc = arcs_df[
        (arcs_df['From'] == origin) &
        (arcs_df['To'] == destination) &
        (arcs_df['Day'] == day) &
        (arcs_df['Time'] == time_str)
    ]
    
    if not matching_arc.empty:
        duration_str = matching_arc.iloc[0]['Duration']
        duration_minutes = int(duration_str.split()[0])
        return timedelta(minutes=duration_minutes)
    else:
        return timedelta(hours=1)  # Penalty if no direct route is found

def parse_time(time_str):
    return datetime.strptime(time_str, "%H:%M:%S")

def add_time(start_time, duration):
    return start_time + duration

def check_capacity(vehicle, request):
    return vehicle['Capacity'] >= request['PartySize']

def check_time_window(vehicle_arrival, request):
    earliest_pickup = parse_time(request['Earliest'])
    latest_arrival = parse_time(request['Latest'])
    return earliest_pickup <= vehicle_arrival <= latest_arrival

def dijkstra_shortest_path(origin, destination, current_time):
    distances = {origin: timedelta(0)}
    previous_nodes = {origin: None}
    pq = [(timedelta(0), origin)]

    while pq:
        current_distance, current_node = heapq.heappop(pq)
        
        if current_node == destination:
            break

        current_arcs = arcs_df[(arcs_df['From'] == current_node)]
        
        for _, arc in current_arcs.iterrows():
            next_node = arc['To']
            travel_time = get_dynamic_travel_time(current_node, next_node, current_time)
            new_distance = current_distance + travel_time
            
            if new_distance < distances.get(next_node, timedelta.max):
                distances[next_node] = new_distance
                previous_nodes[next_node] = current_node
                heapq.heappush(pq, (new_distance, next_node))
        
        current_time += timedelta(minutes=1)

    path = deque()
    while destination:
        path.appendleft(destination)
        destination = previous_nodes[destination]

    return list(path), distances[path[-1]]

def check_compatibility(vehicle, request, current_time):
    """Check if adding this request is compatible with the vehicle's current route"""
    # Evaluate if the request can be added without disrupting the existing schedule
    potential_route, _ = dijkstra_shortest_path(vehicle['CurrentLocation'], request['Origin'], current_time)
    
    travel_time_to_pickup = get_dynamic_travel_time(vehicle['CurrentLocation'], request['Origin'], current_time)
    arrival_time_at_pickup = add_time(current_time, travel_time_to_pickup)
    
    if check_time_window(arrival_time_at_pickup, request) and check_capacity(vehicle, request):
        # Now check if the request can be added to the current route of the vehicle
        new_route = vehicle.get('Route', []) + potential_route
        if request['Destination'] not in new_route:
            new_route.append(request['Destination'])
        
        vehicle['Route'] = new_route
        return True
    
    return False

def assign_request(vehicle, request, current_time, assignment):
    travel_time_to_pickup = get_dynamic_travel_time(vehicle['CurrentLocation'], request['Origin'], current_time)
    arrival_time_at_pickup = add_time(current_time, travel_time_to_pickup)
    
    if check_capacity(vehicle, request) and check_time_window(arrival_time_at_pickup, request):
        # Find the best route from pickup to destination
        path, travel_time = dijkstra_shortest_path(request['Origin'], request['Destination'], arrival_time_at_pickup)
        
        # Check if this route can include more than one request
        if check_compatibility(vehicle, request, current_time):
            assignment[vehicle['Name']].append({
                "Request": request['Name'],
                "Path": path,
                "Pickup": request['Origin'],
                "Dropoff": request['Destination']
            })
            
            # Update vehicle's state after assignment
            vehicle['Capacity'] -= request['PartySize']
            vehicle['CurrentLocation'] = request['Destination']
            vehicle['CurrentTime'] = add_time(arrival_time_at_pickup, travel_time)
            
            print(f"Assigned {request['Name']} to {vehicle['Name']} with path: {path} and travel time: {travel_time}.")
            return True
    
    return False

def score_request(vehicle, request, current_time):
    """Score a request based on time window, distance, and potential future impact"""
    travel_time_to_pickup = get_dynamic_travel_time(vehicle['CurrentLocation'], request['Origin'], current_time)
    arrival_time_at_pickup = add_time(current_time, travel_time_to_pickup)
    
    # Calculate time window tightness
    time_window_tightness = (parse_time(request['Latest']) - arrival_time_at_pickup).total_seconds() / 60
    
    # Estimate the impact on the vehicle's route
    path, route_impact = dijkstra_shortest_path(request['Origin'], request['Destination'], arrival_time_at_pickup)
    
    # Calculate distance to pickup
    distance_score = travel_time_to_pickup.total_seconds() / 60
    
    # Combine scores, with higher weight on time window tightness
    return time_window_tightness - route_impact.total_seconds() / 60 - distance_score


def main(instance):
    vehicles = instance['Vehicles']
    requests = sorted(instance['Requests'], key=lambda x: parse_time(x['PreDeparture']))
    
    for vehicle in vehicles:
        vehicle['CurrentLocation'] = vehicle['Origin']
        vehicle['CurrentTime'] = parse_time("08:00:00")
        vehicle['Route'] = []

    assignment = defaultdict(list)
    
    for request in requests:
        print(f"Trying to assign {request['Name']}...")
        
        best_vehicle = None
        best_score = float('-inf')
        
        for vehicle in vehicles:
            print(f"Checking vehicle {vehicle['Name']} - Location: {vehicle['CurrentLocation']}, Time: {vehicle['CurrentTime']}, Capacity: {vehicle['Capacity']}")
            if vehicle['CurrentTime'] <= parse_time(request['Latest']):
                score = score_request(vehicle, request, vehicle['CurrentTime'])
                print(f"Score for {vehicle['Name']} to take {request['Name']}: {score}")
                if score > best_score:
                    best_score = score
                    best_vehicle = vehicle
        
        if best_vehicle:
            if assign_request(best_vehicle, request, best_vehicle['CurrentTime'], assignment):
                print(f"Successfully assigned {request['Name']} to {best_vehicle['Name']}.")
            else:
                print(f"Failed to assign {request['Name']} to {best_vehicle['Name']}.")
        else:
            print(f"Request {request['Name']} could not be assigned to any vehicle.")
    
    return assignment

# Example usage with provided instances
instance = {
    "Vehicles": [
        {
            "Name": "V_0",
            "Capacity": 5,
            "Origin": "Settimo"
        },
        {
            "Name": "V_1",
            "Capacity": 5,
            "Origin": "Nichelino"
        }
    ],
    "Requests": [
        {
            "Name": "R_0",
            "Earliest": "08:00:00",
            "PreDeparture": "08:47:00",
            "PreArrival": "09:43:00",
            "Latest": "10:00:00",
            "MaxTransfer": 1,
            "PartySize": 1,
            "Origin": "Collegno",
            "Destination": "Orbassano"
        },
        {
            "Name": "R_1",
            "Earliest": "08:00:00",
            "PreDeparture": "08:56:00",
            "PreArrival": "09:47:00",
            "Latest": "10:00:00",
            "MaxTransfer": 4,
            "PartySize": 3,
            "Origin": "Grugliasco",
            "Destination": "Orbassano"
        },
        {
            "Name": "R_2",
            "Earliest": "08:00:00",
            "PreDeparture": "08:21:00",
            "PreArrival": "09:27:00",
            "Latest": "10:00:00",
            "MaxTransfer": 4,
            "PartySize": 1,
            "Origin": "Grugliasco",
            "Destination": "Pinerolo"
        }
    ]
}

assignment = main(instance)
print(assignment)
