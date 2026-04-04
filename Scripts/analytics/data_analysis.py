from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict
import networkx as nx

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def explain_betweenness_centrality_normalized(betweenness_dict: Dict[str, float]) -> str:
    """
    Explain normalized betweenness centrality in a co-authorship graph using fixed thresholds.

    Thresholds:
    - 0.000 <= value < 0.010: Very low betweenness
    - 0.010 <= value < 0.050: Low to moderate betweenness
    - 0.050 <= value < 0.150: High betweenness
    - 0.150 <= value: Very high / dominant betweenness
    """
    average_score = sum(betweenness_dict.values()) / len(betweenness_dict) if betweenness_dict else 0.0

    if average_score < 0.010:
        explanation = (
            "With this in mind, the top 5% of authors suggests that even the strongest potential brokers in the network are not especially dominant as bridges."
            "In this co-authorship graph, this means collaboration paths do not rely heavily on a small elite group of authors to connect communities. The network may be relatively decentralized, "
            "or communities may already be interconnected enough that no particular set of authors controls the flow between them."
        )
    elif average_score < 0.050:
        explanation = (
            "With this in mind, the top 5% of authors play some meaningful bridging role, "
            "but they are not overwhelmingly important to the network’s structure. In this co-authorship graph, "
            "this means the most central authors help connect different research groups, but the graph is not excessively dependent on them. "
            "Collaboration between communities is present, and the network likely retains some structural flexibility even without very dominant brokers."
        )
    elif average_score < 0.150:
        explanation = (
            "With this in mind, the top 5% of authors are important structural bridges in the co-authorship network. "
            "This suggests that a small set of researchers frequently sits on the shortest paths between different communities, "
            "meaning they play a major role in linking otherwise separate collaboration clusters. In practice, this often reflects senior academics, "
            "interdisciplinary researchers, or highly connected collaborators who help ideas, projects, and partnerships move across the network."
        )
    else:
        explanation = (
            "With this in mind, the top 5% of authors are extremely influential brokers in the co-authorship graph. "
            "This means the network depends strongly on a small number of researchers to connect different communities, departments, "
            "or subfields. Such a pattern can indicate strong leadership and high cross-group coordination, but it can also reveal structural vulnerability, "
            "since removing or losing these authors could significantly reduce collaboration flow across the network."
        )

    return f"Based on the betweenness centrality scores, the top 5% of authors include {list(betweenness_dict.values())}. {explanation}"


def explain_average_community_density(value: float):
    """
    Explain average community density in a co-authorship graph using fixed thresholds.

    Thresholds:
    - 0.00 <= value < 0.10: Very low community density
    - 0.10 <= value < 0.30: Low to moderate community density
    - 0.30 <= value < 0.60: Moderately high community density
    - 0.60 <= value <= 1.00: Very high community density
    """
   

    if value < 0.10:
        explanation = (
            "indicates that the detected communities are very loose internally. "
            "In this co-authorship network, it means that although authors may be grouped into the same community by the "
            "algorithm, they are not all strongly collaborating with one another. These communities may represent broad "
            "thematic similarity rather than tightly functioning research teams."
        )
    elif value < 0.30:
        explanation = (
            "indicates that communities have some internal structure, but they are not highly cohesive. "
            "In co-authorship terms, this often reflects research groups where collaboration exists, but not all authors "
            "collaborate directly with many others in the same group. The communities are real, but they may contain subgroups "
            "or be organized around a few central collaborators rather than dense all-to-all interaction."
        )
    elif value < 0.60:
        explanation = (
            "indicates that the detected communities are fairly cohesive. "
            "In a co-authorship network, this means authors inside the same community frequently collaborate with one another, "
            "which is consistent with organized labs, stable teams, or closely related academic subfields. These communities "
            "are meaningful and socially or scientifically coherent."
        )
    else:
        explanation = (
            "indicates very tightly knit communities. In the context of co-authorship, this means "
            "many authors inside the same group collaborate directly with each other, which is typical of highly integrated "
            "research teams or small, intensely collaborative clusters. If many communities are this dense, the network "
            "is composed of strongly bonded groups with clear internal collaboration patterns."
        )

    return f"An average community density in this range = {value:.4f} {explanation}"


def explain_community_modularity(value: float):
    """
    Explain community modularity in a co-authorship graph using fixed thresholds.

    Thresholds:
    - value < 0.20: Weak community structure
    - 0.20 <= value < 0.40: Moderate community structure
    - 0.40 <= value <= 0.60: Strong community structure
    - value > 0.60: Very strong / highly separated community structure
    """
    if value < 0.20:
        explanation = (
            "indicates that the co-authorship network has weakly defined communities. "
            "This means collaboration ties are spread in a way that does not strongly separate authors into distinct groups. "
        )
    elif value < 0.40:
        explanation = (
            "indicates noticeable but not extremely strong community structure. In the co-authorship graph, "
            "this suggests that authors do cluster into research groups or thematic areas, but there is still a fair amount of "
            "cross-community collaboration. The communities are meaningful, though not sharply isolated from one another."
        )
    elif value <= 0.60:
        explanation = (
            "indicates strong community organization in the co-authorship network. This means "
            "authors tend to collaborate much more within their own communities than outside them. In academic terms, this often "
            "reflects well-defined labs, departments, research themes, or institutional clusters with relatively limited cross-group "
            "collaboration."
        )
    else:
        explanation = (
            "indicates very strong separation between communities. In a co-authorship graph, this means the "
            "network is highly partitioned into distinct collaboration groups, with relatively few ties connecting them. This can "
            "reflect specialization and strong internal teamwork, but it may also suggest silos, limited interdisciplinarity, or "
            "weak collaboration across research areas."
        )

    return f"Community modularity of = {value:.4f} {explanation}"


