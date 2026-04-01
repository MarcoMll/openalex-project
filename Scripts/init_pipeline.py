import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from pipeline.fetch_raw_data import fetch_raw_data_from_api
from pipeline.derive_data import derive_raw_data
from graph.build_networkx_graph import build_network_graph
from dataclasses import dataclass

@dataclass
class PipelineConfig:
    institution_id: str
    api_email: str
    api_key: str

pipeline_config = PipelineConfig(
    institution_id="i56441308",
    api_email="marcomalliani@gmail.com",
    api_key="oICxPdw6eeP6UJGK6xtQB1",
)

if __name__ == "__main__":
    fetch_raw_data_from_api(pipeline_config)
    derive_raw_data()
    build_network_graph()