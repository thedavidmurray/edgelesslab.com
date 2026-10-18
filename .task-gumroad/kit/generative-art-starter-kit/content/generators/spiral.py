#!/usr/bin/env python3
"""
Spiral Generator for Pen Plotters.

Three parametric spiral families:
  - archimedean: r = a + b * theta             (constant arm spacing)
  - logarithmic: r = a * exp(b * theta)        (exponential growth)
  - hypotrochoid: classic roulette curve       (inner-circle tracing)

Usage:
    python spiral.py --type archimedean --seed 1 --output out.svg
    python spiral.py --type logarithmic --turns 8 --output out.svg
    python spiral.py --type hypotrochoid --R 80 --r 21 --d 51 --output out.svg

Stdlib only.
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
    fit_paths_to_paper,
    optimize_stroke_order,
    paths_to_svg,
    report,
    write_svg,
)


def archimedean(turns: float, a: float, b: float, samples: int) -> list[tuple[float, float]]:
    pts = []
    theta_max = turns * 2 * math.pi
    for i in range(samples + 1):
        theta = (i / samples) * theta_max
        r = a + b * theta
        pts.append((r * math.cos(theta), r * math.sin(theta)))
    return pts


def logarithmic(turns: float, a: float, b: float, samples: int) -> list[tuple[float, float]]:
    pts = []
    theta_max = turns * 2 * math.pi
    for i in range(samples + 1):
        theta = (i / samples) * theta_max
        r = a * math.exp(b * theta)
        pts.append((r * math.cos(theta), r * math.sin(theta)))
    return pts


def hypotrochoid(R: float, r: float, d: float, samples: int) -> list[tuple[float, float]]:
    """Curve traced by a point at distance d from the centre of a small
    circle of radius r rolling inside a circle of radius R."""
    pts = []
    # Periodic with period 2 pi r / gcd(R, r); use a comfortable upper bound.
    cycles = max(1, int(r / math.gcd(int(R), max(int(r), 1)) or 1))
    theta_max = 2 * math.pi * cycles
    diff = R - r
    for i in range(samples + 1):
        t = (i / samples) * theta_max
        x = diff * math.cos(t) + d * math.cos(diff * t / r)
        y = diff * math.sin(t) - d * math.sin(diff * t / r)
        pts.append((x, y))
    return pts


def stacked_spirals(kind: str, count: int, paper: PaperSize, seed: int) -> list[list[tuple[float, float]]]:
    rng = random.Random(seed)
    paths: list[list[tuple[float, float]]] = []
    cols = max(1, int(math.sqrt(count)))
    rows = (count + cols - 1) // cols
    cell_w = paper.inner_width / cols
    cell_h = paper.inner_height / rows
    radius = min(cell_w, cell_h) * 0.42

    for i in range(count):
        cx = paper.margin + (i % cols + 0.5) * cell_w
        cy = paper.margin + (i // cols + 0.5) * cell_h
        if kind == "archimedean":
            pts = archimedean(rng.uniform(4, 9), 0.0, radius / (rng.uniform(20, 35)), 600)
        elif kind == "logarithmic":
            pts = logarithmic(rng.uniform(2.0, 4.0), 1.0, rng.uniform(0.13, 0.22), 600)
        else:  # hypotrochoid
            pts = hypotrochoid(R=radius, r=rng.uniform(radius * 0.18, radius * 0.45), d=rng.uniform(radius * 0.4, radius * 0.95), samples=1200)
        # Normalise to fit cell
        max_r = max(math.hypot(x, y) for x, y in pts) or 1.0
        scale = radius / max_r
        pts = [(x * scale + cx, y * scale + cy) for x, y in pts]
        paths.append(pts)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Spiral Generator")
    add_common_args(parser)
    parser.add_argument("--type", choices=["archimedean", "logarithmic", "hypotrochoid", "grid"], default="archimedean")
    parser.add_argument("--turns", type=float, default=6.0)
    parser.add_argument("--a", type=float, default=0.0, help="Inner radius / scale param")
    parser.add_argument("--b", type=float, default=2.0, help="Growth param")
    parser.add_argument("--R", type=float, default=80.0, help="Outer radius (hypotrochoid)")
    parser.add_argument("--r", type=float, default=21.0, help="Inner radius (hypotrochoid)")
    parser.add_argument("--d", type=float, default=51.0, help="Pen offset (hypotrochoid)")
    parser.add_argument("--samples", type=int, default=2000)
    parser.add_argument("--count", type=int, default=12, help="Number of spirals when --type grid")
    args = parser.parse_args()

    seed = args.seed if args.seed is not None else random.randint(0, 999999)
    paper = PAPERS[args.paper]

    if args.type == "archimedean":
        pts = archimedean(args.turns, args.a, args.b, args.samples)
        paths = [pts]
    elif args.type == "logarithmic":
        pts = logarithmic(args.turns, max(args.a, 1.0), max(args.b, 0.05), args.samples)
        paths = [pts]
    elif args.type == "hypotrochoid":
        pts = hypotrochoid(args.R, args.r, args.d, args.samples)
        paths = [pts]
    else:
        paths = stacked_spirals("archimedean" if seed % 3 == 0 else ("logarithmic" if seed % 3 == 1 else "hypotrochoid"), args.count, paper, seed)

    paths = fit_paths_to_paper(paths, paper)

    if not args.no_optimize:
        paths = optimize_stroke_order(paths)

    svg = paths_to_svg(
        paths,
        paper,
        seed=seed,
        generator="spiral.py",
        params={
            "type": args.type,
            "turns": args.turns,
            "a": args.a,
            "b": args.b,
            "R": args.R,
            "r": args.r,
            "d": args.d,
            "samples": args.samples,
            "count": args.count,
        },
        stroke_width=args.stroke_width,
    )
    write_svg(svg, args.output)
    report("spiral", seed, len(paths), paths)
    print(f"Saved {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
