from pathlib import Path
import json
import webbrowser

from pyvis.network import Network
import networkx as nx

from utils.project_paths import get_paths

P = get_paths()
GRAPHS_DIR = Path(P.GRAPHS_DIR)
RAW_AUTHORS_PATH = Path(P.RAW_AUTHORS)
BUTTON_STYLE_SNIPPET = """
<style>
.btn-primary {
  background-color: #63c791 !important;
  border-color: #63c791 !important;
}
.btn-primary:hover,
.btn-primary:focus,
.btn-primary:active {
  background-color: #57b884 !important;
  border-color: #57b884 !important;
}
</style>
"""
EDGE_FOCUS_SCRIPT = """
<script>
(function () {
  function applyNameSearchOptions() {
    const selectElement = document.getElementById("select-node");
    if (!selectElement || typeof nodes === "undefined") {
      return;
    }

    const allNodes = nodes.get({ returnType: "Object" });
    const mappedOptions = [];

    for (const option of Array.from(selectElement.options)) {
      if (!option.value) {
        continue;
      }
      const nodeData = allNodes[option.value];
      if (!nodeData) {
        continue;
      }

      const label = nodeData.label || option.value;
      option.textContent = label;
      mappedOptions.push({ value: option.value, text: label });
    }

    if (selectElement.tomselect) {
      const ts = selectElement.tomselect;
      const selectedValue = ts.getValue();

      ts.clearOptions();
      ts.addOptions(mappedOptions);
      ts.refreshOptions(false);

      if (selectedValue) {
        ts.setValue(selectedValue, true);
      }
    }
  }

  function setConnectedNodeAccent(selectedNodes) {
    if (typeof nodes === "undefined" || typeof network === "undefined") {
      return;
    }

    if (!Array.isArray(selectedNodes) || selectedNodes.length === 0) {
      return;
    }

    const selectedNode = selectedNodes[0];
    const connectedNodes = network.getConnectedNodes(selectedNode);
    const updates = [];

    for (const nodeId of connectedNodes) {
      updates.push({
        id: nodeId,
        color: {
          background: "#6399c7",
          border: "#6399c7",
          highlight: {
            background: "#63c7c3",
            border: "#63c7c3"
          },
          hover: {
            background: "#6399c7",
            border: "#6399c7"
          }
        }
      });
    }

    if (updates.length > 0) {
      nodes.update(updates);
    }
  }

  function setEdgeFocus(selectedNodes) {
    if (typeof edges === "undefined" || typeof network === "undefined") {
      return;
    }

    const allEdges = edges.get({ returnType: "Object" });
    const updates = [];
    const hasSelection = Array.isArray(selectedNodes) && selectedNodes.length > 0;
    const selectedNode = hasSelection ? selectedNodes[0] : null;
    const connectedEdgeIds = hasSelection ? new Set(network.getConnectedEdges(selectedNode)) : new Set();

    for (const edgeId in allEdges) {
      if (!Object.prototype.hasOwnProperty.call(allEdges, edgeId)) {
        continue;
      }

      if (hasSelection && !connectedEdgeIds.has(edgeId) && !connectedEdgeIds.has(Number(edgeId))) {
        updates.push({
          id: edgeId,
          color: {
            color: "rgba(103, 199, 99, 0.18)",
            highlight: "rgba(99, 199, 195, 0.25)",
            hover: "rgba(99, 199, 195, 0.25)",
            inherit: false
          }
        });
      } else {
        updates.push({
          id: edgeId,
          color: {
            color: "#67c763",
            highlight: "#63c7c3",
            hover: "#63c7c3",
            inherit: false
          }
        });
      }
    }

    edges.update(updates);
  }

  function resetSelectionVisuals() {
    if (typeof neighbourhoodHighlight === "function") {
      neighbourhoodHighlight({ nodes: [] });
    }
    setEdgeFocus([]);
  }

  function applySelectionFromSearch(nodeId) {
    if (!nodeId || typeof network === "undefined") {
      return;
    }

    const selected = [nodeId];
    network.selectNodes(selected);

    if (typeof neighbourhoodHighlight === "function") {
      neighbourhoodHighlight({ nodes: selected });
    }

    setEdgeFocus(selected);
    setConnectedNodeAccent(selected);
  }

  function bindSearchSelectionHandlers() {
    const selectElement = document.getElementById("select-node");
    if (!selectElement) {
      return;
    }

    selectElement.addEventListener("change", function () {
      if (selectElement.value) {
        applySelectionFromSearch(selectElement.value);
      } else {
        resetSelectionVisuals();
      }
    });

    if (selectElement.tomselect) {
      const ts = selectElement.tomselect;
      ts.on("change", function (value) {
        const nodeId = Array.isArray(value) ? value[0] : value;
        if (nodeId) {
          applySelectionFromSearch(nodeId);
        } else {
          resetSelectionVisuals();
        }
      });
    }
  }

  function bindEdgeFocusHandlers() {
    if (typeof network === "undefined") {
      return;
    }

    applyNameSearchOptions();
    bindSearchSelectionHandlers();

    network.on("selectNode", function (params) {
      setEdgeFocus(params.nodes || []);
      setConnectedNodeAccent(params.nodes || []);
    });

    network.on("deselectNode", function () {
      resetSelectionVisuals();
    });

    network.on("click", function (params) {
      if (!params.nodes || params.nodes.length === 0) {
        resetSelectionVisuals();
      }
    });
  }

  bindEdgeFocusHandlers();
})();
</script>
"""


