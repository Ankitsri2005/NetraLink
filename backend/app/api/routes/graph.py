from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, Query
from neo4j.exceptions import Neo4jError

from ...neo4j import importer, queries
from ...neo4j.client import is_available
from ...schemas.models import (
    BetweenResponse,
    EvidenceResponse,
    GraphResponse,
    ImportSummary,
    Neo4jEntity,
    Neo4jSummary,
    NeighborLinkRecord,
    NeighborsResponse,
    TwoHopResponse,
)
from ...services import graph_service

log = logging.getLogger(__name__)

router = APIRouter(prefix="/graph", tags=["graph"])


# ─────────────────── NetworkX Analytics Graph ───────────────────


@router.get("", response_model=GraphResponse)
def get_graph():
    return graph_service.get_graph()


@router.get("/nodes/{node_id}")
def get_node(node_id: str):
    node = graph_service.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.get("/nodes/{node_id}/neighbors")
def get_neighbors(node_id: str):
    result = graph_service.get_neighbors(node_id)
    if result["node"] is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return result


# ─────────────────── Neo4j Property Knowledge Graph ───────────────────


def _guard() -> None:
    if not is_available():
        raise HTTPException(
            status_code=503,
            detail="Neo4j is not reachable. Check NEO4J_URI/NEO4J_USER/NEO4J_PASSWORD in backend/.env",
        )


def _not_found(entity_id: str) -> HTTPException:
    return HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found")


@router.get("/neo4j/health")
def neo4j_health():
    return {"available": is_available()}


@router.get("/neo4j/debug")
def neo4j_debug():
    """Temporary debug endpoint — shows connection error from Render."""
    import os
    from ...neo4j.client import NEO4J_URI, NEO4J_USER, NEO4J_DATABASE
    from neo4j import GraphDatabase
    uri = os.getenv("NEO4J_URI", NEO4J_URI)
    user = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME", NEO4J_USER)
    password = os.getenv("NEO4J_PASSWORD", "")
    db = os.getenv("NEO4J_DATABASE", NEO4J_DATABASE)
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        driver.close()
        return {"status": "connected", "uri": uri, "user": user, "database": db}
    except Exception as exc:
        return {
            "status": "failed",
            "uri": uri,
            "user": user,
            "database": db,
            "error": str(exc)[:500],
        }



@router.post("/neo4j/import", response_model=ImportSummary)
def import_neo4j_graph():
    _guard()
    try:
        return ImportSummary(**importer.import_all())
    except Neo4jError as exc:
        log.exception("Neo4j import failed")
        raise HTTPException(status_code=500, detail=f"Import failed: {exc}")


@router.get("/neo4j/summary", response_model=Neo4jSummary)
def neo4j_summary():
    _guard()
    return Neo4jSummary(**queries.summary())


@router.get("/neo4j/full", response_model=GraphResponse)
def get_neo4j_full(limit: int = Query(2000, ge=1, le=10000)):
    _guard()
    return GraphResponse(**queries.full_graph(limit=limit))


@router.get("/neo4j/entities", response_model=list[Neo4jEntity])
def search_entities(q: str = Query(..., min_length=1)):
    _guard()
    return [Neo4jEntity(**e) for e in queries.search_entities(q)]


@router.get("/neo4j/entities/{entity_id}", response_model=Neo4jEntity)
def get_neo4j_entity(entity_id: str):
    _guard()
    entity = queries.get_entity(entity_id)
    if entity is None:
        raise _not_found(entity_id)
    return Neo4jEntity(**entity)


@router.get("/neo4j/entities/{entity_id}/neighbors", response_model=NeighborsResponse)
def get_neo4j_neighbors(entity_id: str, limit: int = Query(25, ge=1, le=200)):
    _guard()
    result = queries.neighbors(entity_id, limit=limit)
    if result is None:
        raise _not_found(entity_id)
    return NeighborsResponse(
        entity=Neo4jEntity(**result["entity"]),
        neighbors=[NeighborLinkRecord(**n) for n in result["neighbors"]],
    )


@router.get(
    "/neo4j/entities/{entity_a}/relationships/{entity_b}",
    response_model=BetweenResponse,
)
def get_neo4j_between(entity_a: str, entity_b: str):
    _guard()
    result = queries.relationships_between(entity_a, entity_b)
    if result is None:
        raise _not_found(f"{entity_a}/{entity_b}")
    if result.get("other_missing"):
        missing = entity_a if result["entity"]["id"] == entity_b else entity_b
        raise _not_found(missing)
    return BetweenResponse(
        entity_a=Neo4jEntity(**result["entity_a"]),
        entity_b=Neo4jEntity(**result["entity_b"]),
        relationships=[r for r in result["relationships"]],
    )


@router.get("/neo4j/entities/{entity_id}/two-hop", response_model=TwoHopResponse)
def get_neo4j_two_hop(entity_id: str, limit: int = Query(50, ge=1, le=200)):
    _guard()
    result = queries.two_hop(entity_id, limit=limit)
    if result is None:
        raise _not_found(entity_id)
    return TwoHopResponse(
        entity=Neo4jEntity(**result["entity"]),
        first_hop=[NeighborLinkRecord(**h) for h in result["first_hop"]],
    )


@router.get("/neo4j/relationships/{relationship_id}", response_model=EvidenceResponse)
def get_relationship_evidence(relationship_id: str):
    _guard()
    result = queries.relationship_evidence(relationship_id)
    if result is None:
        raise HTTPException(
            status_code=404, detail=f"Relationship '{relationship_id}' not found"
        )
    return EvidenceResponse(
        relationship=result["relationship"],
        source_entity=Neo4jEntity(**result["source_entity"]),
        target_entity=Neo4jEntity(**result["target_entity"]),
    )