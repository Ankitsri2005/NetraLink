"""Seed the Neo4j knowledge graph from the raw CSV sources.

Run from the backend directory:

    python scripts/seed_neo4j.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.neo4j import importer, schema
from app.neo4j.client import close_driver, get_driver, is_available


def main() -> int:
    if not is_available():
        print(
            "ERROR: Neo4j is not reachable. Check NEO4J_URI/NEO4J_USER/NEO4J_PASSWORD "
            "in backend/.env and start the Neo4j server."
        )
        return 1

    driver = get_driver()
    print("Installing schema (constraints + indexes)...")
    created = schema.install_schema(driver)
    print(f"  constraints: {len(created['constraints'])}")
    print(f"  indexes:     {len(created['indexes'])}")

    print("Importing knowledge graph in a single transaction (commit or rollback)...")
    summary = importer.import_all(driver)
    print("Nodes:")
    for label, count in sorted(summary["nodes"].items()):
        print(f"  {label:12s} {count}")
    print("Relationships:")
    for rel_type, count in sorted(summary["relationships"].items()):
        print(f"  {rel_type:17s} {count}")

    close_driver()
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())