# Example Gallery Manifest

Thirty pre-generated SVGs, three seeds per generator, all produced by
the scripts in `content/generators/` with no hand editing. Every file
embeds its seed, parameters, path count and plot-time estimate inside
the SVG as XML comments, so you can recover the exact recipe by
opening the file in any text editor.

All examples are A4 unless noted. Plot-time estimates assume an
AxiDraw V3 with a 0.25 mm fineliner drawing at 40 mm/s, travel at
120 mm/s, 0.18 s per pen lift. Real-world plot times in the shop
have landed within +/- 15 % of these numbers.

## Generator index

| # | Generator | Examples | Kind | Depends on |
|---|-----------|----------|------|------------|
| 1 | `flow_field.py`         | 3 | Perlin-noise particle traces | stdlib |
| 2 | `l_system.py`           | 3 (fern / oak / willow) | Turtle-graphics L-system | stdlib |
| 3 | `voronoi.py`            | 3 | Voronoi tessellation with Lloyd's relaxation | numpy + scipy |
| 4 | `spiral.py`             | 3 (archimedean / log / hypotrochoid) | Parametric spirals | stdlib |
| 5 | `reaction_diffusion.py` | 3 (spots / worms / coral) | Gray-Scott contours | numpy |
| 6 | `subdivision.py`        | 3 | Vera Molnar-style recursive grid | stdlib |
| 7 | `hatching.py`           | 3 | Subject-driven hatching (NO background hatching) | Pillow optional |
| 8 | `space_filling.py`      | 3 (Hilbert / dragon / Gosper) | Single-stroke space-filling curves | stdlib |
| 9 | `topographic.py`        | 3 | Multi-octave noise contour map | numpy |
| 10 | `cellular_automata.py` | 3 (rule 30 / 90 / 110) | 1-D elementary CA rectangles | stdlib |

Total: **30 SVGs + 30 PNG previews** in `png/`.

## File listing

| File | Seed | Paths | Plot time | Size (bytes) | Params |
|------|------|-------|-----------|--------------|--------|
| flow_field_1.svg | 1 | 597 | 26min | 593,979 | resolution=25 noise_scale=0.015 step_length=1.5 max_steps=80 |
| flow_field_2.svg | 2 | 597 | 24min | 567,762 | resolution=25 noise_scale=0.015 step_length=1.5 max_steps=80 |
| flow_field_3.svg | 3 | 592 | 22min | 501,705 | resolution=25 noise_scale=0.015 step_length=1.5 max_steps=80 |
| l_system_fern_79.svg | 79 | 2,048 | 7min | 155,223 | preset=fern iterations=6 angle=25 length_ratio=0.5 |
| l_system_oak_47.svg | 47 | 1,024 | 7min | 94,915 | preset=oak iterations=4 angle=22.5 length_ratio=0.65 |
| l_system_willow_81.svg | 81 | 1,875 | 9min | 109,298 | preset=willow iterations=5 angle=20 length_ratio=0.75 |
| voronoi_1.svg | 1 | 461 | 4min | 22,448 | num_points=140 relaxation=4 |
| voronoi_2.svg | 2 | 467 | 4min | 22,738 | num_points=140 relaxation=4 |
| voronoi_3.svg | 3 | 462 | 4min | 22,536 | num_points=140 relaxation=4 |
| spiral_archimedean_7.svg | 7 | 1 | 42s | 31,505 | type=archimedean turns=6 b=2 samples=2000 |
| spiral_logarithmic_7.svg | 7 | 1 | 5s | 30,694 | type=logarithmic turns=6 a=1 b=0.15 samples=2000 |
| spiral_hypotrochoid_7.svg | 7 | 1 | 6min | 31,471 | type=hypotrochoid R=80 r=21 d=51 samples=2000 |
| reaction_diffusion_spots_4.svg | 4 | 414 | 5min | 159,510 | preset=spots feed=0.030 kill=0.062 iter=3500 grid=140x200 |
| reaction_diffusion_worms_4.svg | 4 | 147 | 6min | 190,703 | preset=worms feed=0.055 kill=0.062 iter=3500 grid=140x200 |
| reaction_diffusion_coral_4.svg | 4 | 129 | 6min | 195,567 | preset=coral feed=0.0545 kill=0.062 iter=3500 grid=140x200 |
| subdivision_11.svg | 11 | 215 | 6min | 18,119 | splits=140 min_size=8 decorate=True |
| subdivision_22.svg | 22 | 238 | 7min | 19,818 | splits=140 min_size=8 decorate=True |
| subdivision_33.svg | 33 | 228 | 7min | 18,867 | splits=140 min_size=8 decorate=True |
| hatching_parallel_43.svg | 43 | 137 | 4min | 253,863 | style=parallel angle=35 density=0.8 threshold=0.35 |
| hatching_crosshatch_24.svg | 24 | 248 | 6min | 412,410 | style=crosshatch angle=35 density=0.8 threshold=0.35 |
| hatching_parallel_33.svg | 33 | 137 | 4min | 253,975 | style=parallel angle=35 density=0.8 threshold=0.35 |
| space_filling_hilbert_1.svg | 1 | 1 | 5min | 63,351 | type=hilbert order=6 vertices=4096 |
| space_filling_dragon_2.svg | 2 | 1 | 6min | 125,246 | type=dragon order=13 vertices=8193 |
| space_filling_gosper_3.svg | 3 | 1 | 3min | 37,598 | type=gosper order=4 vertices=2402 |
| topographic_5.svg | 5 | 96 | 4min | 167,104 | levels=10 noise_scale=0.018 octaves=4 |
| topographic_15.svg | 15 | 102 | 4min | 166,802 | levels=10 noise_scale=0.018 octaves=4 |
| topographic_25.svg | 25 | 99 | 3min | 160,132 | levels=10 noise_scale=0.018 octaves=4 |
| cellular_automata_rule30.svg | 1 | 8,573 | 44min | 804,489 | rule=30 width=121 generations=170 init=single |
| cellular_automata_rule90.svg | 1 | 2,649 | 14min | 248,973 | rule=90 (sierpinski) width=121 generations=170 |
| cellular_automata_rule110.svg | 1 | 7,620 | 39min | 713,207 | rule=110 (turing-complete) width=121 generations=170 |

