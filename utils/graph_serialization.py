import networkx as nx
import json

from typing import Any
from utils.project_paths import get_paths
from utils.graph_visualizer import GraphConfig
from dataclasses import dataclass, field, asdict
from Scripts.analytics.graph_analyzer import GraphAnalytics, HypergraphAnalytics
from utils.graph_coloring import GraphColoringArtifacts

P = get_paths()
REPORT_FILE_NAME = "scholarnet_report.json"

@dataclass
class ColorPartitions:
    communities: list[Any] = field(default_factory=list)
    hubs: list[Any] = field(default_factory=list)

@dataclass
class ReconstructionData:
    # basic data
    nodes: list[str] = field(default_factory=list)
    edges: list[dict] = field(default_factory=list)

    # generation properties
    graph_config: GraphConfig = field(default_factory=GraphConfig)
    color_partitions: ColorPartitions = field(default_factory=ColorPartitions)

@dataclass
class GraphData:
    graph_name: str
    graph_analytics: GraphAnalytics
    reconstruction_data: ReconstructionData

@dataclass
class HypergraphData:
    graph_name: str
    graph_analytics: HypergraphAnalytics

def serialize_edges(graph: nx.Graph):
    edges = [
        {"u": u, "v": v, "weight": data.get("weight", 1.0)}
        for u, v, data in graph.edges(data=True)
    ]

    return edges

def serialize_hypergraph(graph_name: str, graph: Any, graph_analytics: HypergraphAnalytics):
    hypergraph_data = HypergraphData(graph_name=graph_name, graph_analytics=graph_analytics)
    save_to_json(hypergraph_data)

def serialize_graph(
    graph_name: str,
    graph: nx.Graph,
    graph_analytics: GraphAnalytics,
    graph_config: GraphConfig,
    graph_coloring: GraphColoringArtifacts | None = None,
):
    community_colors = []
    hub_colors = []

    if graph_coloring is not None:
        if graph_coloring.node_order != list(graph.nodes()):
            raise ValueError(
                "graph_coloring.node_order does not match current graph node order."
            )
        community_colors = graph_coloring.communities
        hub_colors = graph_coloring.hubs

    color_partitions = ColorPartitions(
        communities=community_colors if community_colors is not None else [],
        hubs=hub_colors if hub_colors is not None else [],
    )

    reconstruction_data = ReconstructionData(
        nodes=list(graph.nodes),
        edges=serialize_edges(graph),
        graph_config=graph_config,
        color_partitions=color_partitions,
    )

    graph_data = GraphData(
        graph_name=graph_name,
        graph_analytics=graph_analytics,
        reconstruction_data=reconstruction_data,
    )

    save_to_json(graph_data)

def save_to_json(graph_data: GraphData | HypergraphData):
    payload = asdict(graph_data)
    graph_name = payload.pop("graph_name")  # ключ верхнего уровня в report

    save_path = P.ANALYTICS_DIR / REPORT_FILE_NAME
    save_path.parent.mkdir(parents=True, exist_ok=True)

    data = {}
    if save_path.exists():
        with save_path.open("r", encoding="utf-8") as f:
            try:
                loaded = json.load(f)
            except json.JSONDecodeError:
                loaded = {}

        if isinstance(loaded, dict):
            data = loaded

    data[graph_name] = payload

    with save_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)