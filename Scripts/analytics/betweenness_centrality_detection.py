import networkx

import sys
from itertools import islice
from pathlib import Path
import math

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def detect_betweenness_centrality(graph, top_percent=5.0):

    G = graph
    nodes = G.nodes()
    
    if len(nodes) < 3:
        raise ValueError("Graph must have at least 3 nodes to compute betweenness centrality.") # Not enough nodes to compute betweenness centrality     
    
    seen_pairs = set()
    betweenness = {node: 0.0 for node in G.nodes()}
    num_nodes = G.number_of_nodes()
    scale = 2.0 / ((num_nodes - 1) * (num_nodes - 2))

    for n in nodes:
        
        connected_component = networkx.node_connected_component(G, n)
        target = connected_component - {n}
        
        for c in target:
            pair = frozenset((n, c))   # undirected pair used because needed a immutable varible for dict key and cba to do sorted tuple
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            shortest_paths = list(networkx.all_shortest_paths(G, source=n, target=c))
            sigma_st = len(shortest_paths) #total number of shortest paths between n and c

            for path in shortest_paths:
                for v in path[1:-1]:   # exclude endpoints n and c
                    betweenness[v] += (1.0 / sigma_st) * scale
    
    # betweenness: {node: score}
    items = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)

    percent = top_percent  # top percent
    k = max(1, math.ceil(len(items) * (percent / 100.0)))

    top_nodes = dict(items[:k]) 
    return top_nodes