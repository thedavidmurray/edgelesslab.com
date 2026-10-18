#!/usr/bin/env python3
"""
Gray-Scott Reaction-Diffusion Generator for Pen Plotters.

Simulates the Gray-Scott model:
    dU/dt = Du * lap(U) - U V^2 + f (1 - U)
    dV/dt = Dv * lap(V) + U V^2 - (f + k) V

Pattern presets change (feed, kill) and produce spots, worms, coral,
zebra-stripes etc. Contour lines of V at multiple thresholds are then
extracted with marching squares and rendered as single-stroke SVG paths.

Usage:
    python reaction_diffusion.py --preset worms --seed 3 --output out.svg
    python reaction_diffusion.py --preset coral --iterations 8000 --output out.svg

Requires: numpy (pip install numpy)
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
    fit_paths_to_paper,
    optimize_stroke_order,
    paths_to_svg,
    report,
    write_svg,
)

PRESETS = {
    "spots":   {"feed": 0.030, "kill": 0.062, "levels": [0.15, 0.25, 0.35, 0.45]},
    "worms":   {"feed": 0.055, "kill": 0.062, "levels": [0.10, 0.20, 0.30, 0.40]},
    "coral":   {"feed": 0.0545, "kill": 0.062, "levels": [0.12, 0.22, 0.32, 0.42]},
    "maze":    {"feed": 0.029, "kill": 0.057, "levels": [0.18, 0.28, 0.38]},
    "zebra":   {"feed": 0.014, "kill": 0.045, "levels": [0.20, 0.30, 0.40]},
}


def run_simulation(feed: float, kill: float, grid_w: int, grid_h: int, iterations: int, seed: int):
    import numpy as np

    rng = np.random.default_rng(seed)
    U = np.ones((grid_h, grid_w), dtype=np.float64)
    V = np.zeros((grid_h, grid_w), dtype=np.float64)

    # Seed several splotches so symmetry breaks quickly.
    local = random.Random(seed)
    n_seeds = local.randint(5, 10)
    for _ in range(n_seeds):
        ry = local.randint(grid_h // 6, 5 * grid_h // 6)
        rx = local.randint(grid_w // 6, 5 * grid_w // 6)
        r = local.randint(4, 8)
        U[ry - r:ry + r, rx - r:rx + r] = 0.5
        V[ry - r:ry + r, rx - r:rx + r] = 0.25

    V += rng.uniform(0.0, 0.02, (grid_h, grid_w))
    V = np.clip(V, 0.0, 1.0)

    Du, Dv, dt = 0.16, 0.08, 1.0
    for i in range(iterations):
        lap_U = (
            np.roll(U, 1, 0) + np.roll(U, -1, 0) + np.roll(U, 1, 1) + np.roll(U, -1, 1) - 4.0 * U
        )
        lap_V = (
            np.roll(V, 1, 0) + np.roll(V, -1, 0) + np.roll(V, 1, 1) + np.roll(V, -1, 1) - 4.0 * V
        )
        uvv = U * V * V
        U += dt * (Du * lap_U - uvv + feed * (1.0 - U))
        V += dt * (Dv * lap_V + uvv - (feed + kill) * V)
        if i % 1000 == 0:
            print(f"[rd] step {i}/{iterations} Vmax={V.max():.3f}", file=sys.stderr)

    return V


# Marching-squares ------------------------------------------------------

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
        # Extend tail
        while True:
            tail = chain[-1]
            cand = [(i, e) for (i, e) in endpoint_map[key(tail)] if not used[i]]
            if not cand:
                break
            i, e = cand[0]
            used[i] = True
            p0, p1 = segments[i]
            chain.append(p1 if e == 0 else p0)
        # Extend head
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
    parser = argparse.ArgumentParser(description="Reaction-Diffusion Generator")
    add_common_args(parser)
    parser.add_argument("--preset", choices=PRESETS.keys(), default="worms")
    parser.add_argument("--iterations", type=int, default=5000)
    parser.add_argument("--grid-w", type=int, default=160)
    parser.add_argument("--grid-h", type=int, default=220)
    args = parser.parse_args()

    try:
        import numpy as np  # noqa: F401
    except ImportError:
        sys.stderr.write(
            "[reaction_diffusion] ERROR: numpy is required. pip install numpy\n"
        )
        sys.exit(2)

    seed = args.seed if args.seed is not None else random.randint(0, 999999)
    paper = PAPERS[args.paper]
    preset = PRESETS[args.preset]

    V = run_simulation(
        feed=preset["feed"],
        kill=preset["kill"],
        grid_w=args.grid_w,
        grid_h=args.grid_h,
        iterations=args.iterations,
        seed=seed,
    )

    # Extract contour lines in grid coordinates then fit to paper.
    paths = []
    for level in preset["levels"]:
        segs = extract_contour(V, level)
        chains = chain_segments(segs)
        paths.extend(chains)

    paths = fit_paths_to_paper(paths, paper)

    if not args.no_optimize:
        paths = optimize_stroke_order(paths)

    svg = paths_to_svg(
        paths,
        paper,
        seed=seed,
        generator="reaction_diffusion.py",
        params={
            "preset": args.preset,
            "feed": preset["feed"],
            "kill": preset["kill"],
            "iterations": args.iterations,
            "grid": f"{args.grid_w}x{args.grid_h}",
        },
        stroke_width=args.stroke_width,
    )
    write_svg(svg, args.output)
    report("reaction_diffusion", seed, len(paths), paths)
    print(f"Saved {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
