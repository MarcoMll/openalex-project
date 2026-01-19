from pyvis.network import Network
import networkx as nx

def generate_interactive_graph(nx_graph: nx.Graph, output_path: str = "interactive_graph.html"):
    # Initialize the PyVis network
    # height/width: Canvas size
    # bgcolor/font_color: Dark mode theme for better visibility
    net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white", select_menu=True)
    
    # Pre-process nodes for better interactivity
    # We add 'title' for hover tooltips and 'value' for node sizing
    degrees = dict(nx_graph.degree())
    strengths = dict(nx_graph.degree(weight="weight"))

    for node in nx_graph.nodes():
        deg = degrees[node]
        strg = strengths.get(node, 0)
        
        # Set attributes PyVis looks for
        nx_graph.nodes[node]['value'] = deg  # Larger degree = Larger node
        nx_graph.nodes[node]['title'] = (
            f"<b>Author ID:</b> {node}<br>"
            f"<b>Degree:</b> {deg}<br>"
            f"<b>Strength:</b> {strg:.2f}"
        )
        nx_graph.nodes[node]['label'] = str(node) # Text shown on the node

    # Pre-process edges to show weight thickness
    for u, v, data in nx_graph.edges(data=True):
        if 'weight' in data:
            data['value'] = data['weight'] # Thicker line for higher weight
            data['title'] = f"Weight: {data['weight']}"

    # Import the enriched NetworkX graph
    net.from_nx(nx_graph)
    
    # Enable physics controls so you can manipulate the layout in real-time
    net.show_buttons(filter_=['physics'])
    
    # Save the file
    print(f"Generating interactive graph at: {output_path}")
    net.write_html(output_path)