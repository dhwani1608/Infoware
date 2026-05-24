# AI Route Prediction System

Production-grade AI route prediction backend using FastAPI, XGBoost, OR-Tools, SQLAlchemy, and Google Maps integrations.

## Features

- Daily route prediction (sequence, ETA, distance, confidence, efficiency)
- Weekly optimized stop schedule per driver
- Traffic-aware multi-stop route optimization (TSP-inspired)
- Synthetic Gujarat/Ahmedabad telemetry generation
- Feature engineering + clustering + model training pipeline
- Google Distance Matrix + Places integration with retries/rate-limit/cache
- Route map visualization with Folium
- Dynamic rerouting endpoint for live traffic changes
- Monitoring summary + dashboard endpoints
- Dockerized local deployment with PostgreSQL + Redis
- Unit tests with pytest

## Project Structure

Matches required structure under `project/`:

- `api/` FastAPI app, routes, schemas, services, dependencies
- `model/` feature engineering, clustering, trainer, predictor, optimizer
- `database/` SQLAlchemy setup, models, CRUD
- `integrations/` Google Maps, Places, and cache adapters
- `scripts/` data generation, training, and DB seed scripts
- `tests/` API/model/optimizer tests
- `config/` settings and logging

## Model Pipeline

1. Generate synthetic trips with time/day/traffic/weather/driver patterns.
2. Cluster locations using KMeans for geographic behavior features.
3. Engineer temporal, route, driver, and density features.
4. Train XGBoost regressor to predict travel time.
5. Optimize stop ordering using OR-Tools on traffic-aware duration matrix.
6. Aggregate outputs into confidence and route efficiency metrics.

Why these models:
- XGBoost: robust for tabular nonlinear traffic/driver interactions and efficient retraining.
- KMeans: lightweight geographic segmentation that scales cheaply.
- OR-Tools: reliable constrained optimization engine for route sequencing.

## Local Setup

1. Create environment:
```bash
cd project
python -m venv .venv
# Windows
.venv\\Scripts\\activate
pip install -r requirements.txt
```

2. Configure env:
```bash
copy .env.example .env
```

3. Prepare data/models/database:
```bash
python scripts/generate_data.py
python scripts/train_model.py
python scripts/seed_database.py
```

4. Run API:
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger: `http://localhost:8000/docs`

## Docker Run

```bash
cd project
copy .env.example .env
docker compose up --build
```

## GitHub Prep

Before pushing:

1. Ensure `.env` has your local secrets but is **not** committed.
2. Confirm `.gitignore` excludes local DB/cache/model artifacts.
3. Commit from `project/` root.

Example:

```bash
git init
git add .
git commit -m "Initial assignment submission"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

## Shareable Assignment Link

Local Docker is only for development on your machine.  
For evaluator access, deploy to a public platform (for example Railway) and share:

- `https://<your-app>/docs`
- `https://<your-app>/health`
- `https://<your-app>/monitoring/dashboard`

## API Endpoints

- `GET /health`
- `POST /predict/daily`
- `POST /predict/weekly`
- `POST /retrain`
- `GET /drivers`
- `GET /locations`
- `GET /route-map/{driver_id}`
- `POST /reroute/dynamic`
- `GET /monitoring/summary`
- `GET /monitoring/dashboard`

## cURL Examples

```bash
curl -X GET http://localhost:8000/health
```

```bash
curl -X POST http://localhost:8000/predict/daily ^
  -H "Content-Type: application/json" ^
  -d "{\"driver_id\":\"D1\",\"date\":\"2026-05-20\",\"locations\":[\"Store_1\",\"Store_2\",\"Store_3\",\"Store_4\"]}"
```

```bash
curl -X POST http://localhost:8000/predict/weekly ^
  -H "Content-Type: application/json" ^
  -d "{\"driver_id\":\"D1\",\"week\":\"2026-W20\"}"
```

```bash
curl -X POST http://localhost:8000/retrain
```

## Example Responses

Daily:
```json
{
  "recommended_route": ["Store_1", "Store_3", "Store_2", "Store_4"],
  "predicted_time": "3.2 hours",
  "confidence": 0.89,
  "total_distance_km": 45.2,
  "route_efficiency_score": 92.0
}
```

Weekly:
```json
{
  "monday": ["Store_7", "Store_3"],
  "tuesday": ["Store_12", "Store_6"],
  "wednesday": ["Store_2"],
  "thursday": [],
  "friday": [],
  "saturday": [],
  "sunday": [],
  "weekly_distance": "230km",
  "weekly_efficiency": 0.91
}
```

## Assumptions

- If `GOOGLE_MAPS_API_KEY` is not set, mock geospatial responses are used.
- First-stop origin is treated as optimizer start node.
- Weekly schedule is based on historical dominant stops by weekday.

## Monitoring and Operations

- Request logging middleware with latency output.
- Retrain endpoint returns MAE and R² for model quality tracking.
- Cached integration responses reduce API cost and rate pressure.

## Scalability Improvements (Roadmap)

- Redis-backed distributed cache + Celery async retraining jobs.
- PostGIS + spatial indexes for geospatial queries at scale.
- Real-time dynamic rerouting from telemetry stream ingestion.
- Model registry/versioning with canary rollout.
