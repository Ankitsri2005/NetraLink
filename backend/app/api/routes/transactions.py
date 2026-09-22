from fastapi import APIRouter, Query

from ...schemas.models import Transaction
from ...services import transaction_service

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=list[Transaction])
def list_transactions(
    sender: str | None = None,
    limit: int = Query(200, ge=1, le=2000),
    offset: int = Query(0, ge=0),
):
    return transaction_service.list_transactions(sender=sender, limit=limit, offset=offset)