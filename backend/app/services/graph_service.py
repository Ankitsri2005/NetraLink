from __future__ import annotations

from ..aiml import loader
from ..db.database import SessionLocal
from ..db.models import Evidence


def _merge_fragments(base: dict) -> dict:
    """Merge per-case evidence fragments into the base knowledge graph."""
    db = SessionLocal()
    try:
        rows = (
            db.query(Evidence)
            .filter(Evidence.ingested_nodes.isnot(None), Evidence.ingested_edges.isnot(None))
            .all()
        )
    finally:
        db.close()

    if not rows:
        return base

    nodes = {n["id"]: n for n in base["nodes"]}
    edges = {}
    for edge in base["edges"]:
        key = (edge["source"], edge["target"], edge["type"], str(edge.get("key")))
        edges[key] = edge

    for row in rows:
        for node in row.ingested_nodes or []:
            if node.get("id"):
                existing = nodes.get(node["id"])
                nodes[node["id"]] = existing or node
        for edge in row.ingested_edges or []:
            key = (edge["source"], edge["target"], edge["type"], str(edge.get("key")))
            edges.setdefault(key, edge)

    return {"nodes": list(nodes.values()), "edges": list(edges.values())}


def get_graph() -> dict:
    return _merge_fragments(loader.graph())


def get_node(node_id: str) -> dict | None:
    graph = get_graph()
    return next((n for n in graph["nodes"] if n["id"] == node_id), None)


def get_neighbors(node_id: str) -> dict:
    graph = get_graph()
    links = []
    for edge in graph["edges"]:
        if edge["source"] != node_id and edge["target"] != node_id:
            continue
        direction = "outgoing" if edge["source"] == node_id else "incoming"
        other_id = edge["target"] if edge["source"] == node_id else edge["source"]
        other = next((n for n in graph["nodes"] if n["id"] == other_id), None)
        if other is not None:
            links.append(
                {"node": other, "relationship": edge["type"], "direction": direction}
            )
    return {"node": get_node(node_id), "links": links}