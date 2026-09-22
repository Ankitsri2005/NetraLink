from fastapi import APIRouter, HTTPException, Query

from ...schemas.models import Person, PersonDetail
from ...services import person_service

router = APIRouter(prefix="/persons", tags=["persons"])


@router.get("", response_model=list[Person])
def list_persons(
    limit: int = Query(200, ge=1, le=600),
    offset: int = Query(0, ge=0),
):
    return person_service.list_persons(limit=limit, offset=offset)


@router.get("/{person_id}", response_model=PersonDetail)
def get_person(person_id: str):
    detail = person_service.get_person(person_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Person not found")
    return detail