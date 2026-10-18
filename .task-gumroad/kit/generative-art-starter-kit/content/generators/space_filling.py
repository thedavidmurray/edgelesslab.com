#!/usr/bin/env python3
"""
Space-Filling Curve Generator for Pen Plotters.

Presets:
  - hilbert  : Hilbert curve (recursive U-shape)
  - dragon   : Heighway dragon curve
  - gosper   : Gosper / flowsnake curve

The entire curve is a single continuous path, which means the pen
never leaves the paper during plotting -- these are the most
plotter-efficient curves in the kit.

Usage:
    python space_filling.py --type hilbert --order 6 --seed 1 --output out.svg
    python space_filling.py --type dragon --order 12 --output out.svg
    python space_filling.py --type gosper --order 4 --output out.svg

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
    add_common_args,
    fit_paths_to_paper,
    paths_to_svg,
    report,
    write_svg,
)

# --- Hilbert ---------------------------------------------------------------


def hilbert_curve(order: int) -> list[tuple[float, float]]:
    """Return Hilbert curve vertices on an integer grid (0..2^order - 1)."""
    n = 1 << order

    def d2xy(d: int) -> tuple[int, int]:
        rx = ry = 0
        x = y = 0
        t = d
        s = 1
        while s < n:
            rx = 1 & (t >> 1)
            ry = 1 & (t ^ rx)
            if ry == 0:
                if rx == 1:
                    x = s - 1 - x
                    y = s - 1 - y
                x, y = y, x
            x += s * rx
            y += s * ry
            t >>= 2
            s <<= 1
        return x, y

    return [d2xy(i) for i in range(n * n)]


# --- Dragon curve ----------------------------------------------------------


def dragon_curve(order: int) -> list[tuple[float, float]]:
    # Generate turn sequence
    seq: list[int] = []  # +1 = left, -1 = right
    for i in range(1, (1 << order)):
        # Classic bit trick for dragon turns
        turn = (((i & -i) << 1) & i) == 0
        seq.append(1 if turn else -1)

    x, y = 0.0, 0.0
    angle = 0.0
    step = 1.0
    pts = [(x, y)]
    x += step
    pts.append((x, y))
    for s in seq:
        angle += 90 * s
        rad = math.radians(angle)
        x += math.cos(rad) * step
        y += math.sin(rad) * step
        pts.append((x, y))
    return pts


# --- Gosper curve ----------------------------------------------------------


def gosper_curve(order: int) -> list[tuple[float, float]]:
    """Gosper (flowsnake) curve via L-system expansion then turtle walk."""
    axiom = "A"
    rules = {
        "A": "A-B--B+A++AA+B-",
        "B": "+A-BB--B-A++A+B",
    }
    s = axiom
    for _ in range(order):
        s = "".join(rules.get(c, c) for c in s)

    x, y = 0.0, 0.0
    angle = 0.0
    step = 1.0
    pts = [(x, y)]
    for c in s:
        if c in ("A", "B"):
            x += math.cos(math.radians(angle)) * step
            y += math.sin(math.radians(angle)) * step
            pts.append((x, y))
        elif c == "+":
            angle += 60
        elif c == "-":
            angle -= 60
    return pts


def main() -> None:
    parser = argparse.ArgumentParser(description="Space-Filling Curve Generator")
    add_common_args(parser)
    parser.add_argument("--type", choices=["hilbert", "dragon", "gosper"], default="hilbert")
    parser.add_argument("--order", type=int, default=6, help="Recursion order")
    args = parser.parse_args()

    seed = args.seed if args.seed is not None else random.randint(0, 999999)
    paper = PAPERS[args.paper]

    if args.type == "hilbert":
        pts = hilbert_curve(args.order)
    elif args.type == "dragon":
        pts = dragon_curve(args.order)
    else:
        pts = gosper_curve(args.order)

    pts = [(float(x), float(y)) for x, y in pts]
    paths = [pts]
    paths = fit_paths_to_paper(paths, paper)

    svg = paths_to_svg(
        paths,
        paper,
        seed=seed,
        generator="space_filling.py",
        params={"type": args.type, "order": args.order, "vertices": len(pts)},
        stroke_width=args.stroke_width,
    )
    write_svg(svg, args.output)
    report("space_filling", seed, len(paths), paths)
    print(f"Saved {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