def explain_average_hub_degree_top_5_percent_ratio(average_hub_degree: float, average_degree: float):
    """
    Explain average hub degree dominance based on the ratio:
    R = (average degree of top 5% hubs) / (graph average degree)

    Thresholds:
    - R < 1.5: Weak hub dominance
    - 1.5 <= R < 3.0: Moderate hub dominance
    - 3.0 <= R <= 6.0: Strong hub dominance
    - R > 6.0: Very strong / highly centralized hub dominance
    """
    r_value = average_hub_degree/average_degree

    if r_value < 1.5:
        explanation = (
            "This ratio indicates that the network "
            "does not appear strongly hub-dominated. In the co-authorship graph, this suggests collaboration opportunities "
            "are more evenly spread across authors, and the most connected researchers are not dramatically more central "
            "than everyone else. The structure is therefore relatively balanced."
        )
    elif r_value < 3.0:
        explanation = (
            "This ratio suggests a moderate hub effect. In the co-authorship network, the most connected authors "
            "clearly collaborate with more people than average, but they do not completely dominate the graph. This often "
            "reflects senior researchers, supervisors, or active interdisciplinary scholars who collaborate broadly without "
            "the network becoming entirely centered around them."
        )
    elif r_value <= 6.0:
        explanation = (
            "This ratio indicates that the top 5% of authors act as major collaboration hubs. In the co-authorship "
            "graph, this means a small set of researchers collaborates with far more people than the average author, likely "
            "shaping the structure of the network. This can reflect strong leadership, visibility, or coordination roles, "
            "but it may also mean collaboration is concentrated around a limited elite group."
        )
    else:
        explanation = (
            "This ratio indicates that the network is extremely hub-centered. In the co-authorship graph, the most connected "
            "authors have far more collaborative reach than the rest of the graph, which can indicate dependency on a few highly "
            "active individuals. This may increase efficiency and visibility, but it can also reveal structural imbalance where "
            "many collaborations depend on a very small group of central authors."
        )

    return f"The average hub degree is {average_hub_degree:.4f}, and the dominance ratio (R) = {r_value:.4f}. {explanation}"


def explain_weighted_density_whole_graph(value: float):
    """
    Explain weighted density of the whole graph.

    Thresholds:
    - 0.00 <= value < 0.05: Very low weighted density
    - 0.05 <= value < 0.15: Low weighted density
    - 0.15 <= value < 0.30: Moderate weighted density
    - 0.30 <= value: High weighted density
    """

    if value < 0.05:
        explanation = (
            "This weighted density indicates that the overall collaboration strength across the graph is very weak. "
            "In the co-authorship network, this means that not only are relatively few pairs of authors connected, but even the "
            "existing ties are not very intense in terms of repeated joint publications."
        )
    elif value < 0.15:
        explanation = (
            "This weighted density indicates a lightly connected collaboration structure with limited repetition of ties. "
            "In the co-authorship network, authors may collaborate, but many of these ties are probably based on one-off "
            "or infrequent publications. The network contains real collaboration, though it is not yet strongly reinforced "
            "through repeated co-authorship."
        )
    elif value < 0.30:
        explanation = (
            "This weighted density indicates a reasonably cohesive network with repeated collaboration patterns. "
            "In the co-authorship network, this means that authors are not only connected, but many ties also carry meaningful "
            "weight through multiple shared publications. The network likely contains stable working relationships and recurring teams."
        )
    else:
        explanation = (
            "This weighted density indicates a strongly reinforced collaboration network. In the co-authorship network, this suggests "
            "that collaboration is both widespread and repeated, meaning authors often publish multiple times with the same "
            "partners. Such a structure is typical of mature, stable research groups or strongly established collaboration ecosystems."
        )

    return f"Weighted density of the whole graph = {value:.4f}. {explanation}"


def explain_density_whole_graph(value: float):
    """
    Explain density of the whole graph.

    Thresholds:
    - 0.000 <= value < 0.010: Extremely sparse
    - 0.010 <= value < 0.050: Sparse
    - 0.050 <= value < 0.150: Moderately dense
    - 0.150 <= value: High density
    """

    if value < 0.010:
        explanation = (
            "This density indicates an extremely sparse co-authorship network. This means only a very small "
            "fraction of all possible pairs of authors have collaborated. Such a structure is common in large academic "
            "graphs, where most researchers only interact with a limited number of others and the network expands through "
            "many weakly connected local circles."
        )
    elif value < 0.050:
        explanation = (
            "This density indicates a sparse but meaningful collaboration network. In the co-authorship graph, "
            "this suggests that collaboration exists across the graph, but authors still work with a relatively limited "
            "subset of possible partners. This is often a normal pattern in academic networks, where specialization and "
            "institutional boundaries keep density low."
        )
    elif value < 0.150:
        explanation = (
            "This density indicates a reasonably cohesive network with repeated collaboration patterns. "
            "In the co-authorship network, this means that authors are not only connected, but many ties also carry meaningful "
            "weight through multiple shared publications. The network likely contains stable working relationships and recurring teams."
        )
    else:
        explanation = (
            "This density indicates a highly connected co-authorship graph. In practice, this suggests that many "
            "authors collaborate with many others, creating a strongly interlinked structure. This can point to an unusually "
            "cohesive research environment, where collaboration is common and boundaries between groups are relatively weak."
        )

    return f"The density of the whole graph = {value:.4f}. {explanation}"


