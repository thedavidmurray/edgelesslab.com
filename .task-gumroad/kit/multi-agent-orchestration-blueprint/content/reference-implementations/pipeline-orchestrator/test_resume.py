#!/usr/bin/env python3
"""
Smoke test for Pipeline checkpoint resume.

Runs a pipeline that deliberately fails at stage 3, captures the pipeline_id,
then resumes with --resume and verifies:
  1. Stages 1 and 2 are NOT re-executed (their handler counters don't increment)
  2. Stage 3 runs successfully on the retry
  3. Final output reflects all three stages

Exit code: 0 on success, non-zero on failure.

Run: python3 test_resume.py
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline import Pipeline, PipelineStage, PipelineError  # pyright: ignore[reportMissingImports]


def make_handler(fail_stage: str | None, counters: dict):
    """Build a stage handler that increments per-stage counters and
    optionally raises on a named stage."""

    def handler(stage: PipelineStage, input_data: dict) -> dict:
        counters[stage.name] = counters.get(stage.name, 0) + 1
        if stage.name == fail_stage:
            return {"error": f"synthetic failure at {stage.name}"}
        return {
            "output": {
                **input_data,
                f"{stage.name}_ran": True,
                f"{stage.name}_count": counters[stage.name],
            }
        }

    return handler


def main() -> int:
    tmpdir = Path(tempfile.mkdtemp(prefix="pipeline-resume-test-"))
    try:
        checkpoint_dir = tmpdir / "checkpoints"
        pipeline = Pipeline(
            name="resume-test",
            stages=[
                PipelineStage("fetch", "worker-a"),
                PipelineStage("score", "worker-b"),
                PipelineStage("format", "worker-c"),
            ],
        )

        # --- Run 1: fail at stage "format" ---
        counters_run1: dict = {}
        handler_fail = make_handler("format", counters_run1)
        pipeline_id = None
        try:
            pipeline.execute(
                {"seed": 1},
                checkpoint_dir=str(checkpoint_dir),
                stage_handler=handler_fail,
            )
            print("FAIL: pipeline should have raised PipelineError")
            return 1
        except PipelineError as exc:
            # Find the pipeline_id by inspecting the checkpoint dir.
            subdirs = [p for p in checkpoint_dir.iterdir() if p.is_dir()]
            if len(subdirs) != 1:
                print(f"FAIL: expected 1 checkpoint dir, got {len(subdirs)}")
                return 1
            pipeline_id = subdirs[0].name
            print(f"Run 1 failed as expected at stage '{exc.stage}' "
                  f"(pipeline_id={pipeline_id})")

        # Verify stages 0 and 1 left checkpoint files behind.
        cp_dir = checkpoint_dir / pipeline_id
        assert (cp_dir / "stage-0.json").exists(), "missing stage-0 checkpoint"
        assert (cp_dir / "stage-1.json").exists(), "missing stage-1 checkpoint"
        assert not (cp_dir / "stage-2.json").exists(), \
            "stage-2 checkpoint should not exist yet"

        # Run 1 counters: fetch=1, score=1, format=1 (ran and failed).
        assert counters_run1 == {"fetch": 1, "score": 1, "format": 1}, \
            f"unexpected run1 counters: {counters_run1}"

        # --- Run 2: resume with no failure ---
        counters_run2: dict = {}
        handler_ok = make_handler(None, counters_run2)
        result = pipeline.execute(
            {"seed": 1},
            checkpoint_dir=str(checkpoint_dir),
            stage_handler=handler_ok,
            resume_id=pipeline_id,
        )

        # Stages 0 and 1 must NOT have been re-executed on resume.
        assert "fetch" not in counters_run2, \
            f"stage 'fetch' was re-executed on resume: {counters_run2}"
        assert "score" not in counters_run2, \
            f"stage 'score' was re-executed on resume: {counters_run2}"
        # Stage "format" must have run exactly once on resume.
        assert counters_run2.get("format") == 1, \
            f"stage 'format' expected 1 run on resume, got {counters_run2}"

        # The returned pipeline_id must match the resumed one.
        assert result["pipeline_id"] == pipeline_id, \
            f"pipeline_id mismatch: {result['pipeline_id']} != {pipeline_id}"

        # Final output must carry the stage-3 marker.
        assert result["output"].get("format_ran") is True, \
            f"final output missing format_ran: {result['output']}"

        # All 3 stage-N.json checkpoints should now exist.
        assert (cp_dir / "stage-2.json").exists(), \
            "stage-2 checkpoint missing after successful resume"

        print("PASS: resume skipped completed stages and finished pipeline")
        return 0
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
