"""Sweep GLiNER thresholds on the development split only."""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import time
from pathlib import Path

from safepaste.evaluation import evaluate_predictions, gold_spans_from_record, score
from safepaste.gliner_detector import GLiNERDetector
from safepaste.pipeline import resolve_overlaps
from safepaste.types import Span


DEFAULT_TYPED_THRESHOLDS = [0.45, 0.50, 0.55, 0.60, 0.65, 0.70]
DEFAULT_ABSTAIN_THRESHOLDS = [0.20, 0.25, 0.30, 0.35, 0.40]


def parse_thresholds(value: str) -> list[float]:
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def record_id(index: int, record: dict) -> str:
    return str(record.get("id") or f"dev-{index + 1:05d}")


def cache_gliner_predictions(records: list[dict], abstain_floor: float, model_path: str | None = None) -> tuple[list[list[dict]], list[float]]:
    detector = GLiNERDetector(model_path=model_path, typed_threshold=1.0, abstain_threshold=abstain_floor)
    cached: list[list[dict]] = []
    runtime_ms: list[float] = []
    for record in records:
        started = time.perf_counter()
        spans = detector.detect(record["text"])
        runtime_ms.append((time.perf_counter() - started) * 1000)
        cached.append([span.to_dict(record["text"]) for span in spans])
    return cached, runtime_ms


def predictions_for_thresholds(cached: list[list[dict]], typed_threshold: float, abstain_threshold: float) -> list[list[Span]]:
    predictions: list[list[Span]] = []
    for record_spans in cached:
        spans = [
            Span(
                start=int(item["start"]),
                end=int(item["end"]),
                label=str(item["label"]),
                score=float(item["score"]),
                source=str(item["source"]),
                abstained=float(item["score"]) < typed_threshold,
                recognizer_name=item.get("recognizer_name"),
            )
            for item in record_spans
            if float(item["score"]) >= abstain_threshold
        ]
        predictions.append(resolve_overlaps(spans))
    return predictions


def per_label_overlap_typed_recall(records: list[dict], predictions: list[list[Span]], label_mapping: dict) -> dict[str, float]:
    labels = list(label_mapping.get("target_labels", []))
    matched = {label: 0 for label in labels}
    totals = {label: 0 for label in labels}
    for record, preds in zip(records, predictions, strict=True):
        gold, _ = gold_spans_from_record(record, label_mapping)
        for label in labels:
            label_gold = [item for item in gold if item.label == label]
            label_preds = [item for item in preds if item.label == label and not item.abstained]
            counts = score(label_preds, label_gold, boundary="overlap", include_abstained=False, require_label=True)
            matched[label] += counts.matched
            totals[label] += counts.gold
    return {f"overlap_typed_recall_{label}": (matched[label] / totals[label] if totals[label] else 1.0) for label in labels}


def run_sweep(records: list[dict], cached: list[list[dict]], label_mapping: dict, typed_thresholds: list[float], abstain_thresholds: list[float]) -> list[dict]:
    rows: list[dict] = []
    for typed_threshold in typed_thresholds:
        for abstain_threshold in abstain_thresholds:
            if abstain_threshold >= typed_threshold:
                continue
            predictions = predictions_for_thresholds(cached, typed_threshold, abstain_threshold)
            metrics = evaluate_predictions(records, predictions, label_mapping)
            per_label = per_label_overlap_typed_recall(records, predictions, label_mapping)
            rows.append(
                {
                    "typed_threshold": typed_threshold,
                    "abstain_threshold": abstain_threshold,
                    **metrics,
                    **per_label,
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("No rows to write")
    fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_prediction_cache(path: Path, records: list[dict], cached: list[list[dict]], runtime_ms: list[float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for index, (record, spans, elapsed) in enumerate(zip(records, cached, runtime_ms, strict=True)):
            handle.write(
                json.dumps(
                    {
                        "record_id": record_id(index, record),
                        "runtime_ms": elapsed,
                        "raw_gliner_spans": spans,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )


def runtime_summary(runtime_ms: list[float]) -> dict:
    if not runtime_ms:
        return {"records": 0, "mean_ms": 0, "p95_ms": 0}
    sorted_values = sorted(runtime_ms)
    p95_index = min(len(sorted_values) - 1, int(len(sorted_values) * 0.95))
    return {
        "records": len(runtime_ms),
        "mean_ms": statistics.fmean(runtime_ms),
        "p95_ms": sorted_values[p95_index],
        "total_ms": sum(runtime_ms),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=Path("data/ai4privacy_split/development_2000.json"))
    parser.add_argument("--label-mapping", type=Path, default=Path("configs/label_mapping.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/threshold_tuning"))
    parser.add_argument("--typed-thresholds", default=",".join(str(item) for item in DEFAULT_TYPED_THRESHOLDS))
    parser.add_argument("--abstain-thresholds", default=",".join(str(item) for item in DEFAULT_ABSTAIN_THRESHOLDS))
    parser.add_argument("--limit", type=int)
    parser.add_argument("--model-path")
    args = parser.parse_args()

    records = load_json(args.dataset)
    if args.limit is not None:
        records = records[: args.limit]
    label_mapping = load_json(args.label_mapping)
    typed_thresholds = parse_thresholds(args.typed_thresholds)
    abstain_thresholds = parse_thresholds(args.abstain_thresholds)
    abstain_floor = min(abstain_thresholds)

    cached, runtime_ms = cache_gliner_predictions(records, abstain_floor, args.model_path)
    rows = run_sweep(records, cached, label_mapping, typed_thresholds, abstain_thresholds)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "threshold_sweep.csv", rows)
    write_prediction_cache(args.output_dir / "raw_gliner_predictions.jsonl", records, cached, runtime_ms)
    summary = {
        "dataset": str(args.dataset),
        "records": len(records),
        "label_mapping": str(args.label_mapping),
        "typed_thresholds": typed_thresholds,
        "abstain_thresholds": abstain_thresholds,
        "runtime": runtime_summary(runtime_ms),
        "frozen_evaluation_used": False,
    }
    (args.output_dir / "runtime_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"rows": len(rows), "output": str(args.output_dir), "records": len(records)}, indent=2))


if __name__ == "__main__":
    main()