def explain_average_degree_whole_graph(value: float):
    """
    Explain average degree of the whole graph.

    Thresholds:
    - 0 <= value < 2: Very low average degree
    - 2 <= value < 5: Low to moderate average degree
    - 5 <= value < 10: Moderately high average degree
    - 10 <= value: High average degree
    """

    if value < 2:
        explanation = (
            "This degree indicates that authors have very few direct collaborators on average. "
            "In the co-authorship network, this indicates a fragmented or highly specialized structure, where many "
            "researchers only work with one or two others. Collaboration exists, but it is limited in breadth and may "
            "be concentrated in isolated pairs or small teams."
        )
    elif value < 5:
        explanation = (
            "This degree indicates a modestly connected co-authorship graph. Authors generally have a few "
            "collaborators, enough to create local structure, but not enough to make the network broadly integrated. "
            "This often reflects normal academic collaboration patterns, where researchers work within small teams or "
            "recurring circles."
        )
    elif value < 10:
        explanation = (
            "This degree indicates that authors collaborate with a substantial number of others. "
            "In the co-authorship graph, this suggests an active and relatively open collaboration environment, where "
            "researchers are not limited to just one small group. The network is likely well integrated and capable of "
            "spreading ideas efficiently through direct ties."
        )
    else:
        explanation = (
            "This degree indicates a very collaborative network in which authors, on average, have many co-authorship "
            "ties. In the co-authorship graph, this can reflect a mature research community, frequent multi-author publishing, or broad "
            "collaboration across labs and subfields. While this indicates strong connectedness, it may also hide inequality "
            "if much of the connectivity is driven by a small number of hubs."
        )

    return f"Average degree of the whole graph = {value:.4f}. {explanation}"


def explain_average_strength_of_edges(value: float):
    """
    Explain average normalized tie strength (average strength of edges).

    Thresholds:
    - 0.00 <= value < 0.10: Very weak average normalized tie strength
    - 0.10 <= value < 0.25: Weak to low-moderate normalized tie strength
    - 0.25 <= value < 0.50: Moderate normalized tie strength
    - 0.50 <= value < 0.75: Strong normalized tie strength
    - 0.75 <= value <= 1.00: Very strong normalized tie strength
    """

    if value < 0.10:
        explanation = (
            "This indicates that most existing co-authorship ties are very weak relative to the strongest "
            "ties in the graph. In practice, this means many author pairs may have collaborated only once, or only at a very "
            "limited level, and repeated collaboration is not very strong across the network. The graph may contain many "
            "connections, but those connections are not deeply reinforced."
        )
    elif value < 0.25:
        explanation = (
            "This indicates that the network has mostly light collaboration ties, with some repeated partnerships "
            "but not many strong ones. In the co-authorship graph, this often means that while authors do collaborate, many of "
            "those collaborations are still occasional rather than long-term or highly repeated. The network shows breadth of "
            "interaction more than depth."
        )
    elif value < 0.50:
        explanation = (
            "This indicates that the average existing collaboration tie has moderate strength. In the "
            "co-authorship graph, this suggests that a meaningful share of author pairs have collaborated more than once, and the network "
            "contains a reasonable amount of stable or recurring partnership. The graph is not dominated by one-off connections alone."
        )
    elif value < 0.75:
        explanation = (
            "This indicates that the existing ties in the network are fairly strong on average. In the co-authorship "
            "graph, this means many connected author pairs have substantial repeated collaboration, which points to stable teams, "
            "long-term research relationships, or recurring publication partnerships. This indicates depth in collaboration, not just connectivity."
        )
    else:
        explanation = (
            "This indicates that the existing co-authorship ties are extremely strong on average relative to the "
            "network's scale. This suggests that many connected author pairs are involved in highly repeated collaboration, which "
            "is typical of very stable research teams or tightly bonded academic groups. The network's collaboration structure is "
            "therefore strongly reinforced."
        )

    return f"Average strength of edges = {value:.4f}. {explanation}"


