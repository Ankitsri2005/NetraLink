from __future__ import annotations

from neo4j import Driver

from .client import get_driver, get_session

CORE_FIELDS = (
    "relationship_id",
    "source_record_id",
    "timestamp",
    "confidence",
    "amount",
    "duration",
    "location",
)


def _scalar(value):
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    try:
        from neo4j.time import Date, DateTime, Time

        if isinstance(value, (Date, DateTime, Time)):
            return value.iso_format()
    except ImportError:
        pass
    return str(value)


def _scalar_map(props: dict) -> dict:
    return {k: _scalar(v) for k, v in props.items()}


def _entity(node) -> dict | None:
    if node is None:
        return None
    props = _scalar_map(dict(node))
    entity_id = props.get("id")
    if entity_id is None:
        entity_id = node.element_id
    labels = list(node.labels)
    type_order = {
        "Person": 0,
        "Phone": 1,
        "Account": 2,
        "Vehicle": 3,
        "Location": 4,
        "Fir": 5,
        "Incident": 6,
    }
    labels.sort(key=lambda label: type_order.get(label, 99))
    entity_type = labels[0] if labels else "Entity"
    return {"id": entity_id, "type": entity_type, "properties": props}


def _relationship(
    rel, src_id, dst_id, src_type=None, dst_type=None
) -> dict:
    props = _scalar_map(dict(rel))
    record = {
        "relationship_id": props.get("relationship_id"),
        "relationship_type": rel.type,
        "source": src_id,
        "target": dst_id,
        "source_type": src_type,
        "target_type": dst_type,
    }
    for field in CORE_FIELDS:
        record[field] = props.get(field)
    record["properties"] = {
        k: v for k, v in props.items() if k not in CORE_FIELDS
    }
    return record


def _get(driver: Driver, query: str, **params) -> list[dict]:
    with get_session() as session:
        result = session.run(query, **params)
        return list(result)


def get_entity(entity_id: str, driver: Driver | None = None) -> dict | None:
    driver = driver or get_driver()
    records = _get(
        driver,
        "MATCH (e {id: $entity_id}) RETURN e, head(labels(e)) AS etype",
        entity_id=entity_id,
    )
    return _entity(records[0]["e"]) if records else None


def search_entities(
    query: str, limit: int = 50, driver: Driver | None = None
) -> list[dict]:
    driver = driver or get_driver()
    records = _get(
        driver,
        """
        MATCH (n)
        WHERE n.id = $q OR n.name = $q OR n.name CONTAINS $q
           OR n.phone_number = $q OR n.account_number = $q
           OR n.registration_number = $q
        RETURN n
        LIMIT $limit
        """,
        q=query,
        limit=limit,
    )
    return [_entity(r["n"]) for r in records]


def neighbors(
    entity_id: str, limit: int = 25, driver: Driver | None = None
) -> dict | None:
    driver = driver or get_driver()
    entity = get_entity(entity_id, driver=driver)
    if entity is None:
        return None

    records = _get(
        driver,
        """
        MATCH (e {id: $entity_id})-[r]-(n)
        RETURN n, r,
               head(labels(n)) AS ntype,
               head(labels(e)) AS etype,
               startNode(r).id AS src_id,
               endNode(r).id AS dst_id
        ORDER BY n.id
        LIMIT $limit
        """,
        entity_id=entity_id,
        limit=limit,
    )
    links = []
    for rec in records:
        src_id = rec["src_id"]
        dst_id = rec["dst_id"]
        direction = "outgoing" if src_id == entity_id else "incoming"
        src_type = rec["etype"] if direction == "outgoing" else rec["ntype"]
        dst_type = rec["ntype"] if direction == "outgoing" else rec["etype"]
        links.append(
            {
                "node": _entity(rec["n"]),
                "relationship": _relationship(
                    rec["r"], src_id, dst_id, src_type, dst_type
                ),
                "direction": direction,
            }
        )
    return {"entity": entity, "neighbors": links}


def relationships_between(
    entity_a: str, entity_b: str, driver: Driver | None = None
) -> dict | None:
    driver = driver or get_driver()
    a = get_entity(entity_a, driver=driver)
    b = get_entity(entity_b, driver=driver)
    if a is None or b is None:
        found = a or b
        return {"entity": found, "other_missing": a is None or b is None} if found else None

    records = _get(
        driver,
        """
        MATCH (a {id: $a_id})-[r]-(b {id: $b_id})
        RETURN r,
               startNode(r).id AS src_id,
               endNode(r).id AS dst_id,
               head(labels(a)) AS atype,
               head(labels(b)) AS btype
        """,
        a_id=entity_a,
        b_id=entity_b,
    )
    relationships = [
        _relationship(rec["r"], rec["src_id"], rec["dst_id"], rec["atype"], rec["btype"])
        for rec in records
    ]
    return {
        "entity_a": a,
        "entity_b": b,
        "relationships": relationships,
    }


