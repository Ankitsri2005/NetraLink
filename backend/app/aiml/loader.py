from __future__ import annotations

import pickle
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[3]
OUTPUTS_DIR = BASE_DIR / "aiml" / "outputs"
RAW_DIR = BASE_DIR / "data" / "raw"

ALERTS_CSV = OUTPUTS_DIR / "investigation_alerts.csv"
PERSONS_CSV = OUTPUTS_DIR / "anomaly_results.csv"
FIR_ENTITIES_CSV = OUTPUTS_DIR / "fir_entities_final.csv"
GRAPH_PKL = OUTPUTS_DIR / "netralink_final_graph.pkl"

def _find_raw(sub: str, name: str) -> Path:
    p = RAW_DIR / sub / name
    return p if p.exists() else (RAW_DIR / name)


RAW_PERSONS_CSV = _find_raw("persons", "persons.csv")
RAW_PHONES_CSV = _find_raw("phones", "phones.csv")
RAW_ACCOUNTS_CSV = _find_raw("accounts", "accounts.csv")
RAW_VEHICLES_CSV = _find_raw("vehicles", "vehicles.csv")
RAW_LOCATIONS_CSV = _find_raw("locations", "locations.csv")
RAW_FIR_CSV = _find_raw("fir", "fir_reports.csv")
RAW_TRANSACTIONS_CSV = _find_raw("transactions", "transactions.csv")
RAW_CDR_CSV = _find_raw("cdr", "cdr.csv")


def _native(value):
    if isinstance(value, np.generic):
        return value.item()
    if pd.isna(value):
        return None
    return value


def _records(path: Path) -> list[dict]:
    df = pd.read_csv(path)
    return [{k: _native(v) for k, v in row.items()} for row in df.to_dict(orient="records")]


@lru_cache(maxsize=1)
def alerts() -> list[dict]:
    return _records(ALERTS_CSV)


@lru_cache(maxsize=1)
def persons() -> list[dict]:
    return _records(PERSONS_CSV)


@lru_cache(maxsize=1)
def fir_entities() -> list[dict]:
    return _records(FIR_ENTITIES_CSV)


@lru_cache(maxsize=1)
def fir_reports() -> list[dict]:
    return _records(RAW_FIR_CSV)


@lru_cache(maxsize=1)
def transactions() -> list[dict]:
    return _records(RAW_TRANSACTIONS_CSV)


@lru_cache(maxsize=1)
def raw_persons() -> list[dict]:
    return _records(RAW_PERSONS_CSV)


@lru_cache(maxsize=1)
def phones() -> list[dict]:
    rows = _records(RAW_PHONES_CSV)
    for row in rows:
        if row.get("phone_number") is not None:
            row["phone_number"] = str(int(row["phone_number"]))
    return rows


@lru_cache(maxsize=1)
def accounts() -> list[dict]:
    return _records(RAW_ACCOUNTS_CSV)


@lru_cache(maxsize=1)
def vehicles() -> list[dict]:
    return _records(RAW_VEHICLES_CSV)


@lru_cache(maxsize=1)
def locations() -> list[dict]:
    return _records(RAW_LOCATIONS_CSV)


@lru_cache(maxsize=1)
def cdr() -> list[dict]:
    return _records(RAW_CDR_CSV)


@lru_cache(maxsize=1)
def graph() -> dict:
    import networkx as nx

    with open(GRAPH_PKL, "rb") as handle:
        g = pickle.load(handle)

    nodes = [
        {
            "id": str(node_id),
            "type": data.get("type") or "Entity",
            "attributes": {k: _native(v) for k, v in data.items() if k != "type"},
        }
        for node_id, data in g.nodes(data=True)
    ]

    edges = []
    for u, v, key, data in g.edges(data=True, keys=True):
        rel = data.get("relationship") or data.get("type") or "RELATED"
        edges.append(
            {
                "source": str(u),
                
                "target": str(v),
                "type": rel,
                "key": int(key) if isinstance(key, (int, np.integer)) else str(key),
                "attributes": {
                    k: _native(val) for k, val in data.items() if k not in ("relationship", "type")
                },
            }
        )

    return {"nodes": nodes, "edges": edges}