def explain_density_and_average_degree(density: float, average_degree: float):
    """
    Joint explanation using AND logic on:
    - density thresholds already used in this file
      low: value < 0.050
      moderate: 0.050 <= value < 0.150
      high: value >= 0.150
    - average degree thresholds already used in this file
      low: value < 5
      moderate: 5 <= value < 10
      high: value >= 10
    """
    if density < 0:
        raise ValueError("Density cannot be negative.")
    if average_degree < 0:
        raise ValueError("Average degree cannot be negative.")

    if density < 0.050:
        density_band = "low"
    elif density < 0.150:
        density_band = "moderate"
    else:
        density_band = "high"

    if average_degree < 5:
        degree_band = "low"
    elif average_degree < 10:
        degree_band = "moderate"
    else:
        degree_band = "high"

    if density_band == "low" and degree_band == "low":
        explanation = (
            "When both density and average degree are low, the institute can be described as weakly collaborative overall. "
            "Collaboration exists, but it is limited both in terms of how widely it is spread across the institute and in terms "
            "of how many co-authors the typical researcher has. This suggests a fragmented research environment where most "
            "collaboration happens inside small, separate groups rather than across the institution as a whole."
        )
    elif density_band == "low" and degree_band in {"moderate", "high"}:
        explanation = (
            "When density is low but average degree is moderate or high, the institute may still have active researchers "
            "individually, but collaboration is not broadly spread across the whole institution. This suggests that many "
            "researchers do collaborate with several others, yet the institute overall remains globally sparse, possibly because "
            "collaboration happens within selected teams, disciplines, or hubs rather than across the full research body."
        )
    elif density_band == "moderate" and degree_band == "moderate":
        explanation = (
            "When both density and average degree are moderate, the institute can be described as reasonably collaborative overall. "
            "Researchers are collaborating with a meaningful number of colleagues, and collaboration is spread across a noticeable "
            "portion of the institution. This suggests a healthy collaboration culture, though not one that is fully integrated "
            "across all researchers."
        )
    elif density_band == "high" and degree_band == "high":
        explanation = (
            "When both density and average degree are high, the institute can be described as highly collaborative overall. "
            "Researchers not only have many collaborators on average, but collaboration is also widely distributed across the institution. "
            "In a co-authorship graph, this points to a cohesive academic environment in which research ties are broad, active, and well integrated."
        )
    else:
        explanation = (
            "This density/average-degree combination is outside the currently defined joint templates. "
            "You may want to add a custom interpretation for this specific mix."
        )

    return (
        f"Density = {density:.4f} (band: {density_band}), "
        f"Average degree = {average_degree:.4f} (band: {degree_band}). "
        f"{explanation}"
    )


