from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Alert(BaseModel):
    person_id: str
    name: str | None = None
    total_calls: float | None = None
    unique_contacts: float | None = None
    money_sent: float | None = None
    money_received: float | None = None
    total_transactions: float | None = None
    money_difference: float | None = None
    anomaly: int | None = None
    anomaly_score: float | None = None
    priority: str | None = None
    degree_centrality: float | None = None
    betweenness_centrality: float | None = None
    alert_reason: str | None = None


class Person(BaseModel):
    person_id: str
    name: str | None = None
    age: int | None = None
    city: str | None = None
    total_calls: float | None = None
    unique_contacts: float | None = None
    money_sent: float | None = None
    money_received: float | None = None
    total_transactions: float | None = None
    money_difference: float | None = None
    anomaly: int | None = None
    anomaly_score: float | None = None
    priority: str | None = None
    degree_centrality: float | None = None
    betweenness_centrality: float | None = None


class AccountRef(BaseModel):
    account_id: str
    account_number: str | None = None
    bank: str | None = None


class PhoneRef(BaseModel):
    phone_id: str | None = None
    phone_number: str | None = None


class PersonDetail(Person):
    persons_phones: list[PhoneRef] = Field(default_factory=list)
    accounts: list[AccountRef] = Field(default_factory=list)


class FirEntity(BaseModel):
    report_id: str
    entity: str | None = None
    type: str | None = None
    matched_id: str | None = None


class FirReport(BaseModel):
    report_id: str
    date: str | None = None
    report_type: str | None = None
    text: str | None = None


class Transaction(BaseModel):
    transaction_id: str
    sender_account: str | None = None
    receiver_account: str | None = None
    amount: float | None = None
    timestamp: str | None = None
    location: str | None = None


class GraphNode(BaseModel):
    id: str
    type: str
    attributes: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str
    key: int | str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class NeighborLink(BaseModel):
    node: GraphNode
    relationship: str
    direction: str


class Case(BaseModel):
    id: int
    case_number: str
    title: str
    description: str | None = None
    status: str = "open"
    created_by: int | None = None
    created_at: str | None = None
    evidence_count: int = 0
    alert_count: int = 0
    note_count: int = 0


class CaseCreate(BaseModel):
    title: str
    description: str | None = None
    created_by: int | None = None


class CaseUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None


class CaseNote(BaseModel):
    id: int
    case_id: int
    author: str | None = None
    body: str
    created_at: str | None = None


class CaseNoteCreate(BaseModel):
    author: str | None = None
    body: str


class EvidenceRecord(BaseModel):
    id: int
    source_type: str
    source_record_id: str
    file_name: str | None = None
    content_hash: str
    previous_hash: str | None = None
    created_at: str | None = None


class EvidenceUploadResponse(EvidenceRecord):
    case_id: int
    summary: dict[str, Any] = Field(default_factory=dict)
    neo4j: bool = False
    duplicate: bool = False


class CaseDetail(Case):
    evidence: list[EvidenceRecord] = Field(default_factory=list)
    notes: list[CaseNote] = Field(default_factory=list)


class AlertSummary(BaseModel):
    total: int
    by_priority: dict[str, int]
    by_anomaly: dict[str, int]


class Neo4jEntity(BaseModel):
    id: str
    type: str
    properties: dict[str, Any] = Field(default_factory=dict)


class Neo4jRelationship(BaseModel):
    relationship_id: str | None = None
    relationship_type: str | None = None
    source: str | None = None
    target: str | None = None
    source_type: str | None = None
    target_type: str | None = None
    source_record_id: str | None = None
    timestamp: str | None = None
    confidence: float | None = None
    amount: float | None = None
    duration: float | None = None
    location: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class SecondHopRecord(BaseModel):
    node: Neo4jEntity
    relationship: Neo4jRelationship


class NeighborLinkRecord(BaseModel):
    node: Neo4jEntity
    relationship: Neo4jRelationship
    direction: str = "undirected"
    second_hop: list[SecondHopRecord] = Field(default_factory=list)


class NeighborsResponse(BaseModel):
    entity: Neo4jEntity
    neighbors: list[NeighborLinkRecord] = Field(default_factory=list)


class BetweenResponse(BaseModel):
    entity_a: Neo4jEntity
    entity_b: Neo4jEntity
    relationships: list[Neo4jRelationship] = Field(default_factory=list)


class TwoHopResponse(BaseModel):
    entity: Neo4jEntity
    first_hop: list[NeighborLinkRecord] = Field(default_factory=list)


class EvidenceResponse(BaseModel):
    relationship: Neo4jRelationship
    source_entity: Neo4jEntity
    target_entity: Neo4jEntity


class ImportSummary(BaseModel):
    nodes: dict[str, int] = Field(default_factory=dict)
    relationships: dict[str, int] = Field(default_factory=dict)


class Neo4jSummary(BaseModel):
    nodes: dict[str, int] = Field(default_factory=dict)
    relationships: dict[str, int] = Field(default_factory=dict)