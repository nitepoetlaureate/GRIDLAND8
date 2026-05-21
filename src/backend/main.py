"""GRIDLAND FastAPI application entry point.

Run with:  uvicorn backend.main:app --reload --port 8000
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend import __version__
from backend.api import camera_proxy as camera_proxy_routes
from backend.api import context as context_routes
from backend.api import discovery as discovery_routes
from backend.api import live_status as live_status_routes
from backend.api import photosphere as photosphere_routes
from backend.api import realtime as realtime_routes
from backend.api import satellites as satellite_routes
from backend.api import transit as transit_routes
from backend.api import whats_here as whats_here_routes
from backend.settings import get_settings

log = logging.getLogger("gridland")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="GRIDLAND",
        version=__version__,
        description="Public infrastructure visibility platform.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.include_router(discovery_routes.router)
    app.include_router(context_routes.router)
    app.include_router(photosphere_routes.router)
    app.include_router(realtime_routes.router)
    app.include_router(satellite_routes.router)
    app.include_router(transit_routes.router)
    app.include_router(whats_here_routes.router)
    app.include_router(live_status_routes.router)
    app.include_router(camera_proxy_routes.router)

    @app.get("/health", tags=["meta"])
    async def health() -> dict:
        return {"status": "ok", "version": __version__}

    return app


app = create_app()
