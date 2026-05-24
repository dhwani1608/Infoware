from functools import lru_cache
from model.predictor import RoutePredictor


@lru_cache
def get_predictor() -> RoutePredictor:
    return RoutePredictor()
