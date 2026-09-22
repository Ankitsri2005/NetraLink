from __future__ import annotations

from neo4j import Driver

from .client import NEO4J_DATABASE, get_session

NODE_LABELS = (
    "Person",
    "Phone",
    "Account",
    "Vehicle",
    "Location",
    "Fir",
    "Incident",
)

RELATIONSHIP_TYPES = (
    "OWNS",
    "CALLED",
    "TRANSFERRED_TO",
    "MENTIONED_IN",
    "REPORTED_AT",
    "SEEN_AT",
    "ASSOCIATED_WITH",
)

UNIQUE_CONSTRAINTS = (
    ("person_id_unique", "Person", "id"),
    ("phone_id_unique", "Phone", "id"),
    ("account_id_unique", "Account", "id"),
    ("vehicle_id_unique", "Vehicle", "id"),
    ("location_id_unique", "Location", "id"),
    ("fir_id_unique", "Fir", "id"),
    ("incident_id_unique", "Incident", "id"),
)

LOOKUP_INDEXES = (
    ("person_name_index", "Person", "name"),
    ("person_city_index", "Person", "city"),
    ("phone_number_index", "Phone", "phone_number"),
    ("account_number_index", "Account", "account_number"),
    ("account_bank_index", "Account", "bank"),
    ("vehicle_registration_index", "Vehicle", "registration_number"),
    ("location_name_index", "Location", "location_name"),
    ("fir_report_id_index", "Fir", "report_id"),
)


RELATIONSHIP_INDEXES = tuple(
    (f"{reltype.lower()}_relationship_id_index", reltype)
    for reltype in RELATIONSHIP_TYPES
)


def install_schema(driver: Driver) -> dict:
    with get_session() as session:
        return session.execute_write(_apply_schema)


def _apply_schema(tx):
    created = {"constraints": [], "indexes": []}
    for name, label, prop in UNIQUE_CONSTRAINTS:
        tx.run(
            f"CREATE CONSTRAINT {name} IF NOT EXISTS "
            f"FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE"
        )
        created["constraints"].append(name)
    for name, label, prop in LOOKUP_INDEXES:
        tx.run(
            f"CREATE INDEX {name} IF NOT EXISTS "
            f"FOR (n:{label}) ON (n.{prop})"
        )
        created["indexes"].append(name)
    for name, reltype in RELATIONSHIP_INDEXES:
        tx.run(
            f"CREATE INDEX {name} IF NOT EXISTS "
            f"FOR ()-[r:{reltype}]-() ON (r.relationship_id)"
        )
        created["indexes"].append(name)
    return created