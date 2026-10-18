# Changelog

## 1.1.0 (2026-04-07)

Ship-block fixes and a substantial content expansion.

- **All 10 generators now ship as working code**, not just documentation.
  Added: spiral, reaction_diffusion, subdivision, hatching,
  space_filling, topographic, cellular_automata.
- **New shared `plotter_utils.py`** module consolidates PaperSize,
  paths_to_svg, optimize_stroke_order, plot-time estimation and the
  clip / fit helpers that every generator needs. All ten generators
  import from it.
- **30 pre-plotted example SVGs** live in `content/examples/`, three
  seeds per generator, with a `MANIFEST.md` listing seed, paths,
  plot time and file size for every example plus PNG previews
  rasterised at 800 px.
- **Real AI scoring run** on a 10-piece sample of the gallery lives
  at `content/examples/score_log.json`. Average overall 7.2 / 10.
- **Guide expanded from ~1,900 to ~5,700 words**, including:
  measured stroke-travel before/after numbers (17-19x air-travel
  reduction), 4 mermaid diagrams, 30 named parameter recipes,
  AxiDraw and iDraw setup walkthroughs, a failure-mode gallery,
  an FAQ and a "common gotchas" section.
- **voronoi.py** no longer silently falls back to drawing diamonds
  when scipy is missing. It now fails hard with an install hint.
- **l_system.py** now imports and runs `optimize_stroke_order`.
- **All generators** now embed their full parameter dump, measured
  draw-travel, measured air-travel and plot-time estimate in the
  SVG header as XML comments.
- **Paper sizes** now include A5 in addition to A4, A3, Letter.

## 1.0.0 (2026-04-02)

Initial release.

- 10 generator algorithms documented with parameter guides
- 3 complete generators with full source (flow field, L-system, Voronoi)
- AI scoring script (Gemini + OpenAI providers)
- 5-chapter guide: setup, algorithms, SVG optimization, scoring rubric, plotter setup
- Stroke ordering optimization (nearest-neighbor)
- Paper size configs (A4, A3, Letter)
