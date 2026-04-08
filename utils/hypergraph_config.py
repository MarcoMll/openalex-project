from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _is_hex_color(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    if len(value) not in (7, 9) or not value.startswith("#"):
        return False
    return all(char in "0123456789abcdefABCDEF" for char in value[1:])


@dataclass
class HypergraphConfig:
    seed: int = 777
    node_size: int = 15
    node_color: str = "#63c791"
    group_size_colors: dict[int, str] = field(
        default_factory=lambda: {
            2: "#cfd6e0",
            3: "#4DA3FF",
            4: "#8E44AD",
            5: "#E6194B",
            6: "#E6194B",
        }
    )

    def __post_init__(self) -> None:
        normalized: dict[int, str] = {}
        for raw_size, raw_color in self.group_size_colors.items():
            size = int(raw_size)

            if size < 2:
                raise ValueError("HypergraphConfig.group_size_colors keys must be >= 2.")
            if not _is_hex_color(raw_color):
                raise ValueError(
                    f"HypergraphConfig.group_size_colors[{size}] must be a HEX color."
                )
            normalized[size] = raw_color

        self.group_size_colors = dict(sorted(normalized.items()))

    @property
    def max_group_size(self) -> int:
        return max(self.group_size_colors.keys())

    def color_for_group_size(self, size: int) -> str:
        try:
            resolved_size = int(size)
        except (TypeError, ValueError) as error:
            raise ValueError(f"Invalid group size: {size}") from error

        if resolved_size in self.group_size_colors:
            return self.group_size_colors[resolved_size]

        if resolved_size > self.max_group_size:
            return self.group_size_colors[self.max_group_size]

        lower_sizes = [s for s in self.group_size_colors.keys() if s < resolved_size]
        if lower_sizes:
            return self.group_size_colors[max(lower_sizes)]

        return self.node_color

    def label_for_group_size(self, size: int) -> str:
        resolved_size = int(size)
        if resolved_size >= self.max_group_size:
            return f"groups of size {self.max_group_size}+"
        return f"groups of size {resolved_size}"

    @classmethod
    def from_dict(cls, payload: Any) -> "HypergraphConfig":
        if not isinstance(payload, dict):
            return cls()

        return cls(
            seed=payload.get("seed", cls.seed),
            node_size=payload.get("node_size", cls.node_size),
            node_color=payload.get("node_color", cls.node_color),
            group_size_colors=payload.get("group_size_colors", cls().group_size_colors),
        )
