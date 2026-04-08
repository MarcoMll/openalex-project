# OpenAlex LUISS Co-authorship Network
Developers:
* Marco Malliani 324971
* Ryder Mills Wood 321481

### Project overview

This project builds an institution-scoped co-authorship network from OpenAlex data.

Final network artifact:
* undirected weighted graph
* node = OpenAlex author ID
* edge weight = number of shared works for that author pair
* scope = works containing at least two authors from the target institution

---

### Current progress (refactor status)

Completed:
* split graph logic into dedicated modules (`graph_builder`, `graph_analyzer`, `graph_coloring`, `graph_serialization`)
* introduced a cleaner pipeline orchestrator (`Scripts/init_pipeline.py`)
* unified color generation for both visualization and serialization through `GraphColoringArtifacts`
* updated report loader to use new visualization API and new report shape

In progress:
* final cleanup/removal of legacy API files
* minor documentation and compatibility cleanup around old helper scripts

---

### Repository structure (current)

* `Assets/`
  * `Images/` generated static graph images (`base_graph.png`, `largest_connected_component_graph.png`, etc.)
  * `Graphs/` interactive HTML graph (`interactive_graph.html`)
  * `gui/` frontend icons and style assets
* `Data/`
  * `Raw/` raw OpenAlex dumps (`raw_authors.jsonl`, `raw_works.jsonl`)
  * `Derived/` derived artifacts (`derived_works.jsonl`, `hyperedges.jsonl`, `edges.csv`)
  * `Analytics/` final report (`scholarnet_report.json`)
* `Scripts/`
  * `pipeline/` data fetch + derivation
  * `graph/` graph building/loading/hypergraph modules
  * `analytics/` graph and hypergraph analytics
  * `init_pipeline.py` end-to-end orchestration
* `utils/`
  * `project_paths.py` project path source of truth
  * `graph_visualizer.py` static rendering
  * `graph_coloring.py` coloring artifacts generation
  * `graph_serialization.py` report writer
  * `interactive_graph_converter.py` PyVis interactive graph generation
* `app/frontend/` Streamlit UI

---

### New pipeline (primary API)

Implemented in: `Scripts/init_pipeline.py`

Execution order:
1. fetch raw data (`Scripts/pipeline/fetch_raw_data.py`)
2. derive data (`Scripts/pipeline/derive_data.py`)
3. build network graphs (`Scripts/graph/graph_builder.py`)
4. build hypernetwork image (`Scripts/graph/hypernetwork_builder.py`)
5. analyze graphs (`Scripts/analytics/graph_analyzer.py`)
6. prepare colors once (`utils/graph_coloring.py`)
7. render static images (`utils/graph_visualizer.py`)
8. generate interactive graph (`utils/interactive_graph_converter.py`)
9. serialize final report (`utils/graph_serialization.py`)

---

### Key modules

### `Scripts/graph/graph_builder.py`
Purpose:
* reconstructs base graph from `Data/Derived/edges.csv`
* extracts LCC subgraph

### `Scripts/analytics/graph_analyzer.py`
Purpose:
* computes core graph metrics
* computes communities and hubs
* returns:
  * `GraphAnalytics` (metrics)
  * `AnalysisArtifacts` (best partition + hub nodes)

### `utils/graph_coloring.py`
Purpose:
* builds deterministic node-color arrays from analysis artifacts
* supports:
  * numeric color IDs (for colormap workflows like `tab20`)
  * optional HEX palette mapping (if explicitly configured)

### `utils/graph_visualizer.py`
Purpose:
* renders and saves static graph images with deterministic layout seed
* supports either numeric or HEX node colors

### `utils/graph_serialization.py`
Purpose:
* writes the final report JSON
* merges writes by graph key (does not overwrite previous graph section)
* serializes graph analytics and reconstruction payload

### `Scripts/graph/graphs_loader.py`
Purpose:
* reconstructs graphs from `scholarnet_report.json`
* regenerates static images + hypergraph + interactive graph
* supports both current and legacy reconstruction config fields where possible

---

### Report format (current)

Output file: `Data/Analytics/scholarnet_report.json`

High-level shape:

```json
{
  "base_graph": {
    "graph_analytics": {
      "total_nodes": 0,
      "average_degree": 0.0
    },
    "reconstruction_data": {
      "nodes": [],
      "edges": [],
      "graph_config": {
        "seed": 777,
        "node_size": 20
      },
      "color_partitions": {
        "communities": [],
        "hubs": []
      }
    }
  },
  "lcc": {
    "graph_analytics": {},
    "reconstruction_data": {}
  }
}
```

---

### Run instructions

Requirements:
* Python 3.10+
* dependencies in `requirements.txt`

Install:
```bash
pip install -r requirements.txt
```

Run full pipeline:
```bash
python Scripts/pipeline.py
```

Load an existing report and regenerate visual artifacts:
```python
from Scripts.graph.graphs_loader import load_graphs
load_graphs()
```

---

### Frontend notes

The Streamlit UI reads analytics from `Data/Analytics/scholarnet_report.json`.

Graph metric cards are now aligned with the new nested analytics structure:
* `graph_key -> graph_analytics -> metric`

---

### Legacy API note

Some legacy scripts are still present during cleanup, but the **primary supported flow** is the new modular pipeline described above.

---

### Copyright and Academic Integrity

This project was created as part of university coursework.

Copyright (c) 2026 Marco Malliani and Ryder Mills Wood.
All rights reserved.

No copying, redistribution, modification, republication, or submission of this
project as one's own work is permitted without explicit written permission from
the copyright holders.
