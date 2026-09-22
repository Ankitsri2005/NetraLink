from fastapi import APIRouter

from ...schemas.models import FirEntity, FirReport
from ...services import fir_service

router = APIRouter(prefix="/fir", tags=["fir"])


@router.get("/entities", response_model=list[FirEntity])
def list_fir_entities():
    return fir_service.list_fir_entities()


@router.get("/reports", response_model=list[FirReport])
def list_fir_reports():
    return fir_service.list_fir_reports()