def _load_author_display_names(path: Path = RAW_AUTHORS_PATH) -> dict[str, str]:
    if not path.exists():
        return {}

    display_names: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as source:
        for line in source:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            author_id = entry.get("id")
            display_name = entry.get("display_name")
            if isinstance(author_id, str) and author_id and isinstance(display_name, str) and display_name:
                display_names[author_id] = display_name

    return display_names

def generate_interactive_graph(nx_graph: nx.Graph, graph_name: str = "interactive_graph.html"):
    net = Network(
        height="750px",
        width="100%",
        bgcolor="#ffffff",
        font_color="#111111",
        select_menu=True,
        cdn_resources="remote",
    )

    author_display_names = _load_author_display_names()
    degrees = dict(nx_graph.degree())
    strengths = dict(nx_graph.degree(weight="weight"))

    for node in nx_graph.nodes():
        deg = degrees[node]
        strg = strengths.get(node, 0)
        display_name = author_display_names.get(node, node)

        nx_graph.nodes[node]["value"] = deg
        nx_graph.nodes[node]["color"] = {
            "background": "#63c791",
            "border": "#63c791",
            "highlight": {
                "background": "#63c7c3",
                "border": "#63c7c3",
            },
            "hover": {
                "background": "#63c791",
                "border": "#63c791",
            },
        }
        nx_graph.nodes[node]["title"] = (
            f"Name: {display_name}\n"
            f"Author ID: {node}\n"
            f"Degree: {deg}\n"
            f"Strength: {strg:.2f}"
        )
        nx_graph.nodes[node]["label"] = display_name

    for u, v, data in nx_graph.edges(data=True):
        if "weight" in data:
            data["value"] = data["weight"]
            data["title"] = f"Weight: {data['weight']}"
        data["color"] = {
            "color": "#67c763",
            "highlight": "#63c7c3",
            "hover": "#63c7c3",
            "inherit": False,
        }

    net.from_nx(nx_graph)

    # ensure output dir exists
    GRAPHS_DIR.mkdir(parents=True, exist_ok=True)

    html_file_path = GRAPHS_DIR / graph_name
    print(f"Generating interactive graph at: {html_file_path}")
    net.write_html(str(html_file_path))
    html = html_file_path.read_text(encoding="utf-8")
    html = html.replace("Select a Node by ID", "Select a Node by Name")
    if BUTTON_STYLE_SNIPPET not in html and "</head>" in html:
        html = html.replace("</head>", f"{BUTTON_STYLE_SNIPPET}\n</head>")
    if EDGE_FOCUS_SCRIPT not in html and "</body>" in html:
        html = html.replace("</body>", f"{EDGE_FOCUS_SCRIPT}\n</body>")
    html_file_path.write_text(html, encoding="utf-8")

    #webbrowser.open(f"file://{GRAPHS_DIR / graph_name}")
