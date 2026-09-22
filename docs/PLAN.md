# NetraLink Development Roadmap

Development plan tracking implementation phases from prototype to production.

## Milestone Status

| Phase | Milestone | Scope | Status |
|---|---|---|---|
| **0** | Repository & Architecture | Directory layout, schemas, raw data contracts | **Complete** |
| **1** | FastAPI & AIML Pipeline | REST endpoints, data loaders, anomaly scoring | **Complete** |
| **2** | React Investigator UI | Dashboard, Alerts, Entity detail, Network graph | **Complete** |
| **3** | Relational Database Layer | PostgreSQL setup, cases, notes, audit logs | In Progress |
| **4** | Neo4j Knowledge Graph | Multi-hop search, Cypher queries, graph seeding | **Complete** |
| **5** | Security & RBAC | JWT authentication, role-based access control | Planned |
| **6** | Evidence Integrity | SHA-256 evidence hashing and chain-of-custody | **Complete** |
| **7** | Blockchain Anchoring | Solidity smart contract and anchoring scripts | **Complete** |
| **8** | Deployment & Demo | Dockerization, production bundle, end-to-end tests | Planned |

---

## Deliverables Checklist

- [x] High-performance force-directed interactive network graph.
- [x] Anomaly scoring across telecom and banking records.
- [x] Unified FastAPI graph routing (NetworkX + Neo4j).
- [x] Clean modular directory structure.
- [ ] Production JWT authentication flow.
- [ ] Docker Compose bundle for PostgreSQL, Neo4j, Backend, and Frontend.
