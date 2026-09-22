from fastapi import APIRouter, HTTPException, Query

from ...schemas.models import Alert, AlertSummary
from ...services import alert_service

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[Alert])
def list_alerts(
    priority: str | None = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    return alert_service.list_alerts(priority=priority, limit=limit, offset=offset)


@router.get("/summary", response_model=AlertSummary)
def alert_summary():
    return alert_service.summary()


@router.get("/{person_id}", response_model=Alert)
def get_alert(person_id: str):
    row = alert_service.get_alert(person_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return row