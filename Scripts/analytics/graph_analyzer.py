from dataclasses import dataclass, field

from Scripts.analytics.metrics.networkx_metrics_calculator import *
from Scripts.analytics.metrics.hypernetwork_metrics_calculator import *
from Scripts.analytics.community_detection import find_communities, compute_average_community_density
from Scripts.analytics.hub_detection import detect_hubs, compute_average_hub_metric
from hypergraphx.core.hypergraph import Hypergraph

@dataclass
class GraphAnalytics:
    total_nodes: int
    average_degree: float
    average_strength: float
    density: float
    weighted_density: float
    average_normalized_strength_of_edges: float
    number_of_communities: int
    number_of_hubs: int
    average_community_density: float
    average_hub_degree: float

@dataclass
class HypergraphAnalytics:
    hyperdensity: float
    average_hyperdegree: float
    group_size_proportions: dict

@dataclass
class AnalysisArtifacts:
    best_partition: dict = field(default_factory=dict)
    hubs: list[str] = field(default_factory=list)

ExcludeOption = Literal["community", "hubs"]

def analyze_graph(graph: nx.Graph, exclude: set[ExcludeOption] = None):
    if exclude is None:
        exclude = set()

    analysis_artifacts = AnalysisArtifacts()

    if "community" not in exclude:
        newman_output = find_communities(graph, "Newman")

        analysis_artifacts.best_partition = newman_output[2]
        number_of_communities = newman_output[1]
        average_community_density = compute_average_community_density(analysis_artifacts.best_partition )
    else:
        number_of_communities = -1
        average_community_density = -1

    if "hubs" not in exclude:
        hubs_dict = detect_hubs(graph, "degree", 95) # best 5%
        number_of_hubs = len(hubs_dict)
        average_hub_degree = compute_average_hub_metric(hubs_dict)

        analysis_artifacts.hubs = list(hubs_dict.keys())
    else:
        number_of_hubs =-1
        average_hub_degree =-1

    graph_analytics = GraphAnalytics(
        total_nodes=graph.number_of_nodes(),
        average_degree=compute_average_per_node(graph, "degree")[0],
        average_strength=compute_average_per_node(graph, "strength")[0],
        density=compute_graph_density(graph),
        weighted_density=compute_graph_weighted_density(graph),
        average_normalized_strength_of_edges=compute_average_normalized_strength_of_edges(graph),
        number_of_communities=number_of_communities,
        average_community_density=average_community_density,
        number_of_hubs=number_of_hubs,
        average_hub_degree=average_hub_degree,
    )

    return graph_analytics, analysis_artifacts

def analyze_hypergraph(graph: Hypergraph):
    hypergraph_analytics = HypergraphAnalytics(
        hyperdensity=-1,
        average_hyperdegree=compute_average_hyper_degree_per_author(graph),
        group_size_proportions=compute_group_size_proportions(graph),
    )

    return hypergraph_analytics