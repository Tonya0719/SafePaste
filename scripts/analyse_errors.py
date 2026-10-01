"""Create per-label metrics and error-analysis artifacts from saved runs."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from safepaste.types import GoldSpan, Span


RUNS = [
    ("AI4Privacy frozen", "Presidio-only", Path("results/runs/presidio_frozen"), Path("data/ai4privacy_split/frozen_evaluation_3000.json")),
    ("AI4Privacy frozen", "GLiNER-only", Path("results/runs/gliner_frozen"), Path("data/ai4privacy_split/frozen_evaluation_3000.json")),
    ("AI4Privacy frozen", "Hybrid", Path("results/runs/hybrid_frozen"), Path("data/ai4privacy_split/frozen_evaluation_3000.json")),
    ("Singapore stress", "Presidio-only", Path("results/runs/presidio_stress"), Path("data/singapore_stress.json")),
    ("Singapore stress", "GLiNER-only", Path("results/runs/gliner_stress"), Path("data/singapore_stress.json")),
    ("Singapore stress", "Hybrid", Path("results/runs/hybrid_stress"), Path("data/singapore_stress.json")),
]


@dataclass(frozen=True)
class Match:
    pred_index: int
    gold_index: int


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def record_id(index: int, record: dict) -> str:
    return str(record.get("id") or f"record-{index + 1:05d}")


def spans_from_gold(items: list[dict]) -> list[GoldSpan]:
    return [GoldSpan(int(item["start"]), int(item["end"]), str(item["label"])) for item in items]


def spans_from_predictions(items: list[dict]) -> list[Span]:
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


def overlaps(left_start: int, left_end: int, right_start: int, right_end: int) -> bool:
    return left_start < right_end and right_start < left_end


def match_spans(predictions: list[Span], gold: list[GoldSpan], *, boundary: str, include_abstained: bool, require_label: bool) -> list[Match]:
    candidates: list[tuple[int, float, int, int]] = []
    for pi, pred in enumerate(predictions):
        if pred.abstained and not include_abstained:
            continue
        for gi, target in enumerate(gold):
            if require_label and pred.label != target.label:
                continue
            if boundary == "exact" and not (pred.start == target.start and pred.end == target.end):
                continue
            if boundary == "overlap" and not overlaps(pred.start, pred.end, target.start, target.end):
                continue
            overlap = min(pred.end, target.end) - max(pred.start, target.start)
            candidates.append((overlap, pred.score, pi, gi))
    matched_pred: set[int] = set()
    matched_gold: set[int] = set()
    matches: list[Match] = []
    for _, _, pi, gi in sorted(candidates, reverse=True):
        if pi in matched_pred or gi in matched_gold:
            continue
        matched_pred.add(pi)
        matched_gold.add(gi)
        matches.append(Match(pi, gi))
    return matches


def per_label_metrics(dataset: str, system: str, rows: list[dict]) -> list[dict]:
    labels = sorted({item["label"] for row in rows for item in row["gold_spans"]} | {item["label"] for row in rows for item in row["predicted_spans"]})
    output = []
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
        for row in rows:
            gold = [item for item in spans_from_gold(row["gold_spans"]) if item.label == label]
            preds = [item for item in spans_from_predictions(row["predicted_spans"]) if item.label == label]
            gold_total += len(gold)
            pred_typed_total += sum(not item.abstained for item in preds)
            pred_protective_total += len(preds)
            counts["exact_typed"] += len(match_spans(preds, gold, boundary="exact", include_abstained=False, require_label=True))
            counts["exact_protective"] += len(match_spans(preds, gold, boundary="exact", include_abstained=True, require_label=False))
            counts["overlap_typed"] += len(match_spans(preds, gold, boundary="overlap", include_abstained=False, require_label=True))
            counts["overlap_protective"] += len(match_spans(preds, gold, boundary="overlap", include_abstained=True, require_label=False))
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


def classify_errors(dataset: str, system: str, rows: list[dict], records_by_id: dict[str, dict], max_examples: int = 4) -> tuple[list[dict], list[dict]]:
    category_counts: Counter[str] = Counter()
    examples: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        rid = row["record_id"]
        text = str(records_by_id.get(rid, {}).get("text", ""))
        gold = spans_from_gold(row["gold_spans"])
        preds = spans_from_predictions(row["predicted_spans"])
        exact_typed = match_spans(preds, gold, boundary="exact", include_abstained=False, require_label=True)
        exact_typed_gold = {item.gold_index for item in exact_typed}
        exact_typed_pred = {item.pred_index for item in exact_typed}

        for gi, target in enumerate(gold):
            if gi in exact_typed_gold:
                continue
            category = classify_gold_error(target, preds)
            category_counts[category] += 1
            if len(examples[category]) < max_examples:
                examples[category].append(example_row(dataset, system, rid, text, category, target, preds))

        for pi, pred in enumerate(preds):
            if pi in exact_typed_pred:
                continue
            if not any(overlaps(pred.start, pred.end, target.start, target.end) for target in gold):
                category = "false_positive"
                category_counts[category] += 1
                if len(examples[category]) < max_examples:
                    examples[category].append(example_row(dataset, system, rid, text, category, None, [pred]))

        for gi, target in enumerate(gold):
            overlap_count = sum(overlaps(pred.start, pred.end, target.start, target.end) for pred in preds)
            if overlap_count > 1:
                category_counts["split_entity"] += 1
        for pred in preds:
            overlap_count = sum(overlaps(pred.start, pred.end, target.start, target.end) for target in gold)
            if overlap_count > 1:
                category_counts["merged_entities"] += 1

    count_rows = [{"dataset": dataset, "system": system, "category": key, "count": value} for key, value in sorted(category_counts.items())]
    flat_examples = [item for category in sorted(examples) for item in examples[category]]
    return count_rows, flat_examples


def classify_gold_error(target: GoldSpan, preds: list[Span]) -> str:
    exact_range = [pred for pred in preds if pred.start == target.start and pred.end == target.end]
    if any(pred.abstained for pred in exact_range):
        return "correct_range_abstained"
    if exact_range:
        return "label_error"
    overlapping = [pred for pred in preds if overlaps(pred.start, pred.end, target.start, target.end)]
    if not overlapping:
        return "missed_gold"
    if any(pred.label == target.label for pred in overlapping):
        pred = next(pred for pred in overlapping if pred.label == target.label)
        if pred.start >= target.start and pred.end <= target.end:
            return "boundary_too_short"
        if pred.start <= target.start and pred.end >= target.end:
            return "boundary_too_long"
        return "boundary_shifted"
    if any(pred.abstained for pred in overlapping):
        return "overlap_abstained"
    return "overlap_wrong_label"


def example_row(dataset: str, system: str, rid: str, text: str, category: str, gold: GoldSpan | None, preds: list[Span]) -> dict:
    starts = [span.start for span in preds]
    ends = [span.end for span in preds]
    if gold is not None:
        starts.append(gold.start)
        ends.append(gold.end)
    if starts and ends and text:
        left = max(0, min(starts) - 50)
        right = min(len(text), max(ends) + 50)
        context = text[left:right]
    else:
        context = ""
    return {
        "dataset": dataset,
        "system": system,
        "record_id": rid,
        "category": category,
        "context": context,
        "gold": None if gold is None else {"start": gold.start, "end": gold.end, "label": gold.label},
        "predictions": [
            {
                "start": pred.start,
                "end": pred.end,
                "label": pred.label,
                "source": pred.source,
                "score": pred.score,
                "abstained": pred.abstained,
                "recognizer_name": pred.recognizer_name,
            }
            for pred in preds
        ],
    }


def safe_div(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(output_dir: Path) -> dict:
    per_label_rows: list[dict] = []
    error_rows: list[dict] = []
    representative: list[dict] = []
    for dataset, system, run_dir, dataset_path in RUNS:
        rows = load_jsonl(run_dir / "predictions.jsonl")
        records = load_json(dataset_path)
        records_by_id = {record_id(index, record): record for index, record in enumerate(records)}
        per_label_rows.extend(per_label_metrics(dataset, system, rows))
        counts, examples = classify_errors(dataset, system, rows, records_by_id)
        error_rows.extend(counts)
        representative.extend(examples)
    write_csv(output_dir / "per_label_results.csv", per_label_rows)
    write_csv(output_dir / "error_categories.csv", error_rows)
    (output_dir / "representative_errors.json").write_text(json.dumps(representative, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"per_label_rows": len(per_label_rows), "error_rows": len(error_rows), "representative_errors": len(representative)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    args = parser.parse_args()
    print(json.dumps(run(args.output_dir), indent=2))


if __name__ == "__main__":
    main()
