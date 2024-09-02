import json
import random
from datetime import datetime, timedelta




with open('instance_generation 2/parameters.json', 'r') as file:
    parameters = json.load(file)['Parameters']


with open("instance_generation 2/arcs_gen/init_arcs.json", "r") as file:
    data = json.load(file)
    cities = list({row['From'] for row in data['arcs']}.union({row['To'] for row in data['arcs']}))


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
    requests = []
    for i in range(num_requests):
        request = {
            'Name': f'R_{i}',
            'Earliest': parameters['Requests']['EarliestDepartureTimeRange'],
            'PreDeparture': random_time_in_range(*parameters['Requests']['PreferredDepartureTimeRange']),
            'PreArrival': random_time_in_range(*parameters['Requests']['PreferredArrivalTimeRange']),
            'Latest': parameters['Requests']['LatestArrivalTime'],
            'MaxTransfer': random.choice(parameters['Requests']['MaxTransfers']),
            'PartySize': random.randint(*parameters['Requests']['PartySizeRange']),
            'Origin': random.choice(cities),
            'Destination': random.choice(cities),
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
