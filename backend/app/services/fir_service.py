from __future__ import annotations

from ..aiml import loader


def list_fir_entities() -> list[dict]:
    return loader.fir_entities()


def list_fir_reports() -> list[dict]:
    return loader.fir_reports()