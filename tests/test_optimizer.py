from model.route_optimizer import optimize_route


def test_optimize_route():
    stops = [
        {"stop_name": "A", "latitude": 23.02, "longitude": 72.57},
        {"stop_name": "B", "latitude": 23.06, "longitude": 72.62},
        {"stop_name": "C", "latitude": 23.01, "longitude": 72.54},
    ]
    out = optimize_route(stops)
    assert len(out.sequence) == 3
    assert out.total_distance_km >= 0
