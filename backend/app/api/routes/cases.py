from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...schemas.models import Case, CaseCreate, CaseDetail, CaseNote, CaseNoteCreate, CaseUpdate, EvidenceUploadResponse
from ...services import case_service, evidence_service

router = APIRouter(prefix="/cases", tags=["cases"])

CASE_STATUSES = {"open", "in_progress", "closed"}


@router.get("", response_model=list[Case])
def list_cases(db: Session = Depends(get_db)):
    return case_service.list_cases(db)


@router.post("", response_model=Case, status_code=201)
def create_case(payload: CaseCreate, db: Session = Depends(get_db)):
    return case_service.create_case(db, payload)


@router.get("/{case_id}", response_model=CaseDetail)
def get_case(case_id: int, db: Session = Depends(get_db)):
    row = case_service.get_case(db, case_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return row


@router.patch("/{case_id}", response_model=Case)
def update_case(case_id: int, payload: CaseUpdate, db: Session = Depends(get_db)):
    if payload.status is not None and payload.status not in CASE_STATUSES:
        raise HTTPException(status_code=422, detail=f"Invalid status. Allowed: {sorted(CASE_STATUSES)}")
    row = case_service.update_case(db, case_id, payload)
    if row is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return row


@router.post("/{case_id}/notes", response_model=CaseNote, status_code=201)
def add_note(case_id: int, payload: CaseNoteCreate, db: Session = Depends(get_db)):
    if not payload.body.strip():
        raise HTTPException(status_code=422, detail="Note body cannot be empty")
    note = case_service.add_note(db, case_id, payload)
    if note is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return note


@router.post("/{case_id}/evidence", response_model=EvidenceUploadResponse, status_code=201)
def upload_evidence(
    case_id: int,
    source_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        result = evidence_service.ingest_evidence(db, case_id, source_type, file)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return result