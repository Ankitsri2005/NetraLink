# NetraLink AIML Pipeline

This directory contains the machine learning, anomaly detection, and knowledge graph construction pipeline.

## Structure

```
aiml/
├── notebooks/
│   ├── 01_data_preprocessing.ipynb    # Clean raw telecom, banking, and FIR records
│   ├── 02_anomaly_detection.ipynb     # Isolation Forest & graph feature anomaly scoring
│   ├── 03_network_analysis.ipynb      # NetworkX graph construction & centrality metrics
│   └── 04_fir_nlp_extraction.ipynb    # NLP entity extraction from police FIR reports
└── outputs/
    ├── anomaly_results.csv            # Anomaly-scored suspect entities
    ├── fir_entities_final.csv         # Extracted FIR entities (names, phones, vehicles)
    ├── investigation_alerts.csv       # High-priority investigation alert feed
    └── netralink_final_graph.pkl       # Pickled NetworkX multi-directed knowledge graph
```

## Data Flow

```
data/raw/ ──▶ [01 Preprocess] ──▶ [02 Anomaly Detection] ──▶ outputs/anomaly_results.csv
                                           │
                                  [03 Network Analysis] ──▶ outputs/netralink_final_graph.pkl
                                           │
          [04 FIR NLP] ────────────────────┴───────────────▶ outputs/investigation_alerts.csv
```
