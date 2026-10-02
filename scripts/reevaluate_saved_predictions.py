"""Re-score saved SafePaste predictions with an alternate label mapping.

This script is for post-evaluation analysis. It does not rerun detectors or
modify official run directories; it reloads saved prediction spans and original
records, applies a supplied label mapping to gold spans, and writes separate
summary files.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from safepaste.evaluation import evaluate_predictions, gold_spans_from_record, score
from safepaste.types import Span


RUNS = [
    ("AI4Privacy frozen", "Presidio-only", Path("results/runs/presidio_frozen"), Path("data/ai4privacy_split/frozen_evaluation_3000.json")),
    ("AI4Privacy frozen", "GLiNER-only", Path("results/runs/gliner_frozen"), Path("data/ai4privacy_split/frozen_evaluation_3000.json")),
    ("AI4Privacy frozen", "Hybrid", Path("results/runs/hybrid_frozen"), Path("data/ai4privacy_split/frozen_evaluation_3000.json")),
    ("Singapore stress", "Presidio-only", Path("results/runs/presidio_stress"), Path("data/singapore_stress.json")),
    ("Singapore stress", "GLiNER-only", Path("results/runs/gliner_stress"), Path("data/singapore_stress.json")),
    ("Singapore stress", "Hybrid", Path("results/runs/hybrid_stress"), Path("data/singapore_stress.json")),
]

MAIN_COLUMNS = [
    "dataset",
    "system",
    "records",
    "gold_spans",
    "predicted_spans",
    "exact_typed_recall",
    "exact_protective_recall",
    "overlap_typed_recall",
    "overlap_protective_recall",
    "exact_typed_precision",
    "overlap_typed_precision",
    "abstention_rate",
    "errors",
]

PER_LABEL_COLUMNS = [
    "dataset",
    "system",
    "label",
    "gold_spans",
    "typed_predictions",
    "protective_predictions",
    "exact_typed_recall",
    "exact_protective_recall",
    "overlap_typed_recall",
    "overlap_protective_recall",
    "exact_typed_precision",
    "overlap_typed_precision",
]

REPORT_MAIN_COLUMNS = [
    ("system", "System"),
    ("records", "Records"),
    ("gold_spans", "Gold"),
    ("predicted_spans", "Pred."),
    ("exact_typed_recall", "Exact typed R"),
    ("exact_protective_recall", "Exact protective R"),
    ("overlap_typed_recall", "Overlap typed R"),
    ("overlap_protective_recall", "Overlap protective R"),
    ("exact_typed_precision", "Exact typed P"),
    ("overlap_typed_precision", "Overlap typed P"),
    ("abstention_rate", "Abstention"),
]

REPORT_PER_LABEL_COLUMNS = [
    ("label", "Label"),
    ("gold_spans", "Gold"),
    ("exact_typed_recall", "Exact typed R"),
    ("overlap_typed_recall", "Overlap typed R"),
    ("overlap_protective_recall", "Overlap protective R"),
    ("exact_typed_precision", "Exact typed P"),
    ("overlap_typed_precision", "Overlap typed P"),
]

SYSTEM_ORDER = {"Presidio-only": 0, "GLiNER-only": 1, "Hybrid": 2}
PERCENT_KEYS = {
    "exact_typed_recall",
    "exact_protective_recall",
    "overlap_typed_recall",
    "overlap_protective_recall",
    "exact_typed_precision",
    "overlap_typed_precision",
    "abstention_rate",
}
NUMBER_KEYS = {"records", "gold_spans", "predicted_spans", "typed_predictions", "protective_predictions", "errors"}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def spans_from_predictions(items: list[dict]) -> list[Span]:
    """Convert saved prediction dictionaries back to Span objects."""

    return [
        Span(
            int(item["start"]),
            int(item["end"]),
            str(item["label"]),
            float(item["score"]),
            str(item["source"]),
            bool(item.get("abstained", False)),
            item.get("recognizer_name"),
        )
        for item in items
    ]


def predictions_from_rows(rows: list[dict]) -> list[list[Span]]:
    """Extract per-record prediction spans from saved run rows."""

    return [spans_from_predictions(row["predicted_spans"]) for row in rows]


def per_label_metrics(dataset: str, system: str, records: list[dict], predictions: list[list[Span]], label_mapping: dict) -> list[dict]:
    """Compute per-label metrics after remapping gold spans with `label_mapping`."""

    normalized_gold = [gold_spans_from_record(record, label_mapping)[0] for record in records]
    labels = sorted({span.label for spans in normalized_gold for span in spans} | {span.label for spans in predictions for span in spans})
    output: list[dict] = []
    for label in labels:
        gold_total = 0
        pred_typed_total = 0
        pred_protective_total = 0
        counts = {
            "exact_typed": 0,
            "exact_protective": 0,
            "overlap_typed": 0,
            "overlap_protective": 0,
        }
        for gold_spans, pred_spans in zip(normalized_gold, predictions, strict=True):
            gold = [span for span in gold_spans if span.label == label]
            preds = [span for span in pred_spans if span.label == label]
            gold_total += len(gold)
            pred_typed_total += sum(not span.abstained for span in preds)
            pred_protective_total += len(preds)
            counts["exact_typed"] += score(preds, gold, boundary="exact", include_abstained=False, require_label=True).matched
            counts["exact_protective"] += score(preds, gold, boundary="exact", include_abstained=True, require_label=False).matched
            counts["overlap_typed"] += score(preds, gold, boundary="overlap", include_abstained=False, require_label=True).matched
            counts["overlap_protective"] += score(preds, gold, boundary="overlap", include_abstained=True, require_label=False).matched
        output.append(
            {
                "dataset": dataset,
                "system": system,
                "label": label,
                "gold_spans": gold_total,
                "typed_predictions": pred_typed_total,
                "protective_predictions": pred_protective_total,
                "exact_typed_recall": safe_div(counts["exact_typed"], gold_total),
                "exact_protective_recall": safe_div(counts["exact_protective"], gold_total),
                "overlap_typed_recall": safe_div(counts["overlap_typed"], gold_total),
                "overlap_protective_recall": safe_div(counts["overlap_protective"], gold_total),
                "exact_typed_precision": safe_div(counts["exact_typed"], pred_typed_total),
                "overlap_typed_precision": safe_div(counts["overlap_typed"], pred_typed_total),
            }
        )
    return output


def safe_div(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def percent(value: object) -> str:
    try:
        return f"{float(str(value)) * 100:.2f}%"
    except (TypeError, ValueError):
        return str(value)


def number(value: object) -> str:
    try:
        numeric = float(str(value))
    except (TypeError, ValueError):
        return str(value)
    if numeric.is_integer():
        return str(int(numeric))
    return f"{numeric:.2f}"


def markdown_table(rows: list[dict], columns: list[tuple[str, str]]) -> str:
    header = "| " + " | ".join(label for _, label in columns) + " |"
    separator = "| " + " | ".join("---" if key in {"system", "label"} else "---:" for key, _ in columns) + " |"
    lines = [header, separator]
    for row in rows:
        values = []
        for key, _ in columns:
            value = row.get(key, "")
            if key in PERCENT_KEYS:
                values.append(percent(value))
            elif key in NUMBER_KEYS:
                values.append(number(value))
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_report(path: Path, mapping: dict, main_rows: list[dict], per_label_rows: list[dict]) -> None:
    """Write a Markdown report for the alternate mapping results."""

    frozen = sorted([row for row in main_rows if row["dataset"] == "AI4Privacy frozen"], key=lambda row: SYSTEM_ORDER[row["system"]])
    stress = sorted([row for row in main_rows if row["dataset"] == "Singapore stress"], key=lambda row: SYSTEM_ORDER[row["system"]])
    hybrid_frozen_labels = [
        row
        for row in per_label_rows
        if row["dataset"] == "AI4Privacy frozen" and row["system"] == "Hybrid" and int(row["gold_spans"]) > 0
    ]
    hybrid_stress_labels = [
        row
        for row in per_label_rows
        if row["dataset"] == "Singapore stress" and row["system"] == "Hybrid" and int(row["gold_spans"]) > 0
    ]
    content = [
        "# SafePaste V2 Product-Scope Mapping Results",
        "",
        f"Mapping: `{mapping['version']}`.",
        "",
        "These tables re-score the saved V1 prediction files with the V2 product-scope label mapping. They do not replace the official V1 frozen benchmark results and do not rerun detectors.",
        "",
        "## AI4Privacy Frozen Re-Scored With V2 Mapping",
        "",
        markdown_table(frozen, REPORT_MAIN_COLUMNS),
        "",
        "## Singapore Stress Re-Scored With V2 Mapping",
        "",
        markdown_table(stress, REPORT_MAIN_COLUMNS),
        "",
        "## Hybrid Per-Label Results: AI4Privacy Frozen, V2 Mapping",
        "",
        markdown_table(hybrid_frozen_labels, REPORT_PER_LABEL_COLUMNS),
        "",
        "## Hybrid Per-Label Results: Singapore Stress, V2 Mapping",
        "",
        markdown_table(hybrid_stress_labels, REPORT_PER_LABEL_COLUMNS),
        "",
    ]
    path.write_text("\n".join(content), encoding="utf-8")


def run(mapping_path: Path, output_dir: Path, suffix: str = "v2") -> dict:
    """Re-score all official saved runs with `mapping_path` and write V2 outputs."""

    mapping = load_json(mapping_path)
    main_rows: list[dict] = []
    per_label_rows: list[dict] = []
    for dataset, system, run_dir, dataset_path in RUNS:
        records = load_json(dataset_path)
        rows = load_jsonl(run_dir / "predictions.jsonl")
        predictions = predictions_from_rows(rows)
        metrics = evaluate_predictions(records, predictions, mapping)
        errors = len(load_jsonl(run_dir / "errors.jsonl"))
        main_rows.append({"dataset": dataset, "system": system, **metrics, "errors": errors})
        per_label_rows.extend(per_label_metrics(dataset, system, records, predictions, mapping))

    frozen_rows = [row for row in main_rows if row["dataset"] == "AI4Privacy frozen"]
    stress_rows = [row for row in main_rows if row["dataset"] == "Singapore stress"]
    write_csv(output_dir / f"main_results_{suffix}.csv", frozen_rows, MAIN_COLUMNS)
    write_csv(output_dir / f"singapore_stress_results_{suffix}.csv", stress_rows, MAIN_COLUMNS)
    write_csv(output_dir / f"per_label_results_{suffix}.csv", per_label_rows, PER_LABEL_COLUMNS)
    write_report(output_dir / f"report_tables_{suffix}.md", mapping, main_rows, per_label_rows)
    summary = {
        "mapping": str(mapping_path),
        "mapping_version": mapping["version"],
        "official_baseline_replaced": False,
        "detectors_rerun": False,
        "main_rows": len(main_rows),
        "per_label_rows": len(per_label_rows),
    }
    (output_dir / f"mapping_{suffix}_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mapping", type=Path, default=Path("configs/label_mapping_v2_product_scope.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument("--suffix", default="v2")
    args = parser.parse_args()
    print(json.dumps(run(args.mapping, args.output_dir, args.suffix), indent=2))


if __name__ == "__main__":
    main()
