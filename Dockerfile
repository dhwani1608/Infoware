FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python scripts/generate_data.py && python scripts/train_model.py

EXPOSE 8000
CMD ["sh", "-c", "python scripts/seed_database.py && uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
