from pathlib import Path
import os
import webbrowser
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from pyvis.network import Network
import networkx as nx

from utils.project_paths import get_paths

P = get_paths()
GRAPHS_DIR = Path(P.GRAPHS_DIR)
IMAGES_DIR = Path(P.IMAGES_DIR)

def save_graph_screenshot(html_path, output_dir=IMAGES_DIR, filename="graph_preview.png"):
   # 1. Create the directory if it doesn't exist
    target_path = Path(output_dir)
    target_path.mkdir(parents=True, exist_ok=True)
    
    # 2. Define the full save path
    save_to = target_path / filename

    # 3. Setup Selenium (Headless)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), 
        options=chrome_options
    )

    # 4. Load and Capture
    full_html_path = "file://" + os.path.abspath(html_path)
    driver.get(full_html_path)
    
    print(f"Stabilizing graph for 5 seconds...")
    time.sleep(5) 

    # 5. Save using the new path
    driver.save_screenshot(str(save_to))
    driver.quit()
    
    print(f"Preview saved to: {save_to}")
    return str(save_to)

def generate_interactive_graph(nx_graph: nx.Graph, graph_name: str = "interactive_graph.html"):
    net = Network(
        height="750px",
        width="100%",
        bgcolor="#222222",
        font_color="white",
        select_menu=True,
        cdn_resources="local",  # make explicit; local => needs lib/
    )

    degrees = dict(nx_graph.degree())
    strengths = dict(nx_graph.degree(weight="weight"))

    for node in nx_graph.nodes():
        deg = degrees[node]
        strg = strengths.get(node, 0)

        nx_graph.nodes[node]["value"] = deg
        nx_graph.nodes[node]["title"] = (
            f"<b>Author ID:</b> {node}<br>"
            f"<b>Degree:</b> {deg}<br>"
            f"<b>Strength:</b> {strg:.2f}"
        )
        nx_graph.nodes[node]["label"] = str(node)

    for u, v, data in nx_graph.edges(data=True):
        if "weight" in data:
            data["value"] = data["weight"]
            data["title"] = f"Weight: {data['weight']}"

    net.from_nx(nx_graph)
    net.show_buttons(filter_=["physics"])

    # Ensure output dir exists
    GRAPHS_DIR.mkdir(parents=True, exist_ok=True)

    # Force PyVis to create ./lib next to the HTML by changing CWD temporarily
    old_cwd = os.getcwd()
    os.chdir(GRAPHS_DIR)
    try:
        print(f"Generating interactive graph at: {GRAPHS_DIR / graph_name}")
        net.write_html(graph_name)  # NOTE: just the filename now
    finally:
        os.chdir(old_cwd)
    
    html_file_path = GRAPHS_DIR / graph_name
    
    save_graph_screenshot(
        html_path=html_file_path, 
        output_dir=IMAGES_DIR, 
        filename="graph_preview.png"
    )
    webbrowser.open(f"file://{GRAPHS_DIR / graph_name}")