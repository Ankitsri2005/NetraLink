from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db.models import Alert as AlertRow
from ..db.models import Case as CaseRow
from ..db.models import CaseNote as CaseNoteRow
from ..db.models import Evidence as EvidenceRow
from ..schemas.models import CaseCreate, CaseNoteCreate, CaseUpdate


def list_cases(db: Session) -> list[dict]:
    evidence_counts = (
        db.query(EvidenceRow.case_id, func.count().label("n"))
        .group_by(EvidenceRow.case_id)
        .subquery()
    )
    alert_counts = (
        db.query(AlertRow.case_id, func.count().label("n"))
        .group_by(AlertRow.case_id)
        .subquery()
    )
    note_counts = (
        db.query(CaseNoteRow.case_id, func.count().label("n"))
        .group_by(CaseNoteRow.case_id)
        .subquery()
    )

    rows = (
        db.query(
            CaseRow,
            func.coalesce(evidence_counts.c.n, 0).label("evidence_count"),
            func.coalesce(alert_counts.c.n, 0).label("alert_count"),
            func.coalesce(note_counts.c.n, 0).label("note_count"),
        )
        .outerjoin(evidence_counts, evidence_counts.c.case_id == CaseRow.id)
        .outerjoin(alert_counts, alert_counts.c.case_id == CaseRow.id)
        .outerjoin(note_counts, note_counts.c.case_id == CaseRow.id)
        .order_by(CaseRow.id.desc())
        .all()
    )
    return [
        _to_dict(
            row,
            evidence_count=int(evidence_count),
            alert_count=int(alert_count),
            note_count=int(note_count),
        )
        for row, evidence_count, alert_count, note_count in rows
    ]


def get_case(db: Session, case_id: int) -> dict | None:
    row = db.get(CaseRow, case_id)
    if row is None:
        return None

    evidence = [
        {
            "id": e.id,
            "source_type": e.source_type,
            "source_record_id": e.source_record_id,
            "file_name": e.file_name,
            "content_hash": e.content_hash,
            "previous_hash": e.previous_hash,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in row.evidence
    ]

    notes = [
        {
            "id": n.id,
            "case_id": n.case_id,
            "author": n.author,
            "body": n.body,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in sorted(row.notes, key=lambda n: n.id, reverse=True)
    ]

    return {
        **_to_dict(row),
        "evidence_count": len(evidence),
        "alert_count": len(row.alerts),
        "note_count": len(notes),
        "evidence": evidence,
        "notes": notes,
    }


def create_case(db: Session, payload: CaseCreate) -> dict:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    count_today = (
        db.query(CaseRow)
        .filter(CaseRow.created_at >= today_start)
        .count()
    )
    case_number = f"CASE-{now.strftime('%Y%m%d')}-{count_today + 1:04d}"

    case = CaseRow(
        case_number=case_number,
        title=payload.title,
        description=payload.description,
        status="open",
        created_by=payload.created_by,
        created_at=now,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return _to_dict(case)


def update_case(db: Session, case_id: int, payload: CaseUpdate) -> dict | None:
    row = db.get(CaseRow, case_id)
    if row is None:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return _to_dict(row)


def add_note(db: Session, case_id: int, payload: CaseNoteCreate) -> dict | None:
    row = db.get(CaseRow, case_id)
    if row is None:
        return None
    note = CaseNoteRow(case_id=case_id, author=payload.author, body=payload.body)
    db.add(note)
    db.commit()
    db.refresh(note)
    return {
        "id": note.id,
        "case_id": note.case_id,
        "author": note.author,
        "body": note.body,
        "created_at": note.created_at.isoformat() if note.created_at else None,
    }


def _to_dict(
    row: CaseRow,
    evidence_count: int = 0,
    alert_count: int = 0,
    note_count: int = 0,
) -> dict:
    return {
        "id": row.id,
        "case_number": row.case_number,
        "title": row.title,
        "description": row.description,
        "status": row.status,
        "created_by": row.created_by,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "evidence_count": evidence_count,
        "alert_count": alert_count,
        "note_count": note_count,
    }