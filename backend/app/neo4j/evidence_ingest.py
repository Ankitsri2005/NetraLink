from __future__ import annotations

import re
from collections import Counter

from neo4j import Driver, Transaction, exceptions

from ..aiml import loader
from .client import get_driver, get_session


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _rid(*parts) -> str:
    cleaned = [str(p) for p in parts if p]
    return "R-" + "-".join(cleaned)


def _flat(props: dict) -> dict:
    return {k: v for k, v in props.items() if v is not None}


def _merge_node(tx: Transaction, label: str, entity_id: str, props: dict) -> None:
    tx.run(
        f"MERGE (n:{label} {{id: $id}}) SET n += $props",
        id=entity_id,
        props=props,
    )


def _rel_between(
    tx: Transaction,
    from_label: str,
    from_id: str,
    to_label: str,
    to_id: str,
    rel_type: str,
    rid: str,
    evidence: dict,
) -> None:
    query = (
        f"MATCH (a:{from_label} {{id: $from_id}}), (b:{to_label} {{id: $to_id}}) "
        f"MERGE (a)-[r:{rel_type} {{relationship_id: $rid}}]->(b) "
        f"SET r += $evidence"
    )
    tx.run(
        query,
        from_id=from_id,
        to_id=to_id,
        rid=rid,
        evidence={**evidence, "relationship_type": rel_type},
    )


def ingest_cdr(cdr_rows: list[dict], driver: Driver | None = None) -> dict:
    """Ingest parsed CDR records into the Neo4j property graph.

    Merges Phone + Location nodes, creates CALLED (phone->phone) and
    SEEN_AT (phone->location) relationships, and links phones back to
    their registered owners so uploaded evidence connects into the
    existing investigation graph.
    """
    driver = driver or get_driver()
    with get_session() as session:
        return session.execute_write(lambda tx: _ingest_cdr_work(tx, cdr_rows))


def _ingest_cdr_work(tx: Transaction, cdr_rows: list[dict]) -> dict:
    nodes = Counter()
    rels = Counter()

    phones = loader.phones()
    phone_by_id = {r["phone_id"]: r for r in phones}
    location_name_to_id = {r["location_name"]: r["location_id"] for r in loader.locations()}

    derived_locations: dict[str, dict] = {}

    def resolve_location(name: str) -> tuple[str, dict] | None:
        if not name:
            return None
        known = location_name_to_id.get(name)
        if known:
            return known, {}
        lid = "LOC-" + _slug(name)
        if lid not in derived_locations:
            derived_locations[lid] = {
                "location_name": name,
                "city": name,
                "derived": True,
            }
        return lid, derived_locations[lid]

    for row in cdr_rows:
        caller, receiver = row.get("caller_phone"), row.get("receiver_phone")
        if not caller or not receiver:
            continue

        caller_row = phone_by_id.get(caller)
        receiver_row = phone_by_id.get(receiver)

        _merge_node(
            tx,
            "Phone",
            caller,
            _flat(
                {
                    "phone_number": caller_row.get("phone_number") if caller_row else caller,
                    "person_id": caller_row.get("person_id") if caller_row else None,
                }
            ),
        )
        nodes["Phone"] += 1
        _merge_node(
            tx,
            "Phone",
            receiver,
            _flat(
                {
                    "phone_number": receiver_row.get("phone_number") if receiver_row else receiver,
                    "person_id": receiver_row.get("person_id") if receiver_row else None,
                }
            ),
        )
        nodes["Phone"] += 1

        if caller_row and caller_row.get("person_id"):
            _merge_node(tx, "Person", caller_row["person_id"], {})
            _rel_between(
                tx,
                "Person",
                caller_row["person_id"],
                "Phone",
                caller,
                "OWNS",
                _rid("OWNS", caller_row["person_id"], caller),
                {"source_record_id": caller, "confidence": 1.0},
            )
            rels["OWNS"] += 1
        if receiver_row and receiver_row.get("person_id"):
            _merge_node(tx, "Person", receiver_row["person_id"], {})
            _rel_between(
                tx,
                "Person",
                receiver_row["person_id"],
                "Phone",
                receiver,
                "OWNS",
                _rid("OWNS", receiver_row["person_id"], receiver),
                {"source_record_id": receiver, "confidence": 1.0},
            )
            rels["OWNS"] += 1

        if caller != receiver:
            _rel_between(
                tx,
                "Phone",
                caller,
                "Phone",
                receiver,
                "CALLED",
                _rid("CALLED", row.get("call_id")),
                _flat(
                    {
                        "source_record_id": row.get("call_id"),
                        "timestamp": row.get("date_time"),
                        "duration": _num(row.get("duration")),
                        "location": row.get("tower_location"),
                        "confidence": 1.0,
                    }
                ),
            )
            rels["CALLED"] += 1

        seat = resolve_location(str(row.get("tower_location") or ""))
        if seat:
            lid, props = seat
            _merge_node(tx, "Location", lid, props)
            nodes["Location"] += 1
            _rel_between(
                tx,
                "Phone",
                caller,
                "Location",
                lid,
                "SEEN_AT",
                _rid("SEEN_AT", row.get("call_id")),
                _flat(
                    {
                        "source_record_id": row.get("call_id"),
                        "timestamp": row.get("date_time"),
                        "duration": _num(row.get("duration")),
                        "location": row.get("tower_location"),
                        "confidence": 0.9,
                    }
                ),
            )
            rels["SEEN_AT"] += 1

    for lid, props in derived_locations.items():
        _merge_node(tx, "Location", lid, props)

    return {
        "nodes": dict(nodes),
        "relationships": dict(rels),
    }


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def ingest_cdr_guarded(cdr_rows: list[dict]) -> tuple[dict, bool]:
    """Ingest CDR rows, returning (summary, success). Never raises for connectivity."""
    try:
        return ingest_cdr(cdr_rows), True
    except exceptions.Neo4jError:
        return {"nodes": {}, "relationships": {}}, False
    except Exception:
        return {"nodes": {}, "relationships": {}}, False