def explain_overall_connectivity_and_collaboration_intensity(
    density: float,
    average_degree: float,
    average_strength_of_edges: float,
    weighted_density: float,
    include_section_context: bool = True,
):
    """
    Overall connectivity and collaboration intensity.

    Uses the provided threshold guide:
    - Density: [0.000, 0.010), [0.010, 0.050), [0.050, 0.150), [0.150, +inf)
    - Average degree: [0, 2), [2, 5), [5, 10), [10, +inf)
    - Average strength of edges: [1.00, 1.20), [1.20, 2.00), [2.00, 4.00), [4.00, +inf)
    - Weighted density: [0.000, 0.020), [0.020, 0.100), [0.100, 0.300), [0.300, +inf)
    """
    if density < 0:
        raise ValueError("Density cannot be negative.")
    if average_degree < 0:
        raise ValueError("Average degree cannot be negative.")
    if average_strength_of_edges < 0:
        raise ValueError("Average strength of edges cannot be negative.")
    if weighted_density < 0:
        raise ValueError("Weighted density cannot be negative.")

    # Band labels for reporting
    if density < 0.010:
        density_band = "very low"
    elif density < 0.050:
        density_band = "low"
    elif density < 0.150:
        density_band = "moderate"
    else:
        density_band = "high"

    if average_degree < 2:
        avg_degree_band = "very low"
    elif average_degree < 5:
        avg_degree_band = "low to moderate"
    elif average_degree < 10:
        avg_degree_band = "moderately high"
    else:
        avg_degree_band = "high"

    if average_strength_of_edges < 1.20:
        avg_strength_band = "very weak"
    elif average_strength_of_edges < 2.00:
        avg_strength_band = "low to moderate"
    elif average_strength_of_edges < 4.00:
        avg_strength_band = "strong repeated collaboration"
    else:
        avg_strength_band = "very strong repeated collaboration"

    if weighted_density < 0.020:
        weighted_density_band = "very low"
    elif weighted_density < 0.100:
        weighted_density_band = "low"
    elif weighted_density < 0.300:
        weighted_density_band = "moderate"
    else:
        weighted_density_band = "high"

    # 9 main outcomes (ordered from most specific/high-intensity down)
    if (
        density >= 0.150
        and average_degree >= 10
        and average_strength_of_edges > 4.00
        and weighted_density >= 0.300
    ):
        outcome = (
            "The co-authorship graph shows an exceptionally collaborative structure, with both very broad connectivity and "
            "very strong repeated collaboration. Researchers are highly interconnected across the institute, and the co-authorship "
            "ties that exist are reinforced through substantial repeated publication activity. This pattern is characteristic of a "
            "very cohesive research environment in which collaboration is both widespread and deeply embedded in the institution's "
            "academic culture."
        )
    elif (
        density >= 0.150
        and average_degree >= 10
        and average_strength_of_edges > 2.00
        and weighted_density >= 0.300
    ):
        outcome = (
            "The co-authorship graph shows high overall connectivity and high collaboration intensity. Collaboration is spread broadly "
            "across the institute, and the typical researcher works with many co-authors. At the same time, the ties in the network "
            "are strong and repeatedly reinforced, indicating that co-authorship relationships are not merely numerous but also substantial "
            "and sustained. Overall, this suggests a highly collaborative and cohesive institute, with both broad interaction and deep, "
            "stable research partnerships."
        )
    elif (
        density >= 0.150
        and average_degree >= 10
        and 1.20 <= average_strength_of_edges < 2.00
        and weighted_density >= 0.100
    ):
        outcome = (
            "The co-authorship graph shows high connectivity and moderate collaboration intensity. The institute appears broadly "
            "collaborative, with many realized co-authorship ties and a high average number of collaborators per researcher. In addition, "
            "the average strength of edges suggests that at least some of these collaborations are repeated, though not at an exceptionally "
            "high level. This indicates a well-integrated research environment in which collaboration is both widespread and reasonably sustained."
        )
    elif density >= 0.150 and average_degree >= 10 and average_strength_of_edges < 2.00:
        outcome = (
            "The co-authorship graph shows high overall connectivity, but relatively low collaboration intensity at the tie level. "
            "This means collaboration is spread widely across the institute, and researchers have many co-authors on average, which indicates "
            "a broadly collaborative environment. However, the average tie strength remains limited, suggesting that many of these collaborations "
            "are not strongly repeated. Overall, this points to a network in which collaboration is widespread, but often shallow or project-based "
            "rather than deeply reinforced."
        )
    elif (
        0.050 <= density < 0.150
        and 5 <= average_degree < 10
        and average_strength_of_edges > 2.00
        and weighted_density >= 0.100
    ):
        outcome = (
            "The co-authorship graph shows moderate connectivity with high collaboration intensity. Researchers are connected across a "
            "reasonable share of the institute, and the average author has a substantial number of collaborators. More importantly, the ties "
            "that exist appear to be relatively strong and repeatedly reinforced, suggesting that co-authorship relationships are stable rather "
            "than one-off. This pattern indicates an institute with solid collaboration breadth and particularly strong depth inside its working partnerships."
        )
    elif (
        0.050 <= density < 0.150
        and 5 <= average_degree < 10
        and 1.20 <= average_strength_of_edges < 2.00
        and 0.020 <= weighted_density < 0.300
    ):
        outcome = (
            "The co-authorship graph shows moderate overall connectivity and moderate collaboration intensity. Collaboration is spread across a "
            "meaningful portion of the institute, and the typical author works with a reasonable number of co-authors. At the same time, the existing "
            "ties show some repetition and reinforcement, though not at an extremely strong level. Overall, this suggests a healthy and reasonably "
            "collaborative research environment, where collaboration is neither highly fragmented nor exceptionally concentrated in a few repeated partnerships."
        )
    elif (
        0.050 <= density < 0.150
        and 5 <= average_degree < 10
        and average_strength_of_edges < 2.00
        and weighted_density < 0.150
    ):
        outcome = (
            "The co-authorship graph shows moderate connectivity, but relatively low collaboration intensity. Researchers appear to be connected "
            "across a reasonable part of the institute, and the average author collaborates with a meaningful number of colleagues. However, the "
            "average strength of ties remains limited, suggesting that many of these collaborations are light or occasional rather than deeply repeated. "
            "Overall, this points to a network that is fairly broad in reach, but not especially strong in long-term or repeated co-authorship intensity."
        )
    elif density < 0.050 and average_degree < 5 and average_strength_of_edges > 2.00:
        outcome = (
            "The co-authorship graph shows limited overall connectivity, but relatively strong collaboration intensity within the ties that do exist. "
            "This means collaboration is not broadly distributed across the institute, and researchers do not collaborate with a large number of different "
            "co-authors overall. However, the existing collaboration ties are fairly strong, suggesting that authors who do work together tend to publish "
            "repeatedly. This pattern is consistent with an institute organized around smaller, stable research teams rather than broad institute-wide collaboration."
        )
    elif (
        density < 0.050
        and average_degree < 5
        and average_strength_of_edges < 2.00
        and weighted_density < 0.100
    ):
        outcome = (
            "The co-authorship graph shows low overall connectivity and low collaboration intensity. Collaboration is not widely spread across the institute, "
            "and the typical author works with a relatively limited number of co-authors. In addition, the existing ties are not especially strong, which suggests "
            "that many collaborations are occasional rather than repeated. Overall, this points to a research environment in which collaboration is relatively sparse, "
            "localized, and not strongly reinforced over time."
        )
    else:
        outcome = (
            "This metric combination does not map cleanly to one of the predefined main outcomes. It suggests a mixed collaboration profile "
            "with signals that span different connectivity and intensity regimes."
        )

    metric_summary = (
        f"Density = {density:.4f} ({density_band}); "
        f"Average degree = {average_degree:.4f} ({avg_degree_band}); "
        f"Average strength of edges = {average_strength_of_edges:.4f} ({avg_strength_band}); "
        f"Weighted density = {weighted_density:.4f} ({weighted_density_band})."
    )

    if not include_section_context:
        return f"{metric_summary} {outcome}"

    section_measure = (
        "Overall connectivity and collaboration intensity describe how collaborative the co-authorship network is as a whole. "
        "Graph density and average degree reflect the breadth of collaboration, showing how widely researchers are connected and "
        "how many co-authors the typical author has. Weighted density and average strength of edges reflect the intensity of collaboration, "
        "showing whether existing co-authorship ties are light and occasional or strong and repeatedly reinforced. Taken together, these metrics "
        "indicate whether the institute's research network is sparse or well connected, and whether its collaborations are mostly shallow or sustained over time."
    )
    how_to_read = (
        "Density + average degree indicate how broadly collaboration is spread. "
        "Average strength of edges + weighted density indicate how deep and repeated collaboration is."
    )

    return f"{section_measure} {how_to_read} {metric_summary} {outcome}"


