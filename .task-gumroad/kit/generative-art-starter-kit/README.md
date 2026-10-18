# Generative Art Starter Kit

10 Python generators for pen plotters, 30 pre-plotted example SVGs
with full metadata, a 5,700-word plotter-focused guide, and an AI
scoring rubric distilled from 105+ autoresearch experiments.

All ten generators share a common `content/generators/plotter_utils.py`
module for paper sizes, stroke optimization, SVG output, and plot-time
estimation, so extending the kit with your own generators is a
one-import job.

## Quick Start

```bash
# Stdlib-only generators run out of the box
python3 content/generators/flow_field.py --seed 42 --output flow.svg
python3 content/generators/l_system.py --preset fern --seed 7 --output fern.svg
python3 content/generators/space_filling.py --type hilbert --order 6 --seed 1 --output hilbert.svg

# Voronoi, reaction-diffusion, topographic need numpy + scipy
python3 -m pip install numpy scipy Pillow cairosvg
python3 content/generators/voronoi.py --num-points 140 --seed 1 --output vor.svg
python3 content/generators/reaction_diffusion.py --preset worms --seed 3 --output rd.svg
python3 content/generators/topographic.py --seed 5 --output topo.svg

# Score your outputs with AI
GOOGLE_GEMINI_API_KEY=your-key python3 content/scoring/score.py *.png
```

## Generators

| # | Algorithm | Dependencies | Difficulty |
|---|-----------|-------------|-----------|
| 1 | Flow Field | None | Easy |
| 2 | L-System Tree | None | Easy |
| 3 | Voronoi Cells | scipy | Medium |
| 4 | Spiral Patterns | None | Easy |
| 5 | Reaction-Diffusion | numpy | Hard |
| 6 | Subdivision Grid | None | Easy |
| 7 | Hatching Portrait | PIL | Medium |
| 8 | Space-Filling Curve | None | Easy |
| 9 | Topographic Contours | numpy | Medium |
| 10 | Cellular Automata | None | Easy |

## Version

1.0.0 -- Initial release, April 2026
