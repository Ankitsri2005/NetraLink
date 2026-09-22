from __future__ import annotations

import io
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from ..db.models import Case as CaseRow
from ..db.models import Evidence as EvidenceRow
from ..evidence.hashing import sha256_digest
from ..neo4j import client as neo4j_client
from ..neo4j import evidence_ingest

UPLOAD_ROOT = Path(__file__).resolve().parents[2] / "evidence_uploads"

REQUIRED_CDR_COLUMNS = {
    "call_id",
    "caller_phone",
    "receiver_phone",
    "date_time",
    "duration",
    "tower_location",
}

SUPPORTED_TYPES = {"cdr": REQUIRED_CDR_COLUMNS}


def _safe_name(name: str) -> str:
    base = Path(name).name
    return re.sub(r"[^A-Za-z0-9._-]+", "_", base) or "evidence.csv"


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _record_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def ingest_evidence(db: Session, case_id: int, source_type: str, file) -> dict | None:
    """Process an uploaded evidence file for a case.

    Persists the raw file (SHA-256 chained into the case evidence ledger),
    extracts entities/relationships, and ingests them into the Neo4j graph.
    """
    case = db.get(CaseRow, case_id)
    if case is None:
        return None

    source_type = (source_type or "").strip().lower()
    if source_type not in SUPPORTED_TYPES:
        raise ValueError(
            f"Unsupported evidence type '{source_type}'. Supported: {sorted(SUPPORTED_TYPES)}"
        )

    content = file.file.read()
    content_hash = sha256_digest(content)
    source_record_id = f"FILE-{content_hash[:8]}"

    existing = (
        db.query(EvidenceRow)
        .filter(
            EvidenceRow.case_id == case_id,
            EvidenceRow.source_type == source_type.upper(),
            EvidenceRow.source_record_id == source_record_id,
        )
        .first()
    )
    if existing is not None:
        return _as_dict(existing, duplicate=True)

    text = content.decode("utf-8-sig", errors="replace")

    rows = _parse_csv(text, source_type)

    fragment = _build_fragment(rows, source_type)

    ingest_summary: dict = {"nodes": {}, "relationships": {}}
    if source_type == "cdr":
        ingest_summary, _ = evidence_ingest.ingest_cdr_guarded([dict(r) for r in rows])
        neo4j_ok = _neo4j_health()

    case_dir = UPLOAD_ROOT / str(case_id)
    case_dir.mkdir(parents=True, exist_ok=True)
    local_name = f"{_record_ts()}_{_safe_name(file.filename or 'evidence.csv')}"
    saved_path = case_dir / local_name
    saved_path.write_bytes(content)

    previous_hash = _last_evidence_hash(db, case_id)

    record = EvidenceRow(
        case_id=case_id,
        source_type=source_type.upper(),
        source_record_id=source_record_id,
        file_name=file.filename,
        file_path=str(saved_path),
        content_hash=content_hash,
        previous_hash=previous_hash,
        ingested_nodes=fragment["nodes"] or None,
        ingested_edges=fragment["edges"] or None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return _as_dict(record, summary=ingest_summary, neo4j=neo4j_ok)


def _as_dict(
    record: EvidenceRow,
    summary: dict | None = None,
    neo4j: bool = False,
    duplicate: bool = False,
) -> dict:
    return {
        "id": record.id,
        "case_id": record.case_id,
        "source_type": record.source_type,
        "source_record_id": record.source_record_id,
        "file_name": record.file_name,
        "content_hash": record.content_hash,
        "previous_hash": record.previous_hash,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "summary": summary or _summary_from_fragment(record.ingested_nodes, record.ingested_edges),
        "neo4j": neo4j,
        "duplicate": duplicate,
    }


def _summary_from_fragment(nodes: list | None, edges: list | None) -> dict:
    node_counts: dict[str, int] = {}
    for node in nodes or []:
        node_counts[node.get("type", "Unknown")] = node_counts.get(node.get("type", "Unknown"), 0) + 1
    edge_counts: dict[str, int] = {}
    for edge in edges or []:
        edge_counts[edge.get("type", "Unknown")] = edge_counts.get(edge.get("type", "Unknown"), 0) + 1
    return {"nodes": node_counts, "relationships": edge_counts}


def _neo4j_health() -> bool:
    try:
        return bool(neo4j_client.is_available())
    except Exception:
        return False


def _parse_csv(text: str, source_type: str) -> list[dict]:
    try:
        df = pd.read_csv(io.StringIO(text))
    except Exception as exc:
        raise ValueError(f"Could not parse CSV: {exc}") from exc

    required = SUPPORTED_TYPES[source_type]
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"File missing required columns: {', '.join(sorted(missing))}. "
            f"Expected: {', '.join(sorted(required))}"
        )

    return [dict(row) for row in df.to_dict(orient="records")]


def _build_fragment(rows: list[dict], source_type: str) -> dict:
    if source_type != "cdr":
        return {"nodes": [], "edges": []}

    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    def phone_props(phone_id):
        return {"name": phone_id if isinstance(phone_id, str) else str(phone_id)}

    def location_props(lid, name):
        return {"name": name}

    for row in rows:
        caller, receiver = row.get("caller_phone"), row.get("receiver_phone")
        if not caller or not receiver:
            continue
        caller, receiver = str(caller), str(receiver)
        loc_name = str(row.get("tower_location") or "").strip()

        if caller not in nodes:
            nodes[caller] = {"id": caller, "type": "Phone", "attributes": phone_props(caller)}
        if receiver not in nodes:
            nodes[receiver] = {"id": receiver, "type": "Phone", "attributes": phone_props(receiver)}

        if caller != receiver:
            edges.append(
                {
                    "source": caller,
                    "target": receiver,
                    "type": "CALLED",
                    "key": str(row.get("call_id")),
                    "attributes": {
                        "source_record_id": row.get("call_id"),
                        "timestamp": row.get("date_time"),
                        "duration": _num(row.get("duration")),
                        "location": loc_name or None,
                    },
                }
            )

        if loc_name:
            lid = "LOC-" + re.sub(r"[^a-z0-9]+", "-", loc_name.lower()).strip("-")
            if lid not in nodes:
                nodes[lid] = {"id": lid, "type": "Location", "attributes": location_props(lid, loc_name)}
            edges.append(
                {
                    "source": caller,
                    "target": lid,
                    "type": "SEEN_AT",
                    "key": str(row.get("call_id")),
                    "attributes": {
                        "source_record_id": row.get("call_id"),
                        "timestamp": row.get("date_time"),
                        "duration": _num(row.get("duration")),
                        "location": loc_name or None,
                    },
                }
            )

    return {"nodes": list(nodes.values()), "edges": edges}


def _last_evidence_hash(db: Session, case_id: int) -> str | None:
    row = (
        db.query(EvidenceRow)
        .filter(EvidenceRow.case_id == case_id)
        .order_by(EvidenceRow.id.desc())
        .first()
    )
    return row.content_hash if row else None