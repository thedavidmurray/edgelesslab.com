#!/usr/bin/env python3
"""
Topographic Contour Generator for Pen Plotters.

Builds a Perlin-noise heightfield (optionally with octaves and
ridged-multifractal warping) then extracts contour lines at a
configurable set of elevation bands. The result reads as a
topographic map.

Usage:
    python topographic.py --seed 1 --output out.svg
    python topographic.py --levels 12 --noise-scale 0.012 --octaves 4 --output out.svg

Requires: numpy (pip install numpy)
"""

import argparse
import math
import random
import sys

import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

from plotter_utils import (
    PAPERS,
    add_common_args,
    fit_paths_to_paper,
    optimize_stroke_order,
    paths_to_svg,
    report,
    write_svg,
)


def build_heightfield(
    grid_w: int,
    grid_h: int,
    seed: int,
    noise_scale: float,
    octaves: int,
    ridged: bool,
):
    import numpy as np

    # Lightweight value-noise: tile-with-smoothstep bilinear interp.
    rng = np.random.default_rng(seed)

    def layer(period_x: float, period_y: float):
        lattice_w = max(2, int(grid_w / period_x) + 2)
        lattice_h = max(2, int(grid_h / period_y) + 2)
        lat = rng.random((lattice_h, lattice_w))
        xs = np.linspace(0, lattice_w - 1.001, grid_w)
        ys = np.linspace(0, lattice_h - 1.001, grid_h)
        xi = xs.astype(int)
        yi = ys.astype(int)
        xf = xs - xi
        yf = ys - yi
        sx = xf * xf * (3 - 2 * xf)
        sy = yf * yf * (3 - 2 * yf)
        a = lat[yi[:, None], xi[None, :]]
        b = lat[yi[:, None], xi[None, :] + 1]
        c = lat[yi[:, None] + 1, xi[None, :]]
        d = lat[yi[:, None] + 1, xi[None, :] + 1]
        top = a + (b - a) * sx[None, :]
        bot = c + (d - c) * sx[None, :]
        return top + (bot - top) * sy[:, None]

    base_period = 1.0 / max(noise_scale, 1e-4)
    field = np.zeros((grid_h, grid_w))
    amplitude = 1.0
    total = 0.0
    for o in range(octaves):
        p = base_period / (2 ** o)
        l = layer(p, p)
        if ridged:
            l = 1.0 - np.abs(2 * l - 1)
            l *= l
        field += amplitude * l
        total += amplitude
        amplitude *= 0.5
    field /= total
    return field


# Same marching squares as reaction_diffusion (kept separate so each
# generator is a self-contained unit users can lift.)

_EDGE_TABLE = [
    [], [3, 0], [0, 1], [3, 1], [1, 2],
    [3, 0, 1, 2], [0, 2], [3, 2], [2, 3],
    [2, 0], [0, 1, 2, 3], [2, 1], [1, 3],
    [1, 0], [0, 3], [],
]


def _interp(t, v0, v1):
    if abs(v1 - v0) < 1e-10:
        return 0.5
    return (t - v0) / (v1 - v0)


def _edge_pt(edge, row, col, corners, threshold):
    bl, br, tr, tl = corners
    if edge == 0:
        return (col + _interp(threshold, bl, br), row + 1)
    if edge == 1:
        return (col + 1, row + 1 - _interp(threshold, br, tr))
    if edge == 2:
        return (col + _interp(threshold, tl, tr), row)
    return (col, row + 1 - _interp(threshold, bl, tl))


def extract_contour(grid, threshold: float):
    rows, cols = grid.shape
    segments = []
    for row in range(rows - 1):
        for col in range(cols - 1):
            bl = grid[row + 1, col]
            br = grid[row + 1, col + 1]
            tr = grid[row, col + 1]
            tl = grid[row, col]
            corners = [bl, br, tr, tl]
            idx = (
                (1 if tl > threshold else 0) << 3
                | (1 if tr > threshold else 0) << 2
                | (1 if br > threshold else 0) << 1
                | (1 if bl > threshold else 0)
            )
            edges = _EDGE_TABLE[idx]
            for k in range(0, len(edges), 2):
                p0 = _edge_pt(edges[k], row, col, corners, threshold)
                p1 = _edge_pt(edges[k + 1], row, col, corners, threshold)
                segments.append([p0, p1])
    return segments


def chain_segments(segments, tol=1e-5):
    from collections import defaultdict

    def key(p):
        return (round(p[0] / tol), round(p[1] / tol))

    endpoint_map = defaultdict(list)
    for i, (p0, p1) in enumerate(segments):
        endpoint_map[key(p0)].append((i, 0))
        endpoint_map[key(p1)].append((i, 1))

    used = [False] * len(segments)
    chains = []
    for start in range(len(segments)):
        if used[start]:
            continue
        used[start] = True
        chain = list(segments[start])
        while True:
            tail = chain[-1]
            cand = [(i, e) for (i, e) in endpoint_map[key(tail)] if not used[i]]
            if not cand:
                break
            i, e = cand[0]
            used[i] = True
            p0, p1 = segments[i]
            chain.append(p1 if e == 0 else p0)
        while True:
            head = chain[0]
            cand = [(i, e) for (i, e) in endpoint_map[key(head)] if not used[i]]
            if not cand:
                break
            i, e = cand[0]
            used[i] = True
            p0, p1 = segments[i]
            chain.insert(0, p0 if e == 1 else p1)
        if len(chain) >= 2:
            chains.append(chain)
    return chains


def main() -> None:
    parser = argparse.ArgumentParser(description="Topographic Contour Generator")
    add_common_args(parser)
    parser.add_argument("--levels", type=int, default=10)
    parser.add_argument("--noise-scale", type=float, default=0.02)
    parser.add_argument("--octaves", type=int, default=4)
    parser.add_argument("--ridged", action="store_true", help="Ridged multifractal mode")
    parser.add_argument("--grid-w", type=int, default=200)
    parser.add_argument("--grid-h", type=int, default=280)
    args = parser.parse_args()

    try:
        import numpy as np  # noqa: F401
    except ImportError:
        sys.stderr.write("[topographic] ERROR: numpy is required. pip install numpy\n")
        sys.exit(2)

    seed = args.seed if args.seed is not None else random.randint(0, 999999)
    paper = PAPERS[args.paper]

    field = build_heightfield(
        args.grid_w, args.grid_h, seed, args.noise_scale, args.octaves, args.ridged
    )
    lo, hi = float(field.min()), float(field.max())
    rng = hi - lo or 1.0

    paths: list[list[tuple[float, float]]] = []
    for i in range(1, args.levels + 1):
        t = lo + (i / (args.levels + 1)) * rng
        segs = extract_contour(field, t)
        chains = chain_segments(segs)
        paths.extend(chains)

    paths = fit_paths_to_paper(paths, paper)

    if not args.no_optimize:
        paths = optimize_stroke_order(paths)

    svg = paths_to_svg(
        paths,
        paper,
        seed=seed,
        generator="topographic.py",
        params={
            "levels": args.levels,
            "noise_scale": args.noise_scale,
            "octaves": args.octaves,
            "ridged": args.ridged,
            "grid": f"{args.grid_w}x{args.grid_h}",
        },
        stroke_width=args.stroke_width,
    )
    write_svg(svg, args.output)
    report("topographic", seed, len(paths), paths)
    print(f"Saved {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
