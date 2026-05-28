from app.models.point import Point
from app.utils.distance import haversine_distance
import requests


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


def solve_tsp_heuristic(distance_matrix: list[list[int]]) -> list[int]:
    """
    Solve TSP using Nearest Neighbor + 2-opt heuristic.
    Fixed start (index 0) and fixed end (index n-1).
    Returns list of indices representing the optimized path.
    """
    n = len(distance_matrix)
    if n <= 2:
        return list(range(n))
    
    # Step 1: Nearest Neighbor - xây dựng path ban đầu
    path = [0]  # Bắt đầu từ điểm 0
    unvisited = set(range(1, n - 1))  # Các điểm trung gian (không bao gồm 0 và n-1)
    
    current = 0
    while unvisited:
        # Tìm điểm gần nhất trong các điểm chưa thăm
        nearest = min(unvisited, key=lambda x: distance_matrix[current][x])
        path.append(nearest)
        unvisited.remove(nearest)
        current = nearest
    
    # Kết thúc tại điểm n-1
    path.append(n - 1)
    
    # Step 2: 2-opt - tối ưu path bằng cách loại bỏ các cạnh chéo nhau
    improved = True
    max_iterations = 100  # Giới hạn số lần lặp để tránh treo
    iteration = 0
    
    while improved and iteration < max_iterations:
        improved = False
        iteration += 1
        
        # Chỉ tối ưu các điểm trung gian (từ index 1 đến n-2)
        for i in range(1, n - 2):
            for j in range(i + 1, n - 1):
                # Tính chi phí hiện tại
                current_cost = (
                    distance_matrix[path[i-1]][path[i]] + 
                    distance_matrix[path[j]][path[j+1]]
                )
                # Tính chi phí sau khi đảo ngược đoạn từ i đến j
                new_cost = (
                    distance_matrix[path[i-1]][path[j]] + 
                    distance_matrix[path[i]][path[j+1]]
                )
                
                # Nếu chi phí mới tốt hơn thì đảo ngược
                if new_cost < current_cost:
                    path[i:j+1] = reversed(path[i:j+1])
                    improved = True
    
    return path


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
    3. Solves the TSP using Nearest Neighbor + 2-opt heuristic.
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
                
    # 3. Solve TSP using Nearest Neighbor + 2-opt heuristic
    optimized_indices = solve_tsp_heuristic(distance_matrix)
    ordered_snapped_points = [snapped_points[i] for i in optimized_indices]
    
    # 4. Fetch the exact road-based geometry path connecting all ordered snapped nodes
    return fetch_road_route_geometry(ordered_snapped_points)
