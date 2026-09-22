# NetraLink System Architecture

NetraLink is an investigation graph intelligence platform engineered to detect anomalies across telecom and financial networks, structure relationships into a knowledge graph, and present actionable intelligence to investigators.

```
┌─────────────────────────────────────────────────────────────┐
│                    React Investigator UI                    │
│             (Dashboard, Alerts, Network Graph)              │
└──────────────────────────────┬──────────────────────────────┘
                               │ REST / JSON (Vite Proxy)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI API Server                      │
│        (Routes, Pydantic Models, Service Controllers)       │
└───────┬──────────────────────┬──────────────────────┬───────┘
        │                      │                      │
        ▼                      ▼                      ▼
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│  PostgreSQL  │       │   Neo4j 5    │       │ AIML Outputs │
│ (Cases, User │       │ (Multi-Hop   │       │  (NetworkX   │
│  Audit Logs) │       │  Graph Data) │       │ Centrality)  │
└──────────────┘       └──────────────┘       └──────────────┘
                               │
                               ▼
                 ┌───────────────────────────┐
                 │    Blockchain Anchor      │
                 │   (SHA-256 Immutable)     │
                 └───────────────────────────┘
```

---

## Architecture Components

### 1. Frontend Layer (`frontend/`)
- **Technology**: React 18, Vite 5, React Router 6, Vanilla CSS.
- **Network Graph Engine**:
  - Hardware-accelerated SVG renderer with force-directed physics layout.
  - Multi-touch/mouse wheel zooming, drag-to-pan, and individual node repositioning.
  - Subgraph highlight on selection with connection tracing.

### 2. API & Services Layer (`backend/app/`)
- **Framework**: FastAPI with async route handlers and automatic OpenAPI documentation.
- **Route Modules**:
  - `alerts.py`: High-priority anomaly alerts and score breakdowns.
  - `cases.py`: Investigator case tracking and assignment.
  - `fir.py`: Police First Information Report matches and NLP entity links.
  - `graph.py`: Full knowledge graph querying (NetworkX and Neo4j endpoints).
  - `persons.py`: Entity profiles, communication records, and accounts.
  - `transactions.py`: Financial transaction ledger records.

### 3. Data Storage & Graph Engines
- **Neo4j 5 Property Graph**:
  - Stores entities (`Person`, `Phone`, `Account`, `Vehicle`, `Location`, `FIR_Report`).
  - Stores relationships (`OWNS`, `CALLED`, `TRANSFERRED_TO`, `MENTIONED_IN`, `REPORTED_AT`).
  - Preserves evidentiary timestamps and confidence scores on every edge.
- **PostgreSQL 16**: Relational storage for user accounts, case notes, and audit chains.
- **NetworkX Analytics**: Pre-computed topology, degree centrality, and betweenness centrality.

### 4. Machine Learning & Anomaly Pipeline (`aiml/`)
- **Telecom Anomaly Scoring**: Call volume, duration spikes, and unique contact diversity.
- **Financial Flow Analysis**: Inflow/outflow velocity disparity and pass-through account detection.
- **FIR NLP Extractor**: Matches raw police reports against registered entities.

### 5. Cryptographic Evidence Anchoring (`blockchain/`)
- Content-addressable SHA-256 evidence digests.
- EVM `EvidenceAnchor.sol` smart contract for immutable timestamps and chain of custody.
