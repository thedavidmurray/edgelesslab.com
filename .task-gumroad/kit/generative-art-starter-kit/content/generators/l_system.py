#!/usr/bin/env python3
"""
L-System Tree Generator for Pen Plotters.

Lindenmayer-system string rewriting rendered with turtle graphics.
Presets: oak, willow, fern, bush, sierpinski.

Usage:
    python l_system.py --preset fern --seed 42 --output out.svg
    python l_system.py --preset willow --iterations 6 --output out.svg
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

PRESETS = {
    "oak": {
        "axiom": "F",
        "rules": {"F": "FF+[+F-F-F]-[-F+F+F]"},
        "angle": 22.5,
        "length_ratio": 0.65,
        "iterations": 4,
    },
    "willow": {
        "axiom": "F",
        "rules": {"F": "F[+F]F[-F][F]"},
        "angle": 20,
        "length_ratio": 0.75,
        "iterations": 5,
    },
    "fern": {
        "axiom": "X",
        "rules": {"X": "F+[[X]-X]-F[-FX]+X", "F": "FF"},
        "angle": 25,
        "length_ratio": 0.5,
        "iterations": 6,
    },
    "bush": {
        "axiom": "F",
        "rules": {"F": "F[-F]F[+F][F]"},
        "angle": 25.7,
        "length_ratio": 0.6,
        "iterations": 5,
    },
    "sierpinski": {
        "axiom": "F-G-G",
        "rules": {"F": "F-G+F+G-F", "G": "GG"},
        "angle": 120,
        "length_ratio": 0.5,
        "iterations": 6,
    },
}


def expand_lsystem(axiom: str, rules: dict, iterations: int) -> str:
    current = axiom
    for _ in range(iterations):
        current = "".join(rules.get(ch, ch) for ch in current)
    return current


def render_turtle(
    instructions: str,
    base_length: float,
    angle_delta: float,
    length_ratio: float,
    start_angle: float = -90.0,
    jitter: float = 0.0,
    seed: int = 0,
) -> list[list[tuple[float, float]]]:
    rng = random.Random(seed)
    paths: list[list[tuple[float, float]]] = []
    current: list[tuple[float, float]] = [(0.0, 0.0)]
    x = y = 0.0
    angle = start_angle
    length = base_length
    stack: list[tuple[float, float, float, float]] = []

    for char in instructions:
        if char in ("F", "G"):
            jx = rng.uniform(-jitter, jitter) if jitter > 0 else 0.0
            jy = rng.uniform(-jitter, jitter) if jitter > 0 else 0.0
            x += math.cos(math.radians(angle)) * length + jx
            y += math.sin(math.radians(angle)) * length + jy
            current.append((x, y))
        elif char == "f":
            x += math.cos(math.radians(angle)) * length
            y += math.sin(math.radians(angle)) * length
            if len(current) > 1:
                paths.append(current)
            current = [(x, y)]
        elif char == "+":
            angle += angle_delta
        elif char == "-":
            angle -= angle_delta
        elif char == "[":
            stack.append((x, y, angle, length))
            length *= length_ratio
        elif char == "]":
            if len(current) > 1:
                paths.append(current)
            if stack:
                x, y, angle, length = stack.pop()
            current = [(x, y)]

    if len(current) > 1:
        paths.append(current)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="L-System Tree Generator")
    add_common_args(parser)
    parser.add_argument("--preset", choices=PRESETS.keys(), default="fern")
    parser.add_argument("--iterations", type=int, default=None)
    parser.add_argument("--angle", type=float, default=None)
    parser.add_argument("--length-ratio", type=float, default=None)
    parser.add_argument("--base-length", type=float, default=5.0)
    parser.add_argument("--jitter", type=float, default=0.0)
    args = parser.parse_args()

    preset = PRESETS[args.preset]
    seed = args.seed if args.seed is not None else random.randint(0, 999999)
    iterations = args.iterations if args.iterations is not None else preset["iterations"]
    angle_delta = args.angle if args.angle is not None else preset["angle"]
    length_ratio = args.length_ratio if args.length_ratio is not None else preset["length_ratio"]
    paper = PAPERS[args.paper]

    instructions = expand_lsystem(preset["axiom"], preset["rules"], iterations)
    print(f"[l_system] expanded to {len(instructions)} chars", file=sys.stderr)

    paths = render_turtle(
        instructions,
        base_length=args.base_length,
        angle_delta=angle_delta,
        length_ratio=length_ratio,
        jitter=args.jitter,
        seed=seed,
    )
    paths = fit_paths_to_paper(paths, paper)

    if not args.no_optimize:
        paths = optimize_stroke_order(paths)

    svg = paths_to_svg(
        paths,
        paper,
        seed=seed,
        generator="l_system.py",
        params={
            "preset": args.preset,
            "iterations": iterations,
            "angle": angle_delta,
            "length_ratio": length_ratio,
            "base_length": args.base_length,
            "jitter": args.jitter,
        },
        stroke_width=args.stroke_width,
    )
    write_svg(svg, args.output)
    report("l_system", seed, len(paths), paths)
    print(f"Saved {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