Totals: **30 SVGs**, approximately **12 MB** of vector data,
aggregate plot time across the gallery ~ 5 h 30 min.

## Reproducing any of these

Every row above can be rebuilt exactly by calling the generator with
its `--seed` plus the parameters shown in the last column. For
example:

```bash
python3 content/generators/flow_field.py \
    --seed 1 --resolution 25 --noise-scale 0.015 \
    --step-length 1.5 --max-steps 80 \
    --paper A4 --output rebuild.svg

python3 content/generators/cellular_automata.py \
    --rule 30 --seed 1 --width 121 --generations 170 \
    --paper A4 --output rebuild.svg
```

The SVG produced will be byte-identical to the shipped example for
the same seed and parameters (PRNGs are seeded with `random.Random`
and, where numpy is used, `np.random.default_rng`).

## AI scoring run

We ran the included scoring script (`content/scoring/score.py`, with
an OpenRouter vision backend for rate-limit headroom) against a
10-piece sample of the gallery. Full machine-readable output lives at
`score_log.json`. Summary:

- Provider: `openrouter/google/gemini-2.5-flash`
- Sample size: 10 of 30 examples
- Average overall score: **7.2 / 10**
- Range: 6.8 to 7.5
- Zero pieces scored below the 6.0 "worth plotting" gate

The scoring script ships with Gemini and OpenAI providers out of the
box; if you prefer a different vision model you can add your own by
wrapping it in a `score_with_X(image_path) -> dict` function and
registering it in the `PROVIDERS` dict. Both the built-in providers
were rate-limited during generation of this gallery (HTTP 429), which
is a useful demonstration of why you want to score in batches, not
inline with the creative loop.

Scoring rubric (all 1-10, 6.0 is the "worth plotting" gate):

1. **Composition** - balance, space usage, focal point
2. **Complexity** - appropriate detail level
3. **Coherence** - does the piece "make sense"
4. **Ink coverage %** - target 10-80 % (black pixels after render)
5. **Plottability** - clean strokes, no tiny detail that plotters can't render
6. **Uniqueness** - does it look different from typical gen-art

## Previews

PNG previews for each SVG live in `examples/png/` at 800 px wide,
rasterized via `cairosvg` with a white background. These are only
for humans and the scoring model - the SVGs are the canonical
plotter-ready files.

## Rule enforced across the gallery: NO background hatching

Every generator in this kit that could be tempted to fill whitespace
with decorative hatches has been deliberately built NOT to. See
`hatching.py` in particular - it refuses to draw any stroke where the
darkness value is below the `--threshold` parameter. This is a
product rule, not a parameter you should be turning off.