def explain_modularity_and_network_segmentation(
    number_of_communities: int,
    total_nodes: int,
    modularity: float,
    average_community_density: float,
    include_section_context: bool = True,
):
    """
    Modularity and network segmentation.
    """
    if total_nodes <= 0:
        raise ValueError("Total nodes must be > 0.")
    if number_of_communities < 0:
        raise ValueError("Number of communities cannot be negative.")
    if average_community_density < 0:
        raise ValueError("Average community density cannot be negative.")

    community_ratio = number_of_communities / total_nodes

    if community_ratio < 0.050:
        community_band = "few communities"
    elif community_ratio <= 0.150:
        community_band = "moderate number of communities"
    else:
        community_band = "many communities"

    if modularity < 0.20:
        modularity_band = "low modularity"
    elif modularity <= 0.40:
        modularity_band = "moderate modularity"
    else:
        modularity_band = "high modularity"

    if average_community_density < 0.10:
        density_band = "low community density"
    elif average_community_density <= 0.30:
        density_band = "moderate community density"
    else:
        density_band = "high community density"

    # 9 requested outcomes (ordered from most specific to broad)
    if modularity > 0.60 and average_community_density > 0.60 and community_ratio >= 0.050:
        outcome = (
            "The co-authorship graph shows very strong segmentation with highly cohesive internal communities. The detected groups "
            "are not only clearly separated from one another, but also very tightly connected inside. In the context of an institute, "
            "this suggests a collaboration structure dominated by strong and internally integrated research clusters, with relatively "
            "little mixing between different parts of the network."
        )
    elif community_ratio < 0.050 and modularity < 0.20 and average_community_density < 0.10:
        outcome = (
            "The co-authorship graph shows limited network segmentation. The network is divided into only a small number of communities, "
            "and those communities are not strongly separated from one another. In addition, their internal density is low, which suggests "
            "that even within the detected groups, collaboration is relatively loose. Overall, this points to a research network that is only "
            "weakly structured into communities and may be better described as broadly mixed rather than clearly segmented."
        )
    elif community_ratio < 0.050 and modularity > 0.40 and average_community_density > 0.30:
        outcome = (
            "The co-authorship graph shows a small number of clearly defined research blocs. Although the network is not split into many "
            "communities, the communities that do exist are strongly separated from one another and internally cohesive. In a co-authorship "
            "context, this suggests the institute is organized around a few major collaboration clusters, each of which contains strong "
            "internal collaboration but limited interaction across clusters."
        )
    elif 0.050 <= community_ratio <= 0.150 and modularity < 0.40 and average_community_density < 0.30:
        outcome = (
            "The co-authorship graph shows some segmentation into multiple communities, but the boundaries between them are not especially strong. "
            "The institute appears to contain several research groups, but these groups are only moderately distinct and are not highly cohesive "
            "internally. This suggests a collaboration structure in which communities exist, but they are relatively loose and still connected "
            "through substantial cross-group collaboration."
        )
    elif 0.050 <= community_ratio <= 0.150 and 0.20 <= modularity <= 0.40 and average_community_density >= 0.10:
        outcome = (
            "The co-authorship graph shows a balanced level of network segmentation. The institute is divided into a noticeable number of communities, "
            "and these communities are moderately distinct from one another. Their internal density suggests that collaboration within groups is meaningful, "
            "though not extremely tight. Overall, this points to a research environment with recognizable collaboration clusters, but also with some "
            "continued interaction across community boundaries."
        )
    elif 0.050 <= community_ratio <= 0.150 and modularity > 0.40 and average_community_density > 0.30:
        outcome = (
            "The co-authorship graph shows clear and well-formed network segmentation. The institute is divided into several communities that are strongly "
            "separated from one another, and these communities are also internally cohesive. In a co-authorship setting, this suggests a structured research "
            "environment composed of well-defined collaboration groups, where internal teamwork is strong and cross-group collaboration is more limited."
        )
    elif community_ratio > 0.150 and modularity < 0.20 and average_community_density < 0.10:
        outcome = (
            "The co-authorship graph appears to contain many small communities, but without strong structural separation or internal cohesion. This means the "
            "community detection method has identified numerous groups, yet these groups are neither sharply distinct nor tightly connected inside themselves. "
            "In practice, this can indicate a fragmented or noisy network structure rather than a truly organized system of strong research communities."
        )
    elif community_ratio > 0.150 and modularity > 0.40 and average_community_density < 0.30:
        outcome = (
            "The co-authorship graph shows high segmentation into many distinct communities, but the communities themselves are not especially dense internally. "
            "This suggests that the institute is divided into numerous research groups that are structurally separate, yet each group may be relatively small, "
            "specialized, or loosely connected inside. In a co-authorship context, this points to a highly segmented academic environment with clear boundaries "
            "between groups but less intensive collaboration within each one."
        )
    elif community_ratio > 0.150 and modularity > 0.40 and average_community_density > 0.30:
        outcome = (
            "The co-authorship graph shows strong network segmentation into many cohesive communities. The institute appears to be organized into a large number "
            "of clearly separated research groups, and these groups are also internally collaborative. This pattern suggests a highly structured collaboration "
            "landscape in which researchers work within distinct, tightly knit communities, with limited collaboration across them."
        )
    else:
        outcome = (
            "This combination of community ratio, modularity, and average community density does not map exactly to one of the predefined segmentation outcomes. "
            "It suggests a mixed or transitional community structure."
        )

    summary = (
        f"Number of communities = {number_of_communities} (ratio = {community_ratio:.4f}, {community_band}); "
        f"Modularity = {modularity:.4f} ({modularity_band}); "
        f"Average community density = {average_community_density:.4f} ({density_band})."
    )

    if not include_section_context:
        return f"{summary} {outcome}"

    section_measure = (
        "Modularity and network segmentation describe how clearly the co-authorship network is divided into communities and how cohesive those communities are internally."
    )
    how_to_read = (
        "Community ratio indicates how many groups the network is split into, modularity indicates how strongly separated those groups are, "
        "and average community density indicates how strongly authors collaborate inside each group."
    )

    return f"{section_measure} {how_to_read} {summary} {outcome}"


