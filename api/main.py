import logging
import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from api.routes import meta, predictions
from config.logging import setup_logging
from config.settings import get_settings
from database.db import Base, engine


settings = get_settings()
setup_logging(settings.log_level)
logger = logging.getLogger("api")
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version="1.0.0")
app.include_router(meta.router)
app.include_router(predictions.router)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 2)
    logger.info("%s %s -> %s (%sms)", request.method, request.url.path, response.status_code, duration_ms)
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
