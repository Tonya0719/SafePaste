"""Audit SafePaste datasets without running model evaluation."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


DEFAULT_DATASETS = {
    "development": Path("data/ai4privacy_split/development_2000.json"),
    "frozen_evaluation": Path("data/ai4privacy_split/frozen_evaluation_3000.json"),
    "singapore_stress": Path("data/singapore_stress.json"),
}

EXPECTED_COUNTS = {
    "development": 2000,
    "frozen_evaluation": 3000,
    "singapore_stress": 30,
}


@dataclass(frozen=True)
class SpanIssue:
    dataset: str
    record_id: str
    span_index: int
    issue: str
    start: str
    end: str
    label: str
    excerpt: str


@dataclass(frozen=True)
class SpanRelation:
    dataset: str
    record_id: str
    first_span_index: int
    second_span_index: int
    relation: str
    first_label: str
    second_label: str
    first_range: str
    second_range: str


def load_records(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON list")
    return data


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def record_id(dataset: str, index: int, record: dict) -> str:
    return str(record.get("id") or f"{dataset}-{index + 1:05d}")


def validate_records(dataset: str, records: list[dict]) -> tuple[list[SpanIssue], list[SpanRelation]]:
    issues: list[SpanIssue] = []
    relations: list[SpanRelation] = []
    for index, record in enumerate(records):
        rid = record_id(dataset, index, record)
        text = record.get("text")
        spans = record.get("spans")
        if not isinstance(text, str):
            issues.append(SpanIssue(dataset, rid, -1, "missing_or_invalid_text", "", "", "", ""))
            continue
        if not isinstance(spans, list):
            issues.append(SpanIssue(dataset, rid, -1, "missing_or_invalid_spans", "", "", "", ""))
            continue
        normalized = []
        seen = set()
        for span_index, span in enumerate(spans):
            start = span.get("start") if isinstance(span, dict) else None
            end = span.get("end") if isinstance(span, dict) else None
            label = str(span.get("label", "")) if isinstance(span, dict) else ""
            issue = _span_issue(text, start, end)
            start_text = "" if start is None else str(start)
            end_text = "" if end is None else str(end)
            excerpt = ""
            if isinstance(start, int) and isinstance(end, int) and 0 <= start <= len(text) and 0 <= end <= len(text):
                excerpt = text[start:end]
            if issue:
                issues.append(SpanIssue(dataset, rid, span_index, issue, start_text, end_text, label, excerpt))
                continue
            key = (int(start), int(end), label)
            if key in seen:
                issues.append(SpanIssue(dataset, rid, span_index, "duplicate_span", start_text, end_text, label, excerpt))
            seen.add(key)
            normalized.append((span_index, int(start), int(end), label))
        for left_index, left in enumerate(normalized):
            for right in normalized[left_index + 1 :]:
                if left[1] < right[2] and right[1] < left[2]:
                    relation = "same_range" if left[1] == right[1] and left[2] == right[2] else "overlap"
                    relations.append(
                        SpanRelation(
                            dataset=dataset,
                            record_id=rid,
                            first_span_index=left[0],
                            second_span_index=right[0],
                            relation=relation,
                            first_label=left[3],
                            second_label=right[3],
                            first_range=f"{left[1]}:{left[2]}",
                            second_range=f"{right[1]}:{right[2]}",
                        )
                    )
    return issues, relations


def label_counts(records: list[dict]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for record in records:
        for span in record.get("spans", []):
            if isinstance(span, dict) and "label" in span:
                counts[str(span["label"])] += 1
    return counts


def label_examples(records: list[dict], limit: int = 5) -> dict[str, list[str]]:
    examples: dict[str, list[str]] = defaultdict(list)
    for record in records:
        text = record.get("text")
        if not isinstance(text, str):
            continue
        for span in record.get("spans", []):
            if not isinstance(span, dict):
                continue
            start = span.get("start")
            end = span.get("end")
            label = str(span.get("label", ""))
            if not isinstance(start, int) or not isinstance(end, int) or not label:
                continue
            if 0 <= start < end <= len(text) and len(examples[label]) < limit:
                examples[label].append(text[start:end])
    return dict(examples)


def _span_issue(text: str, start, end) -> str | None:
    if not isinstance(start, int) or not isinstance(end, int):
        return "non_integer_bounds"
    if start < 0 or end < 0:
        return "negative_bounds"
    if end <= start:
        return "empty_or_reversed_span"
    if start > len(text) or end > len(text):
        return "out_of_bounds"
    if not text[start:end]:
        return "empty_excerpt"
    return None


def write_csv(path: Path, rows: Iterable[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def audit(datasets: dict[str, Path], output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_rows = []
    all_issues: list[SpanIssue] = []
    all_relations: list[SpanRelation] = []
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": {},
    }
    development_records: list[dict] | None = None

    for name, path in datasets.items():
        resolved = path.resolve()
        records = load_records(resolved)
        issues, relations = validate_records(name, records)
        all_issues.extend(issues)
        all_relations.extend(relations)
        span_count = sum(len(record.get("spans", [])) for record in records if isinstance(record.get("spans"), list))
        expected = EXPECTED_COUNTS.get(name)
        summary_rows.append(
            {
                "dataset": name,
                "path": str(path),
                "records": len(records),
                "expected_records": "" if expected is None else expected,
                "record_count_ok": "" if expected is None else len(records) == expected,
                "spans": span_count,
                "span_issues": len(issues),
                "overlap_relations": len(relations),
            }
        )
        manifest["files"][name] = {
            "path": str(path),
            "bytes": resolved.stat().st_size,
            "sha256": sha256_file(resolved),
            "records": len(records),
            "spans": span_count,
        }
        if name == "development":
            development_records = records

    write_csv(
        output_dir / "record_summary.csv",
        summary_rows,
        ["dataset", "path", "records", "expected_records", "record_count_ok", "spans", "span_issues", "overlap_relations"],
    )
    write_csv(
        output_dir / "invalid_spans.csv",
        [issue.__dict__ for issue in all_issues],
        ["dataset", "record_id", "span_index", "issue", "start", "end", "label", "excerpt"],
    )
    write_csv(
        output_dir / "overlapping_gold_spans.csv",
        [relation.__dict__ for relation in all_relations],
        ["dataset", "record_id", "first_span_index", "second_span_index", "relation", "first_label", "second_label", "first_range", "second_range"],
    )
    if development_records is not None:
        counts = label_counts(development_records)
        examples = label_examples(development_records)
        write_csv(
            output_dir / "development_label_counts.csv",
            [{"label": label, "count": count} for label, count in sorted(counts.items())],
            ["label", "count"],
        )
        example_rows = []
        for label in sorted(examples):
            for value in examples[label]:
                example_rows.append({"label": label, "example": value})
        write_csv(output_dir / "development_label_examples.csv", example_rows, ["label", "example"])

    (output_dir / "data_sha256_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"summary": summary_rows, "issues": all_issues, "relations": all_relations, "manifest": manifest}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--development", type=Path, default=DEFAULT_DATASETS["development"])
    parser.add_argument("--frozen", type=Path, default=DEFAULT_DATASETS["frozen_evaluation"])
    parser.add_argument("--stress", type=Path, default=DEFAULT_DATASETS["singapore_stress"])
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/data_audit"))
    args = parser.parse_args()
    result = audit(
        {
            "development": args.development,
            "frozen_evaluation": args.frozen,
            "singapore_stress": args.stress,
        },
        args.output_dir,
    )
    print(json.dumps({"summary": result["summary"]}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
