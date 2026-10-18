# /// script
# requires-python = ">=3.11"
# dependencies = ["marimo==0.23.16"]
# ///
import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return mo


@app.cell
def _(mo):
    mo.md(r"""# What does a “2-bit KV cache” actually store?

    **Question.** When only MLA's content latent uses low-bit codes, how do
    metadata and the BF16 positional key change the whole-cache precision and
    capacity ratio?

    RoLaQ reports a packed **2-bit content latent**, not a two-bit encoding of
    every cached coordinate. The defaults below reproduce Appendix A.3 for
    DeepSeek-V2-Lite. Moving either control is an **analyst-authored storage
    sensitivity**, not another configuration evaluated by the paper.
    """)
    code_bits = mo.ui.slider(2, 8, value=2, step=1, label="Content code width (bits)")
    group_size = mo.ui.slider(32, 256, value=128, step=32, label="Coordinates per metadata group")
    mo.hstack([code_bits, group_size], justify="start", gap=2)
    return code_bits, group_size


@app.cell
def _(code_bits, group_size, mo):
    _d_content = 512
    _d_rope = 64
    _bits = int(code_bits.value)
    _group = int(group_size.value)
    _code_bytes = _d_content * _bits / 8
    _metadata_bytes = (_d_content / _group) * 2 * 4
    _rope_bytes = _d_rope * 2
    _total_bytes = _code_bytes + _metadata_bytes + _rope_bytes
    _bf16_bytes = (_d_content + _d_rope) * 2
    _effective_bits = _total_bytes * 8 / (_d_content + _d_rope)
    _capacity_ratio = _bf16_bytes / _total_bytes
    _measured_gap = 4.0 - 3.96
    _scale = 540 / _bf16_bytes
    _w_code = _code_bytes * _scale
    _w_meta = _metadata_bytes * _scale
    _w_rope = _rope_bytes * _scale
    _marker = f"bits-{_bits}-group-{_group}-bytes-{_total_bytes:.0f}"
    _chart = f'''<svg data-chart="rolaq-cache-accounting" data-marker="{_marker}"
      viewBox="0 0 720 320" role="img" aria-label="Per-token per-layer MLA cache storage">
      <rect width="720" height="320" rx="12" fill="#f5f7fb"/>
      <text x="28" y="36" font-size="18" font-weight="700">Bytes per token per layer</text>
      <text x="28" y="61" font-size="12" fill="#526071">DeepSeek-V2-Lite dimensions: content 512 + RoPE 64</text>
      <text x="28" y="110" font-size="14">Selected</text>
      <rect x="145" y="86" width="{_w_code:.1f}" height="38" fill="#6554c0"/>
      <rect x="{145 + _w_code:.1f}" y="86" width="{_w_meta:.1f}" height="38" fill="#d97706"/>
      <rect x="{145 + _w_code + _w_meta:.1f}" y="86" width="{_w_rope:.1f}" height="38" fill="#0891b2"/>
      <text x="{153 + _w_code + _w_meta + _w_rope:.1f}" y="111" font-size="13">{_total_bytes:.0f} B</text>
      <text x="28" y="180" font-size="14">BF16 MLA</text>
      <rect x="145" y="156" width="540" height="38" fill="#94a3b8"/>
      <text x="612" y="181" font-size="13" fill="white">{_bf16_bytes:.0f} B</text>
      <rect x="145" y="235" width="16" height="16" fill="#6554c0"/><text x="168" y="248" font-size="12">content codes {_code_bytes:.0f} B</text>
      <rect x="330" y="235" width="16" height="16" fill="#d97706"/><text x="353" y="248" font-size="12">FP32 metadata {_metadata_bytes:.0f} B</text>
      <rect x="540" y="235" width="16" height="16" fill="#0891b2"/><text x="563" y="248" font-size="12">BF16 RoPE {_rope_bytes:.0f} B</text>
      <text x="28" y="292" font-size="12" fill="#526071">Capacity ceiling = BF16 bytes / selected bytes; allocator and protected-token overhead are excluded.</text>
    </svg>'''
    _status = "paper default" if (_bits, _group) == (2, 128) else "hypothetical sensitivity"
    mo.vstack([
        mo.md(f"""## Operating point: {_bits}-bit content / group {_group} / {_total_bytes:.0f} bytes

        **Whole-cache effective precision: {_effective_bits:.3f} bits per stored coordinate.**
        The arithmetic capacity ceiling is **{_capacity_ratio:.3f}× BF16** ({_status}).
        At the paper default this is 4.000×, while its measured capacity ratio is
        3.96×—a {_measured_gap:.2f}× absolute gap from serving overheads."""),
        mo.Html(_chart),
    ], gap=1)
    return


@app.cell
def _(mo):
    mo.md(r"""**Takeaway.** A precision label should name the compressed component.
    At RoLaQ's published default, 128 B of INT2 codes plus 32 B of FP32 group
    statistics and 128 B of BF16 RoPE state total 288 B—not 144 B, which a
    literal two-bit encoding of all 576 coordinates would imply.

    **Provenance.** Ji et al., *RoLaQ: Joint Rotation and Range Calibration for
    2-Bit KV Caches in Multi-Head Latent Attention*, arXiv:2610.20686v1,
    https://arxiv.org/abs/2610.20686 . Appendix A.3 gives `d=512`, `d_r=64`,
    group size 128, two FP32 statistics per group, and a BF16 RoPE key. The
    paper reports 1.15M versus 4.56M tokens (3.96×) under equal memory budgets.

    **Limits.** This demo reproduces storage arithmetic only. It does not run
    RoLaQ, quantize activations, evaluate accuracy, execute CUDA/SGLang, measure
    capacity or throughput, or validate the paper's author-run 2.51× decode
    result. Non-default control values are hypothetical. Original demo code is
    prepared for MIT release and copies no paper code, data, or figures.
    """)
    return


if __name__ == "__main__":
    app.run()
