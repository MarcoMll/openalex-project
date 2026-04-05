# acts as a single source of truth for project navigation
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


def find_project_root(start: Path | None = None, markers: Iterable[str] = ("pyproject.toml", ".git")) -> Path:
    p = (start or Path(__file__).resolve()).parent
    for candidate in (p, *p.parents):
        if any((candidate / m).exists() for m in markers):
            return candidate
    raise RuntimeError(f"Could not find project root (looked for: {list(markers)}).")


@dataclass(frozen=True)
class ProjectPaths:
    ROOT: Path
    DATA: Path
    RAW_DIR: Path
    DERIVED_DIR: Path
    ANALYTICS_DIR: Path

    RAW_AUTHORS: Path
    RAW_WORKS: Path

    DERIVED_WORKS: Path
    HYPEREDGES: Path
    EDGES_CSV: Path

    ASSETS_DIR: Path
    IMAGES_DIR: Path
    GRAPHS_DIR: Path


def get_paths(project_root: Path | None = None) -> ProjectPaths:
    root = project_root or find_project_root()
    data = root / "Data"
    raw = data / "Raw"
    derived = data / "Derived"
    analytics = data / "Analytics"
    assets = root / "Assets"
    images = assets / "Images"
    graphs = assets / "Graphs"

    return ProjectPaths(
        ROOT=root,
        DATA=data,
        RAW_DIR=raw,
        DERIVED_DIR=derived,
        ANALYTICS_DIR=analytics,
        ASSETS_DIR=assets,
        IMAGES_DIR=images,
        GRAPHS_DIR=graphs,
        RAW_AUTHORS=raw / "raw_authors.jsonl",
        RAW_WORKS=raw / "raw_works.jsonl",
        DERIVED_WORKS=derived / "derived_works.jsonl",
        HYPEREDGES=derived / "hyperedges.jsonl",
        EDGES_CSV=derived / "edges.csv",
    )