#!/usr/bin/env python3
"""
Recursive Grid Subdivision Generator for Pen Plotters.

Vera Molnar-inspired rectangular subdivision. Start with the whole
sheet as one cell; repeatedly pick a cell and cut it horizontally or
vertically. Each leaf cell is drawn as a rectangle (and optionally as
a light cross or corner detail).

Usage:
    python subdivision.py --seed 42 --depth 6 --output out.svg
    python subdivision.py --splits 200 --output dense.svg

Stdlib only.
"""

import argparse
import random
import sys

import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

from plotter_utils import (
    PAPERS,
    PaperSize,
    add_common_args,
    optimize_stroke_order,
    paths_to_svg,
    report,
    write_svg,
)

Rect = tuple[float, float, float, float]  # x, y, w, h


def split_rect(rect: Rect, rng: random.Random, prefer: str | None = None) -> tuple[Rect, Rect]:
    x, y, w, h = rect
    if prefer == "h" or (prefer is None and w >= h):
        cut = rng.uniform(0.25, 0.75)
        return (x, y, w * cut, h), (x + w * cut, y, w * (1 - cut), h)
    else:
        cut = rng.uniform(0.25, 0.75)
        return (x, y, w, h * cut), (x, y + h * cut, w, h * (1 - cut))


def subdivide(paper: PaperSize, seed: int, splits: int, min_size: float, decorate: bool) -> list[list[tuple[float, float]]]:
    rng = random.Random(seed)
    rects: list[Rect] = [
        (paper.margin, paper.margin, paper.inner_width, paper.inner_height)
    ]

    for _ in range(splits):
        # Pick a cell weighted by area so big cells split first.
        eligible = [r for r in rects if r[2] > min_size * 2 and r[3] > min_size * 2]
        if not eligible:
            break
        weights = [r[2] * r[3] for r in eligible]
        choice = rng.choices(eligible, weights=weights, k=1)[0]
        rects.remove(choice)
        a, b = split_rect(choice, rng)
        rects.extend([a, b])

    paths: list[list[tuple[float, float]]] = []
    for (x, y, w, h) in rects:
        # Outer rectangle
        paths.append([(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)])

        if decorate:
            roll = rng.random()
            if roll < 0.15:
                # Cross
                paths.append([(x, y), (x + w, y + h)])
                paths.append([(x + w, y), (x, y + h)])
            elif roll < 0.3:
                # Inner concentric rect
                pad = min(w, h) * 0.2
                paths.append(
                    [
                        (x + pad, y + pad),
                        (x + w - pad, y + pad),
                        (x + w - pad, y + h - pad),
                        (x + pad, y + h - pad),
                        (x + pad, y + pad),
                    ]
                )
            elif roll < 0.45:
                # Single diagonal
                if rng.random() < 0.5:
                    paths.append([(x, y), (x + w, y + h)])
                else:
                    paths.append([(x + w, y), (x, y + h)])
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Recursive Grid Subdivision Generator")
    add_common_args(parser)
    parser.add_argument("--splits", type=int, default=120, help="Number of subdivision cuts")
    parser.add_argument("--min-size", type=float, default=8.0, help="Minimum cell dimension (mm)")
    parser.add_argument("--no-decorate", action="store_true", help="Plain rectangles only")
    args = parser.parse_args()

    seed = args.seed if args.seed is not None else random.randint(0, 999999)
    paper = PAPERS[args.paper]

    paths = subdivide(
        paper=paper,
        seed=seed,
        splits=args.splits,
        min_size=args.min_size,
        decorate=not args.no_decorate,
    )

    if not args.no_optimize:
        paths = optimize_stroke_order(paths)

    svg = paths_to_svg(
        paths,
        paper,
        seed=seed,
        generator="subdivision.py",
        params={
            "splits": args.splits,
            "min_size": args.min_size,
            "decorate": not args.no_decorate,
        },
        stroke_width=args.stroke_width,
    )
    write_svg(svg, args.output)
    report("subdivision", seed, len(paths), paths)
    print(f"Saved {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
