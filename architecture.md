# Architecture
![Architecture Diagram](assets/infoware_arch.png)

## High-Level Design

1. Data Layer
- Synthetic data generator creates realistic Gujarat trip telemetry.
- SQLAlchemy models persist drivers, locations, trips, and predictions.

2. ML Layer
- KMeans clusters locations to encode geographical behavior.
- Feature engineering produces temporal, route, driver, and location signals.
- XGBoost predicts travel time per stop/leg.

3. Optimization Layer
- OR-Tools solves a traffic-aware TSP-style route sequencing problem.
- Google Maps distance matrix enriches pairwise durations/distances.

4. API Layer
- FastAPI endpoints serve health, metadata, predictions, retraining, and map output.
- Pydantic schemas validate payloads and drive OpenAPI docs.

5. Integration Layer
- Google Maps/Places clients include retry, caching, and rate limiting.
- When API keys are missing, deterministic mock responses keep the app functional.

## Scalability Notes

- Stateless API service for horizontal scaling.
- Swappable DB (`DATABASE_URL`) for SQLite or PostgreSQL.
- Model artifacts stored in mounted volume/object-store compatible path.
- Cache abstraction supports file cache now and Redis extension next.

## Future Improvements

- Add online learning and drift monitoring.
- Add vehicle constraints/capacity in optimizer.
- Use distributed task queue for asynchronous retraining and batch weekly optimization.