def explain_inequality_of_roles_and_dependence_on_key_authors(
    hub_dominance_ratio: float,
    average_betweenness: float,
    include_section_context: bool = True,
):
    """
    Inequality of roles and dependence on key authors.

    Inputs:
    - hub_dominance_ratio: R_h
    - average_betweenness: average normalized betweenness indicator
    """
    if hub_dominance_ratio < 0:
        raise ValueError("Hub dominance ratio cannot be negative.")
    if average_betweenness < 0:
        raise ValueError("Average betweenness cannot be negative.")

    # Bands for reporting
    if hub_dominance_ratio < 1.5:
        hub_band = "low hub dominance"
    elif hub_dominance_ratio < 3.0:
        hub_band = "moderate hub dominance"
    elif hub_dominance_ratio <= 6.0:
        hub_band = "strong hub dominance"
    else:
        hub_band = "very strong hub dominance"

    if average_betweenness < 0.010:
        bet_band = "very low betweenness dependence"
    elif average_betweenness < 0.050:
        bet_band = "moderate betweenness dependence"
    elif average_betweenness <= 0.150:
        bet_band = "high betweenness dependence"
    else:
        bet_band = "very high betweenness dependence"

    # 9 requested outcomes (ordered to resolve overlap)
    if hub_dominance_ratio > 6.0 and average_betweenness > 0.150:
        outcome = (
            "The co-authorship graph shows very strong inequality of roles and heavy dependence on key authors. The most connected "
            "authors are far more collaborative than the average researcher, and the strongest bridging authors are extremely important "
            "in linking different parts of the network. This indicates a highly centralized collaboration structure in which a small "
            "number of researchers dominate both collaboration reach and structural connectivity. While this may reflect strong leadership "
            "or institutional prominence, it also suggests vulnerability, since the loss of these authors could significantly weaken "
            "cross-network collaboration."
        )
    elif 3.0 <= hub_dominance_ratio <= 6.0 and 0.050 <= average_betweenness <= 0.150:
        outcome = (
            "The co-authorship graph shows strong inequality of roles and substantial dependence on key authors. A small set of authors "
            "has much broader collaboration reach than the rest of the network, and these authors or others like them also appear to play "
            "important bridging roles between communities. In co-authorship terms, this suggests that the institute's collaboration structure "
            "is shaped heavily by a limited group of central researchers, who likely influence both collaboration breadth and cross-group connectivity."
        )
    elif hub_dominance_ratio > 3.0 and 0.010 <= average_betweenness < 0.050:
        outcome = (
            "The co-authorship graph shows clear inequality in who collaborates most broadly, but only moderate dependence on authors as brokers. "
            "A small group of researchers acts as major collaboration hubs, yet the network is not overwhelmingly dependent on them to connect its "
            "different parts. This pattern suggests a hierarchy in collaboration activity, where some authors are much more active than others, but "
            "the network still retains a degree of structural resilience."
        )
    elif hub_dominance_ratio > 3.0 and average_betweenness < 0.010:
        outcome = (
            "The co-authorship graph shows strong inequality in collaboration breadth, but weaker dependence on bridging roles. This means a small "
            "number of authors collaborates with far more colleagues than the average researcher, so they act as major hubs in the network. However, "
            "the relatively low average betweenness suggests that these authors are not the only important connectors between communities. In practice, "
            "the institute appears collaboration-rich around a few highly active authors, but not fully structurally dependent on them as brokers."
        )
    elif 1.5 <= hub_dominance_ratio < 3.0 and average_betweenness > 0.050:
        outcome = (
            "The co-authorship graph shows moderate inequality in collaboration breadth, but stronger inequality in strategic positioning. "
            "The most connected authors are more collaborative than average, though not overwhelmingly so, while the main bridging authors play "
            "a much more important role in linking communities. In practical terms, this suggests that the institute's dependence on key researchers "
            "comes less from raw collaboration volume and more from the fact that a few authors connect otherwise separated research groups."
        )
    elif 1.5 <= hub_dominance_ratio < 3.0 and 0.010 <= average_betweenness < 0.050:
        outcome = (
            "The co-authorship graph shows moderate inequality of roles and a moderate level of dependence on central authors. The most connected "
            "authors collaborate with more colleagues than average, and the most important bridging authors also contribute noticeably to linking "
            "different parts of the network. This suggests that the institute contains a visible set of more influential researchers, but the network "
            "is not so concentrated that it depends overwhelmingly on only a few individuals."
        )
    elif 1.5 <= hub_dominance_ratio < 3.0 and average_betweenness < 0.010:
        outcome = (
            "The co-authorship graph shows some inequality in collaboration reach, but only limited dependence on bridging authors. A small group "
            "of authors collaborates with more colleagues than average, indicating moderate hub formation, yet the network does not appear strongly "
            "reliant on a few brokers to connect different communities. This suggests that some researchers are more prominent in terms of collaboration "
            "breadth, but the network remains relatively stable and not overly dependent on them for overall connectivity."
        )
    elif hub_dominance_ratio < 1.5 and average_betweenness > 0.050:
        outcome = (
            "The co-authorship graph shows limited inequality in collaboration volume, but substantial dependence on key bridging authors. "
            "The most connected authors are not vastly more collaborative than the average researcher, yet a small number of authors still play "
            "an important role in linking different parts of the network. In a co-authorship setting, this suggests that role inequality comes "
            "less from having many collaborators and more from occupying strategically important positions between research groups."
        )
    elif hub_dominance_ratio < 1.5 and average_betweenness < 0.010:
        outcome = (
            "The co-authorship graph shows low inequality of roles and limited dependence on key authors. The most connected authors are not "
            "dramatically more collaborative than the average researcher, and the strongest bridging authors do not appear to dominate the links "
            "between different parts of the network. In co-authorship terms, this suggests that collaboration roles are relatively balanced across "
            "the institute, with no strong structural reliance on a small elite group of central authors."
        )
    else:
        outcome = (
            "This hub-dominance/betweenness combination does not map exactly to one of the predefined role-inequality outcomes. "
            "It suggests a mixed profile between collaboration reach inequality and broker dependence."
        )

    summary = (
        f"Hub dominance ratio (R_h) = {hub_dominance_ratio:.4f} ({hub_band}); "
        f"Average betweenness = {average_betweenness:.4f} ({bet_band})."
    )

    if not include_section_context:
        return f"{summary} {outcome}"

    section_measure = (
        "Inequality of roles and dependence on key authors describe whether collaboration is balanced across researchers or concentrated in a small set of central actors."
    )
    how_to_read = (
        "R_h captures inequality in collaboration breadth (how much more connected top hub authors are), while average betweenness captures dependence on key brokers "
        "for cross-community connectivity."
    )

    return f"{section_measure} {how_to_read} {summary} {outcome}"


def _run_combined_sections_with_project_data(
    top_percent: float = 5.0,
    hub_threshold: float = 95.0,
) -> None:
    """
    Run only the three combined explanation sections using real project data.
    """
    from Scripts.analytics.betweenness_centrality_detection import detect_betweenness_centrality
    from Scripts.analytics.community_detection import average_community_density, find_communities
    from Scripts.analytics.hub_detection import average_hub_metric, detect_hubs
    from Scripts.analytics.metrics.metrics_calculator import (
        compute_average_normalized_strength_of_edges,
        compute_average_per_node,
        compute_graph_density,
        compute_graph_weighted_density,
    )
    from Scripts.graph.build_networkx_graph import (
        find_largest_connected_component,
        get_subgraph_from_component_nodes,
        load_graph_from_edges_csv,
    )

    base_graph = load_graph_from_edges_csv()
    lcc_nodes = find_largest_connected_component(base_graph)
    if not lcc_nodes:
        raise ValueError("Largest connected component could not be computed from project data.")
    lcc_graph = get_subgraph_from_component_nodes(base_graph, lcc_nodes)

    # Inputs for overall connectivity and collaboration intensity (whole graph)
    density = compute_graph_density(lcc_graph)
    weighted_density = compute_graph_weighted_density(lcc_graph)
    average_strength_of_edges = compute_average_normalized_strength_of_edges(lcc_graph)
    average_degree_whole, _ = compute_average_per_node(lcc_graph, "degree")

    # Inputs for modularity and network segmentation (LCC communities)
    modularity, number_of_communities, partition = find_communities(lcc_graph, "Newman")
    avg_comm_density = average_community_density(partition)
    total_nodes_lcc = lcc_graph.number_of_nodes()

    # Inputs for inequality of roles and dependence on key authors (LCC hubs + betweenness)
    average_degree_lcc, _ = compute_average_per_node(lcc_graph, "degree")
    hubs = detect_hubs(lcc_graph, metric="degree", threshold=hub_threshold)
    avg_hub_degree = average_hub_metric(hubs)
    hub_dominance_ratio = (avg_hub_degree / average_degree_lcc) if average_degree_lcc > 0 else 0.0
    betweenness_top = detect_betweenness_centrality(lcc_graph, top_percent=top_percent)
    average_betweenness = (
        sum(betweenness_top.values()) / len(betweenness_top) if betweenness_top else 0.0
    )

    print("=== Combined Sections (Real Project Data) ===\n")

    print("[Overall connectivity and collaboration intensity]")
    print(
        explain_overall_connectivity_and_collaboration_intensity(
            density=density,
            average_degree=average_degree_whole,
            average_strength_of_edges=average_strength_of_edges,
            weighted_density=weighted_density,
        )
    )
    print()

    print("[Modularity and network segmentation]")
    print(
        explain_modularity_and_network_segmentation(
            number_of_communities=number_of_communities,
            total_nodes=total_nodes_lcc,
            modularity=modularity,
            average_community_density=avg_comm_density,
        )
    )
    print()

    print("[Inequality of roles and dependence on key authors]")
    print(
        explain_inequality_of_roles_and_dependence_on_key_authors(
            hub_dominance_ratio=hub_dominance_ratio,
            average_betweenness=average_betweenness,
        )
    )
    print()


if __name__ == "__main__":
    _run_combined_sections_with_project_data()

