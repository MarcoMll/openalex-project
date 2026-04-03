from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from typing import Union

from PIL import Image

DEFAULT_FRAME_DURATION_MS = 120
DEFAULT_DISPLAY_SIZE_PX = 44


def _to_data_uri(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    suffix = path.suffix.lower()
    if suffix == ".png":
        mime = "image/png"
    elif suffix in {".jpg", ".jpeg"}:
        mime = "image/jpeg"
    else:
        mime = "application/octet-stream"
    return f"data:{mime};base64,{encoded}"


def _collect_non_empty_frames(image: Image.Image, cols: int, rows: int, px: int) -> list[tuple[int, int]]:
    """
    Return sprite cell coordinates that contain at least one visible pixel.
    For non-alpha images we keep all frames to avoid false positives.
    """
    if "A" not in image.getbands():
        return [(col, row) for row in range(rows) for col in range(cols)]

    alpha = image.getchannel("A")
    non_empty_frames: list[tuple[int, int]] = []

    for row in range(rows):
        for col in range(cols):
            left = col * px
            top = row * px
            right = left + px
            bottom = top + px
            if alpha.crop((left, top, right, bottom)).getbbox() is not None:
                non_empty_frames.append((col, row))

    return non_empty_frames


def _keyframes(animation_name: str, frames: list[tuple[int, int]], step_px: int) -> str:
    total_frames = len(frames)
    if total_frames <= 1:
        return (
            f"@keyframes {animation_name} {{"
            f"  0% {{ background-position: 0 0; }}"
            f"  100% {{ background-position: 0 0; }}"
            f"}}"
        )

    rules = [f"@keyframes {animation_name} {{"]
    for frame_index, (col, row) in enumerate(frames):
        x = -col * step_px
        y = -row * step_px
        pct = (frame_index / (total_frames - 1)) * 100
        rules.append(f"  {pct:.4f}% {{ background-position: {x}px {y}px; }}")
    rules.append("}")
    return "\n".join(rules)


def play_spritesheet_animation(
    spritesheet: Union[str, Path],
    px: int,
    speed: int | None = None,
    *,
    class_name: str = ".sprite-bar-chart",
    display_size_px: int = DEFAULT_DISPLAY_SIZE_PX,
) -> str:
    """
    Build CSS that plays a spritesheet animation.

    Args:
        spritesheet: Path to spritesheet image.
        px: Size of one cell/frame in source image pixels.
        speed: Frame duration in milliseconds. Defaults to DEFAULT_FRAME_DURATION_MS.
        class_name: CSS selector to bind the animation to.
        display_size_px: Rendered frame size in CSS pixels.
    """
    image_path = Path(spritesheet)
    if px <= 0:
        raise ValueError("px must be > 0")
    if display_size_px <= 0:
        raise ValueError("display_size_px must be > 0")

    frame_duration_ms = DEFAULT_FRAME_DURATION_MS if speed is None else max(20, int(speed))

    with Image.open(image_path) as image:
        sprite_w, sprite_h = image.size
        processed = image.convert("RGBA")

    cols = max(1, sprite_w // px)
    rows = max(1, sprite_h // px)
    frame_positions = _collect_non_empty_frames(processed, cols=cols, rows=rows, px=px)
    if not frame_positions:
        frame_positions = [(0, 0)]

    total_frames = len(frame_positions)
    total_duration_ms = total_frames * frame_duration_ms

    # Unique animation id prevents stale browser style caching when px/speed changes.
    identity = f"{image_path}:{px}:{frame_duration_ms}:{display_size_px}:{cols}:{rows}:{frame_positions}"
    digest = hashlib.sha1(identity.encode("utf-8")).hexdigest()[:10]
    animation_name = f"bar_chart_sprite_{digest}"

    data_uri = _to_data_uri(image_path)
    frames_css = _keyframes(animation_name=animation_name, frames=frame_positions, step_px=display_size_px)

    return f"""
{class_name} {{
  width: {display_size_px}px;
  height: {display_size_px}px;
  background-image: url("{data_uri}");
  background-repeat: no-repeat;
  background-position: 0 0;
  background-size: {cols * display_size_px}px {rows * display_size_px}px;
  animation: {animation_name} {total_duration_ms}ms steps(1, end) infinite;
}}
{frames_css}
"""
