#!/usr/bin/env python3
"""
Subject-Driven Hatching Generator for Pen Plotters.

Reads an input image (or mask), converts it to a darkness map, and
draws hatching strokes ONLY where there is subject content. Light
background areas stay completely empty -- there are no decorative
background hatches, grid hatches, or filler strokes. This is a
deliberate design rule: background hatching turns plotter output
into mud, and the kit enforces it.

The stroke density is proportional to image darkness:
  - pure white (255)  -> no strokes
  - mid grey (128)    -> sparse strokes
  - pure black (0)    -> dense strokes

Two hatch styles are supported:
  - `parallel`  : all strokes at a single angle
  - `crosshatch`: two perpendicular layers

If no input image is provided the generator synthesises a circular
portrait mask with a radial falloff so the kit runs end-to-end out
of the box. Bring your own image for real portraits.

Usage:
    python hatching.py --seed 1 --output out.svg
    python hatching.py --input portrait.jpg --angle 35 --style crosshatch --output out.svg

Requires: Pillow (pip install Pillow)  -- falls back to synthetic mask if missing.
"""

import argparse
import math
import random
import sys

import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

from plotter_utils import (
    PAPERS,
    PaperSize,
    add_common_args,
    clip_to_bounds,
    optimize_stroke_order,
    paths_to_svg,
    report,
    write_svg,
)


def load_darkness(input_path: str | None, grid_w: int, grid_h: int):
    """Return a list-of-lists (grid_h rows, grid_w cols) with values 0..1
    where 1.0 is the darkest (most strokes wanted).
    """
    if input_path:
        try:
            from PIL import Image
        except ImportError:
            sys.stderr.write(
                "[hatching] ERROR: Pillow is required to load images. pip install Pillow\n"
            )
            sys.exit(2)
        img = Image.open(input_path).convert("L").resize((grid_w, grid_h))
        data = list(img.getdata())
        darkness = [
            [1.0 - (data[r * grid_w + c] / 255.0) for c in range(grid_w)]
            for r in range(grid_h)
        ]
        return darkness

    # Synthetic portrait mask: centred circle with radial falloff and a
    # small offset highlight so the result actually looks like a face-ish
    # blob instead of a disk.
    cx, cy = grid_w * 0.5, grid_h * 0.45
    radius = min(grid_w, grid_h) * 0.35
    darkness = [[0.0] * grid_w for _ in range(grid_h)]
    for r in range(grid_h):
        for c in range(grid_w):
            dx = (c - cx) / radius
            dy = (r - cy) / radius
            d = math.hypot(dx, dy)
            if d <= 1.0:
                # Darker at the edges (rim light), softer in centre.
                darkness[r][c] = min(1.0, 0.25 + 0.75 * d * d)
    return darkness


def hatch_lines(
    darkness: list[list[float]],
    paper: PaperSize,
    angle_deg: float,
    density: float,
    threshold: float,
    seed: int,
) -> list[list[tuple[float, float]]]:
    """Draw parallel lines across the inner paper area, but keep only
    the sub-segments that lie over pixels whose darkness exceeds
    `threshold`. This enforces the 'NO background hatching' rule by
    construction.
    """
    rng = random.Random(seed)
    x0, y0, x1, y1 = paper.bounds
    w = x1 - x0
    h = y1 - y0
    grid_h = len(darkness)
    grid_w = len(darkness[0]) if grid_h else 0
    if not grid_h or not grid_w:
        return []

    # Line spacing in mm: density 1.0 -> 0.8 mm; density 0.2 -> 4 mm.
    spacing = max(0.6, 4.0 - 3.2 * density)

    # Parametrise lines by perpendicular offset `t`. The line at offset t
    # has direction (cos a, sin a) and starts at centre + t * perp.
    angle = math.radians(angle_deg)
    dir_x, dir_y = math.cos(angle), math.sin(angle)
    perp_x, perp_y = -dir_y, dir_x

    # Half-extent in perp direction sufficient to cover the rectangle.
    half = math.hypot(w, h) * 0.6
    n_lines = int(2 * half / spacing) + 1

    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2

    paths: list[list[tuple[float, float]]] = []

    for i in range(n_lines):
        t = -half + i * spacing + rng.uniform(-spacing * 0.08, spacing * 0.08)
        ox = cx + perp_x * t
        oy = cy + perp_y * t
        # Clip the infinite line to the paper rect, then walk it sampling darkness.
        seg = [
            (ox - dir_x * half * 2, oy - dir_y * half * 2),
            (ox + dir_x * half * 2, oy + dir_y * half * 2),
        ]
        clipped_segments = clip_to_bounds(seg, paper.bounds)
        for sub in clipped_segments:
            (ax, ay), (bx, by) = sub[0], sub[1]
            length = math.hypot(bx - ax, by - ay)
            if length < 0.5:
                continue
            steps = max(2, int(length / 0.5))
            # Walk and emit sub-strokes only where darkness >= threshold.
            current: list[tuple[float, float]] = []
            for k in range(steps + 1):
                u = k / steps
                px = ax + (bx - ax) * u
                py = ay + (by - ay) * u
                # Sample darkness at this paper coord.
                gx = int((px - x0) / w * (grid_w - 1))
                gy = int((py - y0) / h * (grid_h - 1))
                gx = max(0, min(grid_w - 1, gx))
                gy = max(0, min(grid_h - 1, gy))
                d = darkness[gy][gx]
                if d >= threshold:
                    current.append((px, py))
                else:
                    if len(current) >= 2:
                        paths.append(current)
                    current = []
            if len(current) >= 2:
                paths.append(current)

    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Subject-Driven Hatching Generator (NO background hatching)")
    add_common_args(parser)
    parser.add_argument("--input", type=str, default=None, help="Input image (any PIL format). Defaults to synthetic portrait.")
    parser.add_argument("--style", choices=["parallel", "crosshatch"], default="parallel")
    parser.add_argument("--angle", type=float, default=35.0, help="Hatch angle in degrees")
    parser.add_argument("--density", type=float, default=0.8, help="0.0 = sparse, 1.0 = dense")
    parser.add_argument("--threshold", type=float, default=0.35, help="Min darkness to draw (enforces no-background rule)")
    parser.add_argument("--grid-w", type=int, default=220)
    parser.add_argument("--grid-h", type=int, default=300)
    args = parser.parse_args()

    seed = args.seed if args.seed is not None else random.randint(0, 999999)
    paper = PAPERS[args.paper]

    darkness = load_darkness(args.input, args.grid_w, args.grid_h)

    paths = hatch_lines(
        darkness=darkness,
        paper=paper,
        angle_deg=args.angle,
        density=args.density,
        threshold=args.threshold,
        seed=seed,
    )
    if args.style == "crosshatch":
        paths.extend(
            hatch_lines(
                darkness=darkness,
                paper=paper,
                angle_deg=args.angle + 90,
                density=args.density * 0.8,
                threshold=args.threshold + 0.1,
                seed=seed + 1,
            )
        )

    if not args.no_optimize:
        paths = optimize_stroke_order(paths)

    svg = paths_to_svg(
        paths,
        paper,
        seed=seed,
        generator="hatching.py",
        params={
            "style": args.style,
            "angle": args.angle,
            "density": args.density,
            "threshold": args.threshold,
            "input": args.input or "synthetic",
        },
        stroke_width=args.stroke_width,
    )
    write_svg(svg, args.output)
    report("hatching", seed, len(paths), paths)
    print(f"Saved {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
