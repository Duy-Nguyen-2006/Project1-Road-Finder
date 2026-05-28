from app.models.point import Point
import math
import requests


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


def find_closest_intersection(point: Point, intersections: list[dict]) -> Point:
    """
    Find the closest intersection node (from OSM) for a given point.
    Returns a new Point representing the intersection node coordinates.
    """
    if not intersections:
        return point
        
    best_node = None
    min_dist = float('inf')
    
    # Use Euclidean squared distance for extremely fast local snapping
    for node in intersections:
        lat = node.get('latitude')
        lon = node.get('longitude')
        if lat is None or lon is None:
            continue
            
        dist_sq = (point.latitude - lat)**2 + (point.longitude - lon)**2
        if dist_sq < min_dist:
            min_dist = dist_sq
            best_node = node
            
    if best_node:
        return Point(latitude=best_node['latitude'], longitude=best_node['longitude'])
    return point


def solve_tsp_branch_and_bound(distance_matrix: list[list[int]]) -> list[int]:
    """
    Solve the TSP with a fixed start (index 0) and fixed end (index n-1)
    using a custom Branch & Bound algorithm with a nearest-neighbor heuristic.
    """
    n = len(distance_matrix)
    if n <= 2:
        return list(range(n))
        
    best_path = list(range(n))
    best_cost = float('inf')
    
    # Precompute min outgoing edge for each node (excluding itself)
    min_edges = []
    for i in range(n):
        edges = [distance_matrix[i][j] for j in range(n) if i != j]
        min_edges.append(min(edges) if edges else 0)
        
    def get_lower_bound(curr, unvisited):
        if not unvisited:
            return distance_matrix[curr][n-1]
            
        # Add minimum distance from current node to any unvisited node
        lb = min(distance_matrix[curr][u] for u in unvisited)
        # Add minimum outgoing edge for all remaining unvisited nodes
        for u in unvisited:
            lb += min_edges[u]
        return lb

    def dfs(curr, unvisited, path, cost):
        nonlocal best_cost, best_path
        
        # Calculate lower bound and prune if it exceeds current best cost
        lb = get_lower_bound(curr, unvisited)
        if cost + lb >= best_cost:
            return
            
        if not unvisited:
            # Connect the last waypoint to the fixed end node (n-1)
            total_cost = cost + distance_matrix[curr][n-1]
            if total_cost < best_cost:
                best_cost = total_cost
                best_path = path + [n-1]
            return
            
        # Branch-ordering: visit nearest neighbors first to find good upper bound early
        sorted_unvisited = sorted(unvisited, key=lambda u: distance_matrix[curr][u])
        for next_node in sorted_unvisited:
            dfs(next_node, unvisited - {next_node}, path + [next_node], cost + distance_matrix[curr][next_node])

    # Search: Start at 0, intermediate waypoints are indices 1 to n-2, end is n-1
    dfs(0, set(range(1, n-1)), [0], 0)
    return best_path


def fetch_road_route_geometry(points: list[Point]) -> list[Point]:
    """
    Queries the public OSRM Routing API to get the detailed street-level geometry
    connecting all coordinates in the given order.
    """
    if len(points) < 2:
        return points
        
    # OSRM coordinates path format: lon1,lat1;lon2,lat2;...
    coord_strings = [f"{p.longitude},{p.latitude}" for p in points]
    coords_path = ";".join(coord_strings)
    
    url = f"http://router.project-osrm.org/route/v1/driving/{coords_path}?overview=full&geometries=geojson"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") == "Ok" and data.get("routes"):
            route = data["routes"][0]
            geometry = route.get("geometry", {})
            coordinates = geometry.get("coordinates", [])
            
            # Convert GeoJSON [longitude, latitude] to list[Point]
            road_points = []
            for coord in coordinates:
                road_points.append(Point(latitude=coord[1], longitude=coord[0]))
                
            return road_points
            
    except Exception as e:
        print(f"Warning: Failed to fetch OSRM road geometry: {e}")
        
    # Fallback to returning original points if API fails or offline
    return points


def optimize_points(points: list[Point], intersections: list[dict] = None) -> list[Point]:
    """
    Receive map points, optimize their visiting order, and return
    the detailed street-level road coordinates path.
    
    1. Optionally snaps each selected point to the nearest OSM intersection.
    2. Builds a distance matrix using Haversine formula.
    3. Solves the TSP using a custom Branch & Bound algorithm.
    4. Fetches the exact street-level path geometry from OSRM API.
    """
    # 1. Snap to nearest intersections if provided
    snapped_points = []
    if intersections:
        for p in points:
            snapped_points.append(find_closest_intersection(p, intersections))
    else:
        snapped_points = points
        
    if len(points) <= 2:
        # If only start and end, fetch road geometry between snapped points directly
        return fetch_road_route_geometry(snapped_points)
        
    n = len(snapped_points)
    
    # 2. Create distance matrix (in meters)
    distance_matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                distance_matrix[i][j] = int(haversine_distance(
                    snapped_points[i].latitude, snapped_points[i].longitude,
                    snapped_points[j].latitude, snapped_points[j].longitude
                ) * 1000)  # Convert to meters
                
    # 3. Solve TSP using custom Branch & Bound
    optimized_indices = solve_tsp_branch_and_bound(distance_matrix)
    ordered_snapped_points = [snapped_points[i] for i in optimized_indices]
    
    # 4. Fetch the exact road-based geometry path connecting all ordered snapped nodes
    return fetch_road_route_geometry(ordered_snapped_points)
