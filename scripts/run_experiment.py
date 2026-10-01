"""Run a SafePaste system on a dataset and persist predictions and metrics."""
from __future__ import annotations

import argparse
import json
import shutil
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from safepaste.evaluation import evaluate_predictions, gold_spans_from_record
from safepaste.gliner_detector import GLiNERDetector
from safepaste.pipeline import SafePastePipeline
from safepaste.types import Span


SYSTEMS = {"presidio", "gliner", "hybrid"}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def record_id(index: int, record: dict) -> str:
    return str(record.get("id") or f"record-{index + 1:05d}")


def make_pipeline(system: str, config: dict) -> SafePastePipeline:
    if system not in SYSTEMS:
        raise ValueError(f"system must be one of {sorted(SYSTEMS)}")
    if system in {"gliner", "hybrid"}:
        gliner_config = config["gliner"]
        gliner = GLiNERDetector(
            typed_threshold=float(gliner_config["typed_threshold"]),
            abstain_threshold=float(gliner_config["abstain_threshold"]),
            local_files_only=bool(gliner_config.get("local_files_only", True)),
        )
        return SafePastePipeline(system, gliner=gliner)
    return SafePastePipeline("presidio")


def output_dir_for(path: Path, system: str) -> Path:
    if path.suffix:
        return path
    return path


def run_experiment(
    dataset_path: Path,
    system: str,
    config_path: Path,
    output_dir: Path,
    limit: int | None = None,
    progress_every: int = 100,
) -> dict:
    config = load_json(config_path)
    label_mapping = load_json(Path(config["label_mapping"]["path"]))
    records = load_json(dataset_path)
    if limit is not None:
        records = records[:limit]

    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(config_path, output_dir / "config.json")
    pipeline = make_pipeline(system, config)
    total_records = len(records)
    if progress_every > 0:
        print(
            f"[{system}] start records={total_records} dataset={dataset_path} output={output_dir}",
            flush=True,
        )

    predictions: list[list[Span]] = []
    errors: list[dict] = []
    runtime_values: list[float] = []
    log_lines = [
        f"started_at={datetime.now(timezone.utc).isoformat()}",
        f"dataset={dataset_path}",
        f"system={system}",
        f"records={len(records)}",
        f"limit={limit}",
    ]

    with (output_dir / "predictions.jsonl").open("w", encoding="utf-8") as pred_file, (output_dir / "errors.jsonl").open("w", encoding="utf-8") as err_file:
        for index, record in enumerate(records):
            rid = record_id(index, record)
            started = time.perf_counter()
            warnings: list[str] = []
            spans: list[Span] = []
            try:
                spans, warnings = pipeline.detect(str(record["text"]))
            except Exception as exc:  # Keep the run recoverable and auditable.
                errors.append({"record_id": rid, "error": str(exc), "error_type": type(exc).__name__})
            elapsed_ms = (time.perf_counter() - started) * 1000
            runtime_values.append(elapsed_ms)
            predictions.append(spans)
            gold, skipped = gold_spans_from_record(record, label_mapping)
            row = {
                "record_id": rid,
                "system": system,
                "runtime_ms": elapsed_ms,
                "gold_spans": [asdict(span) for span in gold],
                "predicted_spans": [span.to_dict() for span in spans],
                "warnings": warnings,
                **skipped,
            }
            pred_file.write(json.dumps(row, ensure_ascii=False) + "\n")
            if errors and errors[-1]["record_id"] == rid:
                err_file.write(json.dumps(errors[-1], ensure_ascii=False) + "\n")
            completed = index + 1
            if progress_every > 0 and (completed == total_records or completed % progress_every == 0):
                average_ms = sum(runtime_values) / len(runtime_values)
                percent = (completed / total_records * 100) if total_records else 100.0
                print(
                    f"[{system}] {completed}/{total_records} ({percent:.1f}%) "
                    f"avg_ms={average_ms:.1f} last_ms={elapsed_ms:.1f} errors={len(errors)}",
                    flush=True,
                )

    metrics = evaluate_predictions(records, predictions, label_mapping)
    metrics.update({"system": system, "dataset": str(dataset_path), "config": str(config_path), "errors": len(errors)})
    runtime = runtime_summary(runtime_values)
    runtime.update({"system": system, "records": len(records)})
    (output_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "runtime.json").write_text(json.dumps(runtime, ensure_ascii=False, indent=2), encoding="utf-8")
    log_lines.extend(
        [
            f"finished_at={datetime.now(timezone.utc).isoformat()}",
            f"errors={len(errors)}",
            f"predicted_spans={metrics['predicted_spans']}",
            f"gold_spans={metrics['gold_spans']}",
        ]
    )
    (output_dir / "run.log").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    if progress_every > 0:
        print(
            f"[{system}] finished records={len(records)} predicted_spans={metrics['predicted_spans']} "
            f"errors={len(errors)} output={output_dir}",
            flush=True,
        )
    return {"metrics": metrics, "runtime": runtime, "output_dir": str(output_dir)}


def runtime_summary(values: list[float]) -> dict:
    if not values:
        return {"mean_ms": 0.0, "p95_ms": 0.0, "total_ms": 0.0}
    ordered = sorted(values)
    p95_index = min(len(ordered) - 1, int(len(ordered) * 0.95))
    return {
        "mean_ms": sum(values) / len(values),
        "p95_ms": ordered[p95_index],
        "total_ms": sum(values),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--system", choices=sorted(SYSTEMS), required=True)
    parser.add_argument("--config", type=Path, default=Path("configs/final_experiment.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--progress-every", type=int, default=100)
    args = parser.parse_args()
    result = run_experiment(
        args.dataset,
        args.system,
        args.config,
        output_dir_for(args.output, args.system),
        args.limit,
        args.progress_every,
    )
    print(json.dumps({"output": result["output_dir"], "metrics": result["metrics"], "runtime": result["runtime"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