def two_hop(entity_id: str, limit: int = 50, driver: Driver | None = None) -> dict | None:
    driver = driver or get_driver()
    entity = get_entity(entity_id, driver=driver)
    if entity is None:
        return None

    records = _get(
        driver,
        """
        MATCH (e {id: $entity_id})-[r1]-(n1)
        OPTIONAL MATCH (n1)-[r2]-(n2)
        WHERE n2.id <> $entity_id AND n2.id <> n1.id
        RETURN n1, r1, n2, r2,
               head(labels(n1)) AS n1_type,
               head(labels(n2)) AS n2_type,
               head(labels(e)) AS etype,
               startNode(r1).id AS s1,
               endNode(r1).id AS d1,
               startNode(r2).id AS s2,
               endNode(r2).id AS d2
        ORDER BY n1.id, n2.id
        LIMIT $limit
        """,
        entity_id=entity_id,
        limit=limit,
    )
    first_hop: dict[str, dict] = {}
    for rec in records:
        n1_id = rec["n1"]["id"]
        if n1_id not in first_hop:
            direction = "outgoing" if rec["s1"] == entity_id else "incoming"
            src_type = rec["etype"] if direction == "outgoing" else rec["n1_type"]
            dst_type = rec["n1_type"] if direction == "outgoing" else rec["etype"]
            first_hop[n1_id] = {
                "node": _entity(rec["n1"]),
                "relationship": _relationship(
                    rec["r1"], rec["s1"], rec["d1"], src_type, dst_type
                ),
                "direction": direction,
                "second_hop": [],
            }
        if rec["n2"] is not None:
            first_hop[n1_id]["second_hop"].append(
                {
                    "node": _entity(rec["n2"]),
                    "relationship": _relationship(
                        rec["r2"], rec["s2"], rec["d2"], rec["n2_type"], rec["n2_type"]
                    ),
                }
            )
    return {"entity": entity, "first_hop": list(first_hop.values())}


def relationship_evidence(
    relationship_id: str, driver: Driver | None = None
) -> dict | None:
    driver = driver or get_driver()
    records = _get(
        driver,
        """
        MATCH (a)-[r {relationship_id: $rid}]-(b)
        RETURN a, b, r,
               head(labels(a)) AS atype,
               head(labels(b)) AS btype
        """,
        rid=relationship_id,
    )
    if not records:
        return None
    rec = records[0]
    rel = _relationship(
        rec["r"], rec["a"]["id"], rec["b"]["id"], rec["atype"], rec["btype"]
    )
    return {
        "relationship": rel,
        "source_entity": _entity(rec["a"]),
        "target_entity": _entity(rec["b"]),
    }


def summary(driver: Driver | None = None) -> dict:
    driver = driver or get_driver()
    node_records = _get(
        driver,
        "MATCH (n) RETURN head(labels(n)) AS label, count(*) AS count ORDER BY label",
    )
    rel_records = _get(
        driver,
        "MATCH ()-[r]->() RETURN type(r) AS type, count(*) AS count ORDER BY type",
    )
    return {
        "nodes": {r["label"]: r["count"] for r in node_records},
        "relationships": {r["type"]: r["count"] for r in rel_records},
    }


def full_graph(limit: int = 2000, driver: Driver | None = None) -> dict:
    """Return the entire knowledge graph in GraphResponse-compatible shape.

    Each node is {id, type, attributes} and each edge is
    {source, target, type, key, attributes}.
    """
    driver = driver or get_driver()
    node_records = _get(
        driver,
        "MATCH (n) RETURN n ORDER BY elementId(n) LIMIT $limit",
        limit=limit,
    )
    rel_records = _get(
        driver,
        """
        MATCH ()-[r]->()
        RETURN r,
               startNode(r).id AS src_id,
               endNode(r).id AS dst_id
        LIMIT $limit
        """,
        limit=limit,
    )
    nodes = []
    for rec in node_records:
        entity = _entity(rec["n"])
        nodes.append(
            {
                "id": entity["id"],
                "type": entity["type"],
                "attributes": entity["properties"],
            }
        )
    edges = [
        {
            "source": rec["src_id"],
            "target": rec["dst_id"],
            "type": rec["r"].type,
            "key": rec["r"].element_id,
            "attributes": _scalar_map(dict(rec["r"])),
        }
        for rec in rel_records
    ]
    return {"nodes": nodes, "edges": edges}