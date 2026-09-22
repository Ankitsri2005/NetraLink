from __future__ import annotations

from collections import Counter

from ..aiml import loader
from ..schemas.models import AlertSummary


def list_alerts(
    priority: str | None = None, limit: int = 50, offset: int = 0
) -> list[dict]:
    rows = loader.alerts()
    if priority:
        rows = [
            r for r in rows if (r.get("priority") or "").lower() == priority.lower()
        ]
    rows.sort(key=lambda r: r.get("anomaly_score") if r.get("anomaly_score") is not None else 0.0)
    return rows[offset : offset + limit]


def get_alert(person_id: str) -> dict | None:
    return next((r for r in loader.alerts() if r.get("person_id") == person_id), None)


def summary() -> AlertSummary:
    rows = loader.alerts()
    priorities = Counter((r.get("priority") or "Unknown") for r in rows)
    anomalies = Counter(
        str(r.get("anomaly")) if r.get("anomaly") is not None else "Unknown"
        for r in rows
    )
    return AlertSummary(
        total=len(rows),
        by_priority=dict(priorities),
        by_anomaly=dict(anomalies),
    )