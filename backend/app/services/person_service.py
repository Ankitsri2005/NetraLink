from __future__ import annotations

from ..aiml import loader
from ..schemas.models import AccountRef, PhoneRef


def list_persons(limit: int = 200, offset: int = 0) -> list[dict]:
    return loader.persons()[offset : offset + limit]


def get_person(person_id: str) -> dict | None:
    row = next((r for r in loader.persons() if r.get("person_id") == person_id), None)
    if row is None:
        return None

    demographic = next(
        (r for r in loader.raw_persons() if r.get("person_id") == person_id), {}
    )

    phones = [
        PhoneRef(phone_id=r.get("phone_id"), phone_number=r.get("phone_number"))
        for r in loader.phones()
        if r.get("person_id") == person_id
    ]

    accounts = [
        AccountRef(
            account_id=r.get("account_id"),
            account_number=r.get("account_number"),
            bank=r.get("bank"),
        )
        for r in loader.accounts()
        if r.get("owner_person_id") == person_id
    ]

    return {
        **row,
        "age": demographic.get("age"),
        "city": demographic.get("city"),
        "persons_phones": phones,
        "accounts": accounts,
    }