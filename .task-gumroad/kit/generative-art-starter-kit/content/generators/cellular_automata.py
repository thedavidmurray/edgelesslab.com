#!/usr/bin/env python3
"""
Elementary Cellular Automata Generator for Pen Plotters.

Simulates 1D elementary CAs (8-bit rule) for N generations and
renders each live cell as a stroked rectangle. Famous presets:
  - rule 30  : chaotic, used for hardware RNG in Mathematica
  - rule 90  : Sierpinski triangle via XOR
  - rule 110 : Turing complete, rich structure
  - rule 184 : traffic flow model, clear diagonal bands

No background hatching. Dead cells are left blank.

Usage:
    python cellular_automata.py --rule 30 --seed 1 --output out.svg
    python cellular_automata.py --rule 110 --width 180 --generations 260 --output out.svg

Stdlib only.
"""

import argparse
import random
import sys

import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

from plotter_utils import (
    PAPERS,
    add_common_args,
    optimize_stroke_order,
    paths_to_svg,
    report,
    write_svg,
)

PRESETS = {
    30: "chaotic",
    90: "sierpinski",
    110: "turing-complete",
    184: "traffic",
    54: "soliton",
    150: "xor",
}


def step(row: list[int], rule: int) -> list[int]:
    new = [0] * len(row)
    n = len(row)
    for i in range(n):
        left = row[(i - 1) % n]
        c = row[i]
        right = row[(i + 1) % n]
        idx = (left << 2) | (c << 1) | right
        new[i] = (rule >> idx) & 1
    return new


def simulate(rule: int, width: int, generations: int, seed: int, init: str) -> list[list[int]]:
    rng = random.Random(seed)
    if init == "single":
        row = [0] * width
        row[width // 2] = 1
    else:
        row = [rng.randint(0, 1) for _ in range(width)]
    grid = [row]
    for _ in range(generations - 1):
        row = step(row, rule)
        grid.append(row)
    return grid


def render(grid: list[list[int]], paper) -> list[list[tuple[float, float]]]:
    generations = len(grid)
    width = len(grid[0])
    cell_w = paper.inner_width / width
    cell_h = paper.inner_height / generations
    # Use a consistent square-ish cell size: pick the smaller so neither
    # axis gets stretched too far.
    size = min(cell_w, cell_h)
    off_x = paper.margin + (paper.inner_width - size * width) / 2
    off_y = paper.margin + (paper.inner_height - size * generations) / 2
    pad = size * 0.12  # inner padding so cells do not touch

    paths: list[list[tuple[float, float]]] = []
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v == 0:
                continue
            x = off_x + c * size + pad
            y = off_y + r * size + pad
            w = size - 2 * pad
            h = size - 2 * pad
            paths.append(
                [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
            )
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Elementary Cellular Automata Generator")
    add_common_args(parser)
    parser.add_argument("--rule", type=int, default=30, help="Wolfram rule 0..255")
    parser.add_argument("--width", type=int, default=121, help="Number of cells per row")
    parser.add_argument("--generations", type=int, default=170, help="Number of rows")
    parser.add_argument("--init", choices=["single", "random"], default="single")
    args = parser.parse_args()

    if not 0 <= args.rule <= 255:
        parser.error("rule must be 0..255")

    seed = args.seed if args.seed is not None else random.randint(0, 999999)
    paper = PAPERS[args.paper]

    grid = simulate(args.rule, args.width, args.generations, seed, args.init)
    paths = render(grid, paper)

    if not args.no_optimize:
        paths = optimize_stroke_order(paths)

    svg = paths_to_svg(
        paths,
        paper,
        seed=seed,
        generator="cellular_automata.py",
        params={
            "rule": args.rule,
            "preset": PRESETS.get(args.rule, "custom"),
            "width": args.width,
            "generations": args.generations,
            "init": args.init,
        },
        stroke_width=args.stroke_width,
    )
    write_svg(svg, args.output)
    report("cellular_automata", seed, len(paths), paths)
    print(f"Saved {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
