from __future__ import annotations

import re
from collections import Counter, defaultdict

from neo4j import Driver, Transaction

from ..aiml import loader
from .client import get_driver, get_session


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _rid(*parts) -> str:
    cleaned = [str(p) for p in parts if p]
    return "R-" + "-".join(cleaned)


def _flat(props: dict) -> dict:
    return {k: v for k, v in props.items() if v is not None}


def _amount(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def needs_import(driver: Driver | None = None) -> bool:
    driver = driver or get_driver()
    with get_session() as session:
        result = list(session.run("MATCH (n:Person) RETURN count(n) AS c"))
        return (result[0]["c"] if result else 0) == 0


def import_all(driver: Driver | None = None) -> dict:
    driver = driver or get_driver()
    with get_session() as session:
        return session.execute_write(_import_work)


def _merge_node(tx: Transaction, label: str, entity_id: str, props: dict) -> None:
    tx.run(
        "MERGE (n:" + label + " {id: $id}) SET n += $props",
        id=entity_id,
        props=props,
    )


def _rel_between(
    tx: Transaction,
    from_label: str,
    from_id: str,
    to_label: str,
    to_id: str,
    rel_type: str,
    rid: str,
    evidence: dict,
) -> None:
    query = (
        "MATCH (a:" + from_label + " {id: $from_id}), (b:" + to_label + " {id: $to_id}) "
        "MERGE (a)-[r:" + rel_type + " {relationship_id: $rid}]->(b) "
        "SET r += $evidence"
    )
    tx.run(
        query,
        from_id=from_id,
        to_id=to_id,
        rid=rid,
        evidence={**evidence, "relationship_type": rel_type},
    )


def _import_work(tx: Transaction) -> dict:
    nodes = Counter()
    rels = Counter()

    raw_persons = loader.raw_persons()
    persons_anomaly = {r["person_id"]: r for r in loader.persons()}
    phones = loader.phones()
    accounts = loader.accounts()
    vehicles = loader.vehicles()
    known_locations = loader.locations()
    fir_reports = loader.fir_reports()
    fir_entities = loader.fir_entities()
    transactions = loader.transactions()
    cdr = loader.cdr()

    account_by_number = {r["account_number"]: r["account_id"] for r in accounts}
    phone_by_id = {r["phone_id"]: r for r in phones}
    vehicle_by_registration = {r["registration_number"]: r for r in vehicles}
    location_name_to_id = {r["location_name"]: r["location_id"] for r in known_locations}
    fir_by_id = {r["report_id"]: r for r in fir_reports}

    derived_locations: dict[str, dict] = {}

    def resolve_location(name: str | None) -> str | None:
        if not name:
            return None
        known = location_name_to_id.get(name)
        if known:
            return known
        lid = "LOC-" + _slug(name)
        if lid not in derived_locations:
            derived_locations[lid] = {
                "location_name": name,
                "city": name,
                "derived": True,
            }
        return lid

    for row in transactions:
        resolve_location(str(row.get("location") or ""))
    for row in known_locations:
        location_name_to_id[str(row["location_name"])] = row["location_id"]

    fir_mentions: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for ent in fir_entities:
        report = ent.get("report_id")
        etype = (ent.get("type") or "").upper()
        matched = ent.get("matched_id")
        if not matched or matched == "Not Found":
            continue
        fir_mentions[report][etype].append(str(matched))

    for row in raw_persons:
        pid = row["person_id"]
        props = _flat(
            {
                "name": row.get("name"),
                "age": _int(row.get("age")),
                "city": row.get("city"),
            }
        )
        anomaly = persons_anomaly.get(pid, {})
        for key in (
            "total_calls",
            "unique_contacts",
            "money_sent",
            "money_received",
            "total_transactions",
            "money_difference",
            "anomaly_score",
            "degree_centrality",
            "betweenness_centrality",
        ):
            if anomaly.get(key) is not None:
                props[key] = _amount(anomaly[key])
        props["anomaly"] = _int(anomaly.get("anomaly"))
        props["priority"] = anomaly.get("priority")
        _merge_node(tx, "Person", pid, props)
        nodes["Person"] += 1

    for row in phones:
        _merge_node(
            tx,
            "Phone",
            row["phone_id"],
            _flat(
                {
                    "phone_number": row.get("phone_number"),
                    "person_id": row.get("person_id"),
                }
            ),
        )
        nodes["Phone"] += 1

    for row in accounts:
        _merge_node(
            tx,
            "Account",
            row["account_id"],
            _flat(
                {
                    "account_number": row.get("account_number"),
                    "owner_person_id": row.get("owner_person_id"),
                    "bank": row.get("bank"),
                }
            ),
        )
        nodes["Account"] += 1

    for row in vehicles:
        _merge_node(
            tx,
            "Vehicle",
            row["vehicle_id"],
            _flat(
                {
                    "registration_number": row.get("registration_number"),
                    "vehicle_type": row.get("vehicle_type"),
                    "person_id": row.get("person_id"),
                }
            ),
        )
        nodes["Vehicle"] += 1

    for row in known_locations:
        _merge_node(
            tx,
            "Location",
            row["location_id"],
            _flat({"location_name": row.get("location_name"), "city": row.get("city")}),
        )
        nodes["Location"] += 1
    for lid, props in derived_locations.items():
        _merge_node(tx, "Location", lid, props)
        nodes["Location"] += 1

    for row in fir_reports:
        _merge_node(
            tx,
            "Fir",
            row["report_id"],
            _flat(
                {
                    "report_id": row.get("report_id"),
                    "date": row.get("date"),
                    "report_type": row.get("report_type"),
                    "text": row.get("text"),
                }
            ),
        )
        nodes["Fir"] += 1
        incident_id = "INC-" + row["report_id"]
        incident_loc = None
        mention_ids = fir_mentions.get(row["report_id"], {})
        if mention_ids.get("LOCATION"):
            loc_id = mention_ids["LOCATION"][0]
            incident_loc = next(
                (r["location_name"] for r in known_locations if r["location_id"] == loc_id),
                None,
            )
        _merge_node(
            tx,
            "Incident",
            incident_id,
            _flat(
                {
                    "report_id": row.get("report_id"),
                    "date": row.get("date"),
                    "report_type": row.get("report_type"),
                    "location": incident_loc,
                }
            ),
        )
        nodes["Incident"] += 1

    for row in phones:
        pid = row.get("person_id")
        if not pid:
            continue
        _rel_between(
            tx,
            "Person",
            pid,
            "Phone",
            row["phone_id"],
            "OWNS",
            _rid("OWNS", pid, row["phone_id"]),
            {"source_record_id": row["phone_id"], "confidence": 1.0},
        )
        rels["OWNS"] += 1

    for row in accounts:
        pid = row.get("owner_person_id")
        if not pid:
            continue
        _rel_between(
            tx,
            "Person",
            pid,
            "Account",
            row["account_id"],
            "OWNS",
            _rid("OWNS", pid, row["account_id"]),
            {"source_record_id": row["account_id"], "confidence": 1.0},
        )
        rels["OWNS"] += 1

    for row in vehicles:
        pid = row.get("person_id")
        if not pid:
            continue
        _rel_between(
            tx,
            "Person",
            pid,
            "Vehicle",
            row["vehicle_id"],
            "OWNS",
            _rid("OWNS", pid, row["vehicle_id"]),
            {"source_record_id": row["vehicle_id"], "confidence": 1.0},
        )
        rels["OWNS"] += 1

    for row in cdr:
        caller, receiver = row.get("caller_phone"), row.get("receiver_phone")
        if not caller or not receiver:
            continue
        if caller not in phone_by_id or receiver not in phone_by_id:
            continue
        _rel_between(
            tx,
            "Phone",
            caller,
            "Phone",
            receiver,
            "CALLED",
            _rid("CALLED", row.get("call_id")),
            _flat(
                {
                    "source_record_id": row.get("call_id"),
                    "timestamp": row.get("date_time"),
                    "duration": _amount(row.get("duration")),
                    "location": row.get("tower_location"),
                    "confidence": 1.0,
                }
            ),
        )
        rels["CALLED"] += 1

    for row in transactions:
        sender = account_by_number.get(row.get("sender_account"))
        receiver = account_by_number.get(row.get("receiver_account"))
        if not sender or not receiver or sender == receiver:
            continue
        _rel_between(
            tx,
            "Account",
            sender,
            "Account",
            receiver,
            "TRANSFERRED_TO",
            _rid("TRANSFERRED_TO", row.get("transaction_id")),
            _flat(
                {
                    "source_record_id": row.get("transaction_id"),
                    "timestamp": row.get("timestamp"),
                    "amount": _amount(row.get("amount")),
                    "location": row.get("location"),
                    "confidence": 1.0,
                }
            ),
        )
        rels["TRANSFERRED_TO"] += 1

    for row in cdr:
        caller = row.get("caller_phone")
        lid = resolve_location(str(row.get("tower_location") or ""))
        if caller not in phone_by_id or not lid:
            continue
        _rel_between(
            tx,
            "Phone",
            caller,
            "Location",
            lid,
            "SEEN_AT",
            _rid("SEEN_AT", row.get("call_id")),
            _flat(
                {
                    "source_record_id": row.get("call_id"),
                    "timestamp": row.get("date_time"),
                    "duration": _amount(row.get("duration")),
                    "location": row.get("tower_location"),
                    "confidence": 0.9,
                }
            ),
        )
        rels["SEEN_AT"] += 1

    for row in transactions:
        sender = account_by_number.get(row.get("sender_account"))
        lid = resolve_location(str(row.get("location") or ""))
        if not sender or not lid:
            continue
        _rel_between(
            tx,
            "Account",
            sender,
            "Location",
            lid,
            "SEEN_AT",
            _rid("SEEN_AT", row.get("transaction_id")),
            _flat(
                {
                    "source_record_id": row.get("transaction_id"),
                    "timestamp": row.get("timestamp"),
                    "amount": _amount(row.get("amount")),
                    "location": row.get("location"),
                    "confidence": 0.9,
                }
            ),
        )
        rels["SEEN_AT"] += 1

    for report_id, mentions in fir_mentions.items():
        loc_ids = mentions.get("LOCATION", [])
        person_ids = mentions.get("PERSON", [])
        fir = fir_by_id.get(report_id)
        for pid in person_ids:
            for lid in loc_ids:
                _rel_between(
                    tx,
                    "Person",
                    pid,
                    "Location",
                    lid,
                    "SEEN_AT",
                    _rid("SEEN_AT", report_id, pid, lid),
                    _flat(
                        {
                            "source_record_id": report_id,
                            "timestamp": fir.get("date") if fir else None,
                            "location": next(
                                (
                                    r["location_name"]
                                    for r in known_locations
                                    if r["location_id"] == lid
                                ),
                                None,
                            ),
                            "confidence": 0.7,
                        }
                    ),
                )
                rels["SEEN_AT"] += 1

    entity_label_by_type = {
        "PERSON": "Person",
        "PHONE": "Phone",
        "ACCOUNT": "Account",
        "LOCATION": "Location",
        "VEHICLE": "Vehicle",
    }
    for ent in fir_entities:
        report = ent.get("report_id")
        etype = (ent.get("type") or "").upper()
        label = entity_label_by_type.get(etype)
        matched = ent.get("matched_id")
        if not label or not matched or matched == "Not Found":
            continue
        entity_id = matched
        fir = fir_by_id.get(report)
        _rel_between(
            tx,
            label,
            entity_id,
            "Fir",
            report,
            "MENTIONED_IN",
            _rid("MENTIONED_IN", report, etype, entity_id),
            _flat(
                {
                    "source_record_id": report,
                    "timestamp": fir.get("date") if fir else None,
                    "mention": ent.get("entity"),
                    "confidence": 1.0,
                }
            ),
        )
        rels["MENTIONED_IN"] += 1

    for row in fir_reports:
        _rel_between(
            tx,
            "Fir",
            row["report_id"],
            "Incident",
            "INC-" + row["report_id"],
            "REPORTED_AT",
            _rid("REPORTED_AT", row["report_id"]),
            _flat(
                {
                    "source_record_id": row["report_id"],
                    "timestamp": row.get("date"),
                    "report_type": row.get("report_type"),
                    "confidence": 1.0,
                }
            ),
        )
        rels["REPORTED_AT"] += 1

    owner_of_phone: dict[str, str] = {}
    for row in phones:
        if row.get("person_id"):
            owner_of_phone[row["phone_id"]] = row["person_id"]

    associated: dict[str, tuple[str, str, dict]] = {}
    for row in cdr:
        caller, receiver = row.get("caller_phone"), row.get("receiver_phone")
        p_caller = owner_of_phone.get(caller)
        p_receiver = owner_of_phone.get(receiver)
        if not p_caller or not p_receiver or p_caller == p_receiver:
            continue
        a, b = sorted((p_caller, p_receiver))
        rid = _rid("ASSOCIATED_WITH", row.get("call_id"))
        associated[rid] = (
            a,
            b,
            _flat(
                {
                    "source_record_id": row.get("call_id"),
                    "timestamp": row.get("date_time"),
                    "duration": _amount(row.get("duration")),
                    "confidence": 0.9,
                }
            ),
        )

    for report_id, mentions in fir_mentions.items():
        persons_in_report = mentions.get("PERSON", [])
        fir = fir_by_id.get(report_id)
        seen = set()
        for p1 in persons_in_report:
            for p2 in persons_in_report:
                if p1 == p2:
                    continue
                a, b = sorted((p1, p2))
                if (a, b) in seen:
                    continue
                seen.add((a, b))
                rid = _rid("ASSOCIATED_WITH", report_id, a, b)
                associated[rid] = (
                    a,
                    b,
                    _flat(
                        {
                            "source_record_id": report_id,
                            "timestamp": fir.get("date") if fir else None,
                            "confidence": 0.75,
                        }
                    ),
                )

    for rid, (a, b, evidence) in associated.items():
        _rel_between(tx, "Person", a, "Person", b, "ASSOCIATED_WITH", rid, evidence)
        rels["ASSOCIATED_WITH"] += 1

    return {
        "nodes": dict(nodes),
        "relationships": dict(rels),
    }