import csv
import networkx as nx
from typing import Literal

def find_communities(graph, algorith_type: Literal["Newman", "Louvain"] = "Newman"):
    if algorith_type == "Newman":
        return newman_greedy(graph)
    else:
        raise ValueError("Louvain algorithm is not supported yet.")

def newman_greedy(graph: nx.Graph):
    edges_list = list(graph.edges(data=True)) # [('A', 'B', {'weight': 5}), ('A', 'C', {'weight': 2})]
    edges_lookup_dict = {}

    for edge in edges_list: # creating a fast lookup of edges
        u = edge[0]
        v = edge[1]
        w = edge[2]["weight"]

        if u not in edges_lookup_dict:
            edges_lookup_dict[u] = {}
        if v not in edges_lookup_dict:
            edges_lookup_dict[v] = {}

        edges_lookup_dict[u][v] = float(w) # {A: {B: 5, C:4}}
        edges_lookup_dict[v][u] = float(w) # {B: {A:5, D:2}}

    nodes_set = set(graph.nodes()) # set of nodes with no duplicates

    nodes_degree_dict = {}
    for node in nodes_set:
        weight_sum = sum(edges_lookup_dict[node].values())
        nodes_degree_dict[node] = weight_sum

    L = sum(nodes_degree_dict[node] for node in nodes_set) / 2 # divide by 2 because each undirected edge is counted twice

    communities_dict = {}
    community_of_node = {}

    # initialize each node is its own community
    for node in nodes_set:
        community_id = node  # simplest id strategy for now

        community_of_node[node] = community_id
        communities_dict[community_id] = {
            "nodes": {node},  # set[node]
            "k_c": nodes_degree_dict[node],  # community strength
            "L_c": 0.0,  # internal weight
        }

    Q = calculate_community_modularity(L, communities_dict)

    current_Q = Q
    best_Q = Q
    best_partition = clone_partition(communities_dict)
    merge_counter = 0

    while True:
        community_ids = list(communities_dict.keys())
        if len(community_ids) <= 1:
            break

        iteration_best_Q = current_Q
        iteration_best_partition = None

        for i in range(len(community_ids)):
            for j in range(i + 1, len(community_ids)):
                cid_x = community_ids[i]
                cid_y = community_ids[j]

                community_x = communities_dict[cid_x]
                community_y = communities_dict[cid_y]

                e_xy = calculate_intercommunity_weight(
                    community_x["nodes"],
                    community_y["nodes"],
                    edges_lookup_dict
                )

                merged_id = f"merge_{merge_counter}_{i}_{j}"
                merged_piece = merge_communities(community_x, community_y, merged_id, e_xy)

                candidate_partition = clone_partition(communities_dict)
                del candidate_partition[cid_x]
                del candidate_partition[cid_y]
                candidate_partition.update(merged_piece)

                candidate_Q = calculate_community_modularity(L, candidate_partition)

                if candidate_Q > iteration_best_Q:
                    iteration_best_Q = candidate_Q
                    iteration_best_partition = candidate_partition

        # no improving merge -> stop
        if iteration_best_partition is None:
            break

        communities_dict = iteration_best_partition
        current_Q = iteration_best_Q
        merge_counter += 1

        if current_Q > best_Q:
            best_Q = current_Q
            best_partition = clone_partition(communities_dict)

    ''' output example:
    (0.7, -> Q value of the best partition
    
    12, -> number of communities
    
    best_partition = { 
        "merge_22_36_66": {
            "nodes": {
                "https://openalex.org/A5064682864",
                "https://openalex.org/A5004319715"
            },
            "k_c": 17.0,
            "L_c": 8.0
        },
        ...
    })
    '''

    return best_Q, (len(nodes_set) - merge_counter), best_partition

def calculate_community_modularity(L: int, c):
    if L <= 0:
        raise ValueError("L = 0 (or less), division by zero is not allowed.")

    c_sum = 0

    for community in c.values():
        L_c = community["L_c"]
        k_c = community["k_c"]
        c_sum += L_c - (k_c**2) / (4 * L)

    return (1/L) * c_sum

def clone_partition(partition: dict):
    return {
        cid: {
            "nodes": set(data["nodes"]),
            "k_c": float(data["k_c"]),
            "L_c": float(data["L_c"]),
        }
        for cid, data in partition.items()
    }

def calculate_intercommunity_weight(nodes_x: set, nodes_y: set, edges_lookup_dict: dict) -> float:
    total = 0.0
    for u in nodes_x:
        neighbors = edges_lookup_dict.get(u, {})
        for v in nodes_y:
            total += neighbors.get(v, 0.0)
    return total

def merge_communities(community_x, community_y, new_id, e_xy: float):
    nodes = community_x["nodes"] | community_y["nodes"]
    k_xy = community_x["k_c"] + community_y["k_c"]
    L_xy = community_x["L_c"] + community_y["L_c"] + e_xy
    return {new_id: {"nodes": nodes, "k_c": k_xy, "L_c": L_xy}}



def compute_average_community_density(newman_output):
    """
    uses Newman_greedy output to calculate the average density of communities
    """
    if not newman_output:
        return 0.0

    communities_dict = newman_output
  

    total_density = 0.0
    counted = 0

    for community in communities_dict.values():
        nodes = community.get("nodes", set())
        n = len(nodes)
        if n < 2:
            continue

        internal_weight = float(community.get("L_c", 0.0))
        possible_edges = n * (n - 1) / 2
        density = internal_weight / possible_edges if possible_edges > 0 else 0.0

        total_density += density
        counted += 1

    return total_density / counted if counted else 0.0

