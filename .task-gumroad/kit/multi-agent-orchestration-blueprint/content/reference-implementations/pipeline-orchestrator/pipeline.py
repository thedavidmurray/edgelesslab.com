#!/usr/bin/env python3
"""
Pipeline Orchestrator Reference Implementation

A linear pipeline where each stage processes the output of the previous stage.
Includes checkpoint-based recovery so failed pipelines resume from the last
successful stage.

Usage:
    python pipeline.py --config pipeline.json --input input.json

pipeline.json defines stages:
{
  "name": "rss-intelligence",
  "stages": [
    {"name": "fetch_feeds", "agent": "worker-content", "timeout": 120},
    {"name": "score_articles", "agent": "worker-research", "timeout": 180},
    {"name": "format_digest", "agent": "worker-content", "timeout": 60}
  ]
}
"""

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4


@dataclass
class PipelineStage:
    name: str
    agent: str
    timeout: int = 300  # seconds


@dataclass
class StageResult:
    stage: str
    output: dict
    duration_seconds: float
    agent: str


class PipelineError(Exception):
    def __init__(self, stage: str, error: str, partial_results: list[StageResult]):
        self.stage = stage
        self.error = error
        self.partial_results = partial_results
        super().__init__(f"Pipeline failed at stage '{stage}': {error}")


class Pipeline:
    def __init__(self, name: str, stages: list[PipelineStage]):
        self.name = name
        self.stages = stages

    def execute(
        self,
        input_data: dict,
        checkpoint_dir: str = ".pipeline-checkpoints",
        stage_handler=None,
        resume_id: str | None = None,
    ) -> dict:
        """
        Execute pipeline stages sequentially with checkpointing.

        stage_handler: callable(stage, input_data) -> dict
            A function that processes a single stage. Replace with your
            Agent Bus integration or direct function calls.
            If None, uses a placeholder that passes data through.

        resume_id: str | None
            If provided, resume from an existing checkpoint directory with
            that pipeline_id. Any stage-N.json files already present will be
            loaded as finished stages and execution will continue from the
            first missing stage. If None, a new pipeline_id is generated and
            a fresh checkpoint directory is created.

            Design trade-off: we use an explicit opt-in --resume flag rather
            than deriving the id from a content hash of the inputs. Content
            hashing sounds cleaner but fails in practice because (a) inputs
            often contain timestamps or request ids that change every run,
            producing a new hash and silently orphaning checkpoints, and
            (b) it hides the resume behavior from the operator. Explicit
            --resume makes the retry intent visible in logs and shell history.
        """
        if resume_id:
            pipeline_id = resume_id
            cp_path = Path(checkpoint_dir) / pipeline_id
            if not cp_path.exists():
                raise FileNotFoundError(
                    f"Cannot resume: checkpoint dir not found at {cp_path}. "
                    f"Run without --resume to start a new pipeline."
                )
            print(f"[{pipeline_id}] Resuming existing pipeline from {cp_path}")
        else:
            pipeline_id = f"{self.name}-{uuid4().hex[:8]}"
            cp_path = Path(checkpoint_dir) / pipeline_id
            cp_path.mkdir(parents=True, exist_ok=True)

        current = input_data
        results: list[StageResult] = []

        if stage_handler is None:
            stage_handler = _default_handler

        print(f"[{pipeline_id}] Starting pipeline: {self.name}")
        print(f"  Stages: {' -> '.join(s.name for s in self.stages)}")

        for i, stage in enumerate(self.stages):
            # Check for existing checkpoint
            cp_file = cp_path / f"stage-{i}.json"
            if cp_file.exists():
                print(f"[{pipeline_id}] Resuming from checkpoint: stage {i} ({stage.name})")
                current = json.loads(cp_file.read_text())
                results.append(StageResult(
                    stage=stage.name,
                    output=current,
                    duration_seconds=0,
                    agent=stage.agent,
                ))
                continue

            print(f"[{pipeline_id}] Stage {i + 1}/{len(self.stages)}: "
                  f"{stage.name} -> {stage.agent}")

            start_time = time.time()

            try:
                result = stage_handler(stage, current)
            except Exception as e:
                raise PipelineError(
                    stage=stage.name,
                    error=str(e),
                    partial_results=results,
                )

            duration = time.time() - start_time

            if result.get("error"):
                raise PipelineError(
                    stage=stage.name,
                    error=result["error"],
                    partial_results=results,
                )

            output = result.get("output", result)
            stage_result = StageResult(
                stage=stage.name,
                output=output,
                duration_seconds=duration,
                agent=stage.agent,
            )
            results.append(stage_result)

            # Save checkpoint
            cp_file.write_text(json.dumps(output, indent=2, default=str))
            current = output

            print(f"  Completed in {duration:.1f}s")

        summary = {
            "pipeline_id": pipeline_id,
            "name": self.name,
            "stages": [
                {"name": r.stage, "agent": r.agent, "duration_s": round(r.duration_seconds, 1)}
                for r in results
            ],
            "total_duration_s": round(sum(r.duration_seconds for r in results), 1),
            "output": current,
        }

        print(f"[{pipeline_id}] Pipeline complete in {summary['total_duration_s']}s")
        return summary


def _default_handler(stage: PipelineStage, input_data: dict) -> dict:
    """
    Default stage handler -- passes data through.
    Replace this with your Agent Bus integration:

        async def bus_handler(stage, input_data):
            task_id = f"pipeline-stage-{stage.name}"
            await bus.send(stage.agent, json.dumps({
                "task_id": task_id,
                "stage": stage.name,
                "input": input_data,
            }), type="request")
            return await bus.wait_for_response(task_id, timeout=stage.timeout * 1000)
    """
    # Simulate processing
    time.sleep(0.5)
    return {"output": {**input_data, f"_{stage.name}_processed": True}}


def load_pipeline(config_path: str) -> Pipeline:
    """Load pipeline definition from JSON config."""
    with open(config_path) as f:
        config = json.load(f)

    stages = [
        PipelineStage(
            name=s["name"],
            agent=s.get("agent", "default"),
            timeout=s.get("timeout", 300),
        )
        for s in config["stages"]
    ]

    return Pipeline(name=config["name"], stages=stages)


def main():
    parser = argparse.ArgumentParser(description="Pipeline Orchestrator")
    parser.add_argument("--config", required=True, help="Pipeline config JSON")
    parser.add_argument("--input", required=True, help="Input data JSON")
    parser.add_argument("--checkpoint-dir", default=".pipeline-checkpoints")
    parser.add_argument("--output", help="Save results to JSON file")
    parser.add_argument(
        "--resume",
        metavar="PIPELINE_ID",
        help="Resume an existing pipeline by id (must exist under --checkpoint-dir).",
    )
    args = parser.parse_args()

    pipeline = load_pipeline(args.config)

    with open(args.input) as f:
        input_data = json.load(f)

    result = pipeline.execute(
        input_data,
        checkpoint_dir=args.checkpoint_dir,
        resume_id=args.resume,
    )

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\nResults saved to {args.output}")
    else:
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
