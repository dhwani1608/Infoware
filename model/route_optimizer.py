import itertools
from dataclasses import dataclass
from typing import Dict, List
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from integrations.google_maps import GoogleMapsClient


@dataclass
class OptimizedRoute:
    sequence: List[str]
    total_distance_km: float
    total_duration_min: float


def optimize_route(
    stops: List[dict],
    traffic_level: str = "medium",
    start_index: int = 0,
    refresh_traffic: bool = False,
) -> OptimizedRoute:
    if len(stops) <= 1:
        name = stops[0]["stop_name"] if stops else ""
        return OptimizedRoute(sequence=[name] if name else [], total_distance_km=0.0, total_duration_min=0.0)
    names = [s["stop_name"] for s in stops]
    gm = GoogleMapsClient()
    n = len(stops)
    matrix = [[0 for _ in range(n)] for _ in range(n)]
    distances = [[0.0 for _ in range(n)] for _ in range(n)]
    durations = [[0.0 for _ in range(n)] for _ in range(n)]
    for i, j in itertools.product(range(n), range(n)):
        if i == j:
            continue
        payload = gm.distance_matrix(
            (stops[i]["latitude"], stops[i]["longitude"]),
            (stops[j]["latitude"], stops[j]["longitude"]),
            traffic_level,
            bypass_cache=refresh_traffic,
        )
        matrix[i][j] = int(payload["duration_min"] * 10)
        distances[i][j] = payload["distance_km"]
        durations[i][j] = payload["duration_min"]

    manager = pywrapcp.RoutingIndexManager(n, 1, start_index)
    routing = pywrapcp.RoutingModel(manager)

    def dist_callback(from_index, to_index):
        a = manager.IndexToNode(from_index)
        b = manager.IndexToNode(to_index)
        return matrix[a][b]

    transit = routing.RegisterTransitCallback(dist_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit)
    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    solution = routing.SolveWithParameters(search_params)
    if solution is None:
        return OptimizedRoute(sequence=names, total_distance_km=0.0, total_duration_min=0.0)
    index = routing.Start(0)
    route_nodes = []
    while not routing.IsEnd(index):
        route_nodes.append(manager.IndexToNode(index))
        index = solution.Value(routing.NextVar(index))

    total_distance = 0.0
    total_duration = 0.0
    for a, b in zip(route_nodes[:-1], route_nodes[1:]):
        total_distance += distances[a][b]
        total_duration += durations[a][b]
    return OptimizedRoute(sequence=[names[idx] for idx in route_nodes], total_distance_km=round(total_distance, 2), total_duration_min=round(total_duration, 2))
