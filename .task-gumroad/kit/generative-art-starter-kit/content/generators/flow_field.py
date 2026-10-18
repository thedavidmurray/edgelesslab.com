#!/usr/bin/env python3
"""
Flow Field Generator for Pen Plotters.

Particles trace paths through a Perlin-noise-driven vector field.
The result looks like wind currents, water flow, or magnetic field
lines, depending on the noise scale and step length you choose.

Usage:
    python flow_field.py --seed 42 --output out.svg
    python flow_field.py --seed 7 --resolution 60 --noise-scale 0.012 --output dense.svg
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
    optimize_stroke_order,
    paths_to_svg,
    report,
    write_svg,
)

# ----------------------------------------------------------------------
# Inline Perlin noise (no numpy)
# ----------------------------------------------------------------------

_PERM: list[int] = list(range(256))


def _init_perm(seed: int) -> None:
    global _PERM
    rng = random.Random(seed)
    _PERM = list(range(256))
    rng.shuffle(_PERM)
    _PERM = _PERM + _PERM


def _fade(t: float) -> float:
    return t * t * t * (t * (t * 6 - 15) + 10)


def _lerp(a: float, b: float, t: float) -> float:
    return a + t * (b - a)


def _grad(h: int, x: float, y: float) -> float:
    h = h & 3
    if h == 0:
        return x + y
    if h == 1:
        return -x + y
    if h == 2:
        return x - y
    return -x - y


def perlin2d(x: float, y: float) -> float:
    xi = int(math.floor(x)) & 255
    yi = int(math.floor(y)) & 255
    xf = x - math.floor(x)
    yf = y - math.floor(y)
    u = _fade(xf)
    v = _fade(yf)
    aa = _PERM[_PERM[xi] + yi]
    ab = _PERM[_PERM[xi] + yi + 1]
    ba = _PERM[_PERM[xi + 1] + yi]
    bb = _PERM[_PERM[xi + 1] + yi + 1]
    x1 = _lerp(_grad(aa, xf, yf), _grad(ba, xf - 1, yf), u)
    x2 = _lerp(_grad(ab, xf, yf - 1), _grad(bb, xf - 1, yf - 1), u)
    return _lerp(x1, x2, v)


# ----------------------------------------------------------------------
# Generator
# ----------------------------------------------------------------------


def generate_flow_field(
    seed: int,
    paper: PaperSize,
    resolution: int = 40,
    noise_scale: float = 0.02,
    step_length: float = 1.0,
    max_steps: int = 100,
) -> list[list[tuple[float, float]]]:
    _init_perm(seed)
    rng = random.Random(seed)
    x_min, y_min, x_max, y_max = paper.bounds
    spacing = (x_max - x_min) / resolution

    paths: list[list[tuple[float, float]]] = []
    for row in range(resolution):
        for col in range(resolution):
            x = x_min + col * spacing + rng.uniform(-spacing * 0.3, spacing * 0.3)
            y = y_min + row * spacing + rng.uniform(-spacing * 0.3, spacing * 0.3)
            path = [(x, y)]
            for _ in range(max_steps):
                angle = perlin2d(x * noise_scale, y * noise_scale) * math.pi * 2
                x += math.cos(angle) * step_length
                y += math.sin(angle) * step_length
                if x < x_min or x > x_max or y < y_min or y > y_max:
                    break
                path.append((x, y))
            if len(path) > 3:
                paths.append(path)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Flow Field Generator for Pen Plotters")
    add_common_args(parser)
    parser.add_argument("--resolution", type=int, default=25, help="Grid resolution")
    parser.add_argument("--noise-scale", type=float, default=0.015, help="Noise frequency")
    parser.add_argument("--step-length", type=float, default=1.5, help="Step size (mm)")
    parser.add_argument("--max-steps", type=int, default=80, help="Max steps per path")
    args = parser.parse_args()

    seed = args.seed if args.seed is not None else random.randint(0, 999999)
    paper = PAPERS[args.paper]

    paths = generate_flow_field(
        seed=seed,
        paper=paper,
        resolution=args.resolution,
        noise_scale=args.noise_scale,
        step_length=args.step_length,
        max_steps=args.max_steps,
    )

    if not args.no_optimize:
        paths = optimize_stroke_order(paths)

    svg = paths_to_svg(
        paths,
        paper,
        seed=seed,
        generator="flow_field.py",
        params={
            "resolution": args.resolution,
            "noise_scale": args.noise_scale,
            "step_length": args.step_length,
            "max_steps": args.max_steps,
        },
        stroke_width=args.stroke_width,
    )
    write_svg(svg, args.output)
    report("flow_field", seed, len(paths), paths)
    print(f"Saved {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
