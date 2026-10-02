"""Metric implementation for SafePaste experiments.

The evaluator consumes source records, mapped gold spans and detector
predictions. It reports exact/overlap and typed/protective metrics using
one-to-one prediction/gold matching so duplicate predictions cannot inflate
scores.
"""
from __future__ import annotations

from dataclasses import dataclass

from .types import GoldSpan, Span


@dataclass(frozen=True)
class Counts:
    matched: int
    gold: int
    predicted: int

    @property
    def recall(self) -> float:
        return self.matched / self.gold if self.gold else 1.0

    @property
    def precision(self) -> float:
        return self.matched / self.predicted if self.predicted else (1.0 if not self.gold else 0.0)


def _matches(pred: Span, gold: GoldSpan, boundary: str, require_label: bool) -> bool:
    if require_label and pred.label != gold.label:
        return False
    if boundary == "exact":
        return pred.start == gold.start and pred.end == gold.end
    if boundary == "overlap":
        return pred.start < gold.end and gold.start < pred.end
    raise ValueError("boundary must be exact or overlap")


def score(predictions: list[Span], gold: list[GoldSpan], *, boundary: str, include_abstained: bool, require_label: bool = False) -> Counts:
    """Score one record with exact or overlap matching and one-to-one assignment."""

    eligible = [span for span in predictions if include_abstained or not span.abstained]
    candidates = []
    for pi, pred in enumerate(eligible):
        for gi, target in enumerate(gold):
            if _matches(pred, target, boundary, require_label):
                overlap = min(pred.end, target.end) - max(pred.start, target.start)
                candidates.append((overlap, pred.score, pi, gi))
    matched_pred: set[int] = set()
    matched_gold: set[int] = set()
    for _, _, pi, gi in sorted(candidates, reverse=True):
        if pi not in matched_pred and gi not in matched_gold:
            matched_pred.add(pi)
            matched_gold.add(gi)
    return Counts(len(matched_gold), len(gold), len(eligible))


def gold_spans_from_record(record: dict, label_mapping: dict | None = None) -> tuple[list[GoldSpan], dict[str, int]]:
    """Normalize one record's gold spans through the optional label mapping."""

    text = record["text"]
    mapping = label_mapping or {}
    entries = mapping.get("entries", {})
    target_labels = set(mapping.get("target_labels", []))
    alias_labels = {
        "SG_NRIC": "GOVERNMENT_ID",
        "UNIT_NUMBER": "ADDRESS",
        "POSTAL_CODE": "ADDRESS",
        "CREDIT_CARD": "FINANCIAL",
    }
    skipped = {"excluded_gold_spans": 0, "invalid_gold_spans": 0, "unmapped_gold_spans": 0}
    gold: list[GoldSpan] = []
    for item in record["spans"]:
        start = int(item["start"])
        end = int(item["end"])
        raw_label = str(item["label"])
        if start < 0 or end <= start or end > len(text):
            skipped["invalid_gold_spans"] += 1
            continue
        label = raw_label
        if label_mapping is not None:
            entry = entries.get(raw_label)
            if entry is not None:
                target = str(entry["target"])
            elif raw_label in target_labels:
                target = raw_label
            elif raw_label in alias_labels:
                target = alias_labels[raw_label]
            else:
                skipped["unmapped_gold_spans"] += 1
                continue
            if target == "EXCLUDED":
                skipped["excluded_gold_spans"] += 1
                continue
            label = target
        gold.append(GoldSpan(start, end, label))
    return gold, skipped


def evaluate_predictions(records: list[dict], predictions: list[list[Span]], label_mapping: dict | None = None) -> dict:
    """Aggregate metrics for saved predictions aligned with source records."""

    totals = {(b, a): [0, 0, 0] for b in ("exact", "overlap") for a in (False, True)}
    abstained = predicted = 0
    skipped_totals = {"excluded_gold_spans": 0, "invalid_gold_spans": 0, "unmapped_gold_spans": 0}
    gold_total = 0
    for record, preds in zip(records, predictions, strict=True):
        gold, skipped = gold_spans_from_record(record, label_mapping)
        gold_total += len(gold)
        for key, value in skipped.items():
            skipped_totals[key] += value
        abstained += sum(item.abstained for item in preds)
        predicted += len(preds)
        for key in totals:
            require_label = not key[1]
            counts = score(preds, gold, boundary=key[0], include_abstained=key[1], require_label=require_label)
            bucket = totals[key]
            bucket[0] += counts.matched
            bucket[1] += counts.gold
            bucket[2] += counts.predicted
    output = {}
    for (boundary, protective), values in totals.items():
        counts = Counts(*values)
        kind = "protective" if protective else "typed"
        output[f"{boundary}_{kind}_recall"] = counts.recall
        output[f"{boundary}_{kind}_precision"] = counts.precision
    output["abstention_rate"] = abstained / predicted if predicted else 0.0
    output["records"] = len(records)
    output["gold_spans"] = gold_total
    output["predicted_spans"] = predicted
    output.update(skipped_totals)
    return output


def evaluate_records(records: list[dict], predict, label_mapping: dict | None = None) -> dict:
    """Run a prediction callable over records and evaluate the resulting spans."""

    return evaluate_predictions(records, [predict(record["text"]) for record in records], label_mapping)
