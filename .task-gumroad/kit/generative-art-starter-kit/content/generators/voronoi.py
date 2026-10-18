#!/usr/bin/env python3
"""
Voronoi Cell Generator for Pen Plotters.

Scatters points, optionally relaxes them with Lloyd's algorithm, and
draws the Voronoi tessellation edges. This generator REQUIRES scipy --
the previous release silently fell back to drawing diamonds around
each point if scipy was missing, which made "voronoi" output that
had nothing to do with Voronoi. That dishonest fallback is gone.

Usage:
    python voronoi.py --seed 42 --num-points 120 --output out.svg
    python voronoi.py --num-points 250 --relaxation 5 --output dense.svg

Install requirement:
    python3 -m pip install scipy numpy
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


def _require_scipy():
    try:
        import numpy as np  # noqa: F401
        from scipy.spatial import Voronoi  # noqa: F401
    except ImportError as exc:
        sys.stderr.write(
            "\n[voronoi] ERROR: this generator needs scipy and numpy.\n"
            "   Install them with:\n"
            "       python3 -m pip install scipy numpy\n"
            "   (Use a virtualenv if your system python is PEP 668 locked.)\n"
            f"   Original error: {exc}\n\n"
        )
        sys.exit(2)


def lloyd_relaxation(
    points: list[tuple[float, float]],
    bounds: tuple[float, float, float, float],
    iterations: int,
) -> list[tuple[float, float]]:
    import numpy as np
    from scipy.spatial import Voronoi

    pts = np.array(points, dtype=float)
    x_min, y_min, x_max, y_max = bounds

    for _ in range(iterations):
        mirrored = np.vstack(
            [
                pts,
                np.column_stack([2 * x_min - pts[:, 0], pts[:, 1]]),
                np.column_stack([2 * x_max - pts[:, 0], pts[:, 1]]),
                np.column_stack([pts[:, 0], 2 * y_min - pts[:, 1]]),
                np.column_stack([pts[:, 0], 2 * y_max - pts[:, 1]]),
            ]
        )
        vor = Voronoi(mirrored)
        new_pts = []
        for i in range(len(pts)):
            region = vor.regions[vor.point_region[i]]
            if -1 in region or len(region) == 0:
                new_pts.append(pts[i])
                continue
            vertices = vor.vertices[region]
            cx = float(np.clip(vertices[:, 0].mean(), x_min, x_max))
            cy = float(np.clip(vertices[:, 1].mean(), y_min, y_max))
            new_pts.append([cx, cy])
        pts = np.array(new_pts)

    return [(float(p[0]), float(p[1])) for p in pts]


def voronoi_edges(
    points: list[tuple[float, float]],
    bounds: tuple[float, float, float, float],
) -> list[list[tuple[float, float]]]:
    import numpy as np
    from scipy.spatial import Voronoi

    pts = np.array(points, dtype=float)
    x_min, y_min, x_max, y_max = bounds
    mirrored = np.vstack(
        [
            pts,
            np.column_stack([2 * x_min - pts[:, 0], pts[:, 1]]),
            np.column_stack([2 * x_max - pts[:, 0], pts[:, 1]]),
            np.column_stack([pts[:, 0], 2 * y_min - pts[:, 1]]),
            np.column_stack([pts[:, 0], 2 * y_max - pts[:, 1]]),
        ]
    )
    vor = Voronoi(mirrored)
    segments: list[list[tuple[float, float]]] = []

    for rv in vor.ridge_vertices:
        if -1 in rv:
            continue
        v0 = vor.vertices[rv[0]]
        v1 = vor.vertices[rv[1]]
        seg = [(float(v0[0]), float(v0[1])), (float(v1[0]), float(v1[1]))]
        for clipped in clip_to_bounds(seg, bounds):
            if len(clipped) >= 2:
                segments.append(clipped)

    return segments


def main() -> None:
    parser = argparse.ArgumentParser(description="Voronoi Cell Generator")
    add_common_args(parser)
    parser.add_argument("--num-points", type=int, default=120)
    parser.add_argument("--relaxation", type=int, default=3)
    parser.add_argument("--jitter", type=float, default=0.0)
    parser.add_argument("--border", action="store_true", help="Draw a border rectangle")
    args = parser.parse_args()

    _require_scipy()

    seed = args.seed if args.seed is not None else random.randint(0, 999999)
    paper = PAPERS[args.paper]
    rng = random.Random(seed)

    x_min, y_min, x_max, y_max = paper.bounds
    bounds = (x_min, y_min, x_max, y_max)

    points = [
        (rng.uniform(x_min, x_max), rng.uniform(y_min, y_max))
        for _ in range(args.num_points)
    ]
    points = lloyd_relaxation(points, bounds, args.relaxation)

    if args.jitter > 0:
        spacing = math.sqrt((x_max - x_min) * (y_max - y_min) / args.num_points)
        points = [
            (
                max(x_min, min(x_max, px + rng.uniform(-spacing * args.jitter, spacing * args.jitter))),
                max(y_min, min(y_max, py + rng.uniform(-spacing * args.jitter, spacing * args.jitter))),
            )
            for px, py in points
        ]

    edges = voronoi_edges(points, bounds)

    if not args.no_optimize:
        edges = optimize_stroke_order(edges)

    svg = paths_to_svg(
        edges,
        paper,
        seed=seed,
        generator="voronoi.py",
        params={
            "num_points": args.num_points,
            "relaxation": args.relaxation,
            "jitter": args.jitter,
        },
        stroke_width=args.stroke_width,
        draw_border=args.border,
    )
    write_svg(svg, args.output)
    report("voronoi", seed, len(edges), edges)
    print(f"Saved {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
