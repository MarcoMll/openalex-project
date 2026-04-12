import sys

from typing import Callable
from Scripts.data_aggregation.fetch_raw_data import fetch_raw_data_from_api
from Scripts.data_aggregation.derive_data import derive_raw_data
from Scripts.graph.hypernetwork_builder import build_hypergraphx_graph
from dataclasses import dataclass

from Scripts.graph.graph_builder import build_network_graphs
from Scripts.analytics.graph_analyzer import analyze_graph, analyze_hypergraph
from utils.hypergraph_config import HypergraphConfig
from utils.graph_coloring import GraphColoringConfig, build_graph_coloring_artifacts
from utils.graph_serialization import serialize_graph, serialize_hypergraph
from utils.graph_visualizer import visualize_and_save_graph, GraphConfig
from utils.interactive_graph_converter import generate_interactive_graph
from utils.project_paths import verify_paths

@dataclass
class PipelineConfig:
    institution_id: str
    api_email: str
    api_key: str

base_graph_config = GraphConfig(
    seed=123,
    node_size=20
)

lcc_graph_config = GraphConfig(
    seed=123,
    node_size=20
)

lcc_coloring_config = GraphColoringConfig(
    community_palette=None,
    hub_palette=["#63C791", "#C76399"],
)

hypergraph_config = HypergraphConfig(
    seed=777,
    node_size=15,
    group_size_colors={
        2: "#cfd6e0",
        3: "#4DA3FF",
        4: "#8E44AD",
        5: "#E6194B",
        6: "#E6194B",
    },
)

def _emit_status(on_status: Callable[[str], None] | None, message: str) -> None:
    if on_status is not None:
        on_status(message)

def initialize_pipeline(pipeline_config: PipelineConfig, on_status: Callable[[str], None] | None = None) -> None:
    _emit_status(on_status, "Verifying project directories")
    verify_paths()

    fetch_raw_data_from_api(pipeline_config, on_status=on_status, reset_raw_data=True)

    _emit_status(on_status, "Deriving data")
    derive_raw_data()

    _emit_status(on_status, "Building network graphs")
    graphs = build_network_graphs()
    base_graph = graphs[0]
    lcc_graph = graphs[1]

    _emit_status(on_status, "Building a hypernetwork graph")
    hypergraph = build_hypergraphx_graph(
        lcc_graph,
        hypergraph_config=hypergraph_config,
    )

    _emit_status(on_status, "Analyzing network")
    base_graph_analytics = analyze_graph(base_graph, exclude={"community", "hubs"})
    lcc_graph_analytics = analyze_graph(lcc_graph, exclude=set())
    hypergraph_analytics = analyze_hypergraph(hypergraph)

    lcc_graph_coloring = build_graph_coloring_artifacts(
        lcc_graph,
        lcc_graph_analytics[1],
        config=lcc_coloring_config,
    )

    _emit_status(on_status, "Plotting graphs")
    visualize_and_save_graph("base_graph", base_graph, base_graph_config)
    visualize_and_save_graph("largest_connected_component_graph", lcc_graph, lcc_graph_config)
    visualize_and_save_graph(
        "lcc_community_graph",
        lcc_graph,
        lcc_graph_config,
        node_colors=lcc_graph_coloring.communities,
    )
    visualize_and_save_graph(
        "lcc_hubs_graph",
        lcc_graph,
        lcc_graph_config,
        node_colors=lcc_graph_coloring.hubs,
    )

    _emit_status(on_status, "Setting up the Interactive Environment")
    generate_interactive_graph(lcc_graph)

    _emit_status(on_status, "Serializing")
    serialize_graph(
        "base_graph",
        base_graph,
        base_graph_analytics[0],
        base_graph_config,
    )
    serialize_graph(
        "lcc",
        lcc_graph,
        lcc_graph_analytics[0],
        lcc_graph_config,
        graph_coloring=lcc_graph_coloring,
    )
    serialize_hypergraph(
        "hypergraph",
        hypergraph,
        hypergraph_analytics,
        hypergraph_config=hypergraph_config,
    )

    _emit_status(on_status, "Completed")