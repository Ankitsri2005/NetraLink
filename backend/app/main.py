import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import (
    alerts,
    cases,
    fir,
    graph,
    persons,
    transactions,
)
from .db.models import Base
from .db.database import engine
from .neo4j import importer, schema
from .neo4j.client import close_driver, get_driver

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    try:
        schema.install_schema(get_driver())
        if importer.needs_import(get_driver()):
            summary = importer.import_all(get_driver())
            log.info("Seeded Neo4j knowledge graph: %s", summary)
        else:
            log.info("Neo4j knowledge graph already populated")
    except Exception:
        log.exception(
            "Neo4j unavailable at startup - graph API will return 503 until "
            "the server is reachable (NEO4J_URI=%s)",
            "set",
        )
    yield
    close_driver()


app = FastAPI(
    title="NetraLink API",
    description="Investigation graph intelligence over AIML outputs, PostgreSQL and Neo4j.",
    version="0.1.0",
    lifespan=lifespan,
)

cors_origins_env = os.getenv("CORS_ORIGINS")
if cors_origins_env:
    origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
else:
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "*"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True if "*" not in origins else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (
    alerts.router,
    persons.router,
    fir.router,
    graph.router,
    transactions.router,
    cases.router,
):
    app.include_router(router, prefix="/api/v1")


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "service": "netralink", "version": app.version}
