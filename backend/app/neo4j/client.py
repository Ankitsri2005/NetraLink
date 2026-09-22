from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

log = logging.getLogger(__name__)

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
NEO4J_USER = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

_driver: Driver | None = None


def _create_driver(uri: str, user: str, password: str) -> Driver:
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        return driver
    except Exception as exc:
        # If neo4j+s:// failed (common on Windows due to SSL certificate chain verification),
        # retry automatically with neo4j+ssc:// (encrypted TLS with self-signed/custom CA acceptance)
        if uri.startswith("neo4j+s://") or uri.startswith("bolt+s://"):
            fallback_uri = uri.replace("+s://", "+ssc://")
            log.warning("Secure connection failed for %s (%s). Retrying with %s...", uri, exc, fallback_uri)
            fallback_driver = GraphDatabase.driver(fallback_uri, auth=(user, password))
            fallback_driver.verify_connectivity()
            log.info("Successfully connected using %s", fallback_uri)
            return fallback_driver
        raise



def get_driver() -> Driver:
    global _driver
    if _driver is None:
        load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)
        uri = os.getenv("NEO4J_URI", NEO4J_URI)
        user = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME", NEO4J_USER)
        password = os.getenv("NEO4J_PASSWORD", NEO4J_PASSWORD)
        db = os.getenv("NEO4J_DATABASE", NEO4J_DATABASE)
        _driver = _create_driver(uri, user, password)
        log.info("Neo4j driver configured for %s (db=%s)", uri, db)
    return _driver


def get_session():
    """Return a session scoped to the configured database."""
    db = os.getenv("NEO4J_DATABASE", NEO4J_DATABASE)
    return get_driver().session(database=db)


def close_driver() -> None:
    global _driver
    if _driver is not None:
        try:
            _driver.close()
        except Exception:
            pass
        _driver = None


def is_available() -> bool:
    try:
        get_driver().verify_connectivity()
        return True
    except Exception as exc:
        log.debug("Neo4j is not available: %s", exc)
        return False