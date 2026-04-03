import sys
from pathlib import Path
from typing import Callable

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


def _emit_status(on_status: Callable[[str], None] | None, message: str) -> None:
    if on_status is not None:
        on_status(message)


def init_pipeline(pipeline_config: PipelineConfig, on_status: Callable[[str], None] | None = None) -> None:
    fetch_raw_data_from_api(pipeline_config, on_status=on_status)
    _emit_status(on_status, "Deriving data")
    derive_raw_data()
    _emit_status(on_status, "Building graphs")
    build_network_graph()
    _emit_status(on_status, "Completed")

if __name__ == "__main__":
    pipeline_config = PipelineConfig(
        institution_id="",
        api_email="",
        api_key="",
    )
    init_pipeline(pipeline_config)
