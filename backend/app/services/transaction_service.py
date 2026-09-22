from __future__ import annotations

from ..aiml import loader


def list_transactions(sender: str | None = None, limit: int = 200, offset: int = 0) -> list[dict]:
    rows = loader.transactions()
    if sender:
        rows = [r for r in rows if r.get("sender_account") == sender]
    return rows[offset : offset + limit]