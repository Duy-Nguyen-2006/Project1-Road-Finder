from app.models.point import Point
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import math


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return c * r


def optimize_points(points: list[Point]) -> list[Point]:
    """
    Receive map points and return them in route order using TSP optimization.
    
    Uses OR-Tools to solve the Traveling Salesman Problem.
    The first point is fixed as start, the last point is fixed as end.
    Middle points are optimized for shortest total distance.
    """
    if len(points) <= 2:
        # If only start and end, no optimization needed
        return points
    
    # Extract coordinates
    locations = [(point.latitude, point.longitude) for point in points]
    n = len(locations)
    
    # Create distance matrix
    distance_matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                distance_matrix[i][j] = int(haversine_distance(
                    locations[i][0], locations[i][1],
                    locations[j][0], locations[j][1]
                ) * 1000)  # Convert to meters and round
    
    # Create the routing index manager
    manager = pywrapcp.RoutingIndexManager(n, 1, 0, [n-1])  # Start at 0, end at last point
    
    # Create Routing Model
    routing = pywrapcp.RoutingModel(manager)
    
    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]
    
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    
    # Define cost of each arc
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # Setting first solution heuristic to savings
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.SAVINGS)
    
    # Solve the problem
    solution = routing.SolveWithParameters(search_parameters)
    
    if solution:
        # Extract the optimized route
        index = routing.Start(0)
        optimized_indices = []
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            optimized_indices.append(node_index)
            index = solution.Value(routing.NextVar(index))
        
        # Return points in optimized order
        return [points[i] for i in optimized_indices]
    else:
        # If no solution found, return original order
        return points


# Example:
#
# Receive:
# [
#     Point(latitude=10.762622, longitude=106.660172),
#     Point(latitude=10.776889, longitude=106.700806),
# ]
#
# Return in first version:
# [
#     Point(latitude=10.762622, longitude=106.660172),
#     Point(latitude=10.776889, longitude=106.700806),
# ]
