"""Export report-ready Markdown tables from result CSV files."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


SYSTEM_ORDER = {"Presidio-only": 0, "GLiNER-only": 1, "Hybrid": 2}
DATASET_ORDER = {"AI4Privacy frozen": 0, "Singapore stress": 1}
TEXT_COLUMNS = {"dataset", "system", "label", "category"}

MAIN_COLUMNS = [
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

PER_LABEL_COLUMNS = [
    ("label", "Label"),
    ("gold_spans", "Gold"),
    ("exact_typed_recall", "Exact typed R"),
    ("overlap_typed_recall", "Overlap typed R"),
    ("overlap_protective_recall", "Overlap protective R"),
    ("exact_typed_precision", "Exact typed P"),
    ("overlap_typed_precision", "Overlap typed P"),
]

RUNTIME_COLUMNS = [
    ("dataset", "Dataset"),
    ("system", "System"),
    ("records", "Records"),
    ("total_ms", "Total ms"),
    ("first_record_ms", "First record ms"),
    ("warm_records", "Warm records"),
    ("warm_mean_ms", "Warm mean ms"),
    ("warm_p95_ms", "Warm P95 ms"),
    ("errors", "Errors"),
]

ERROR_COLUMNS = [
    ("dataset", "Dataset"),
    ("system", "System"),
    ("category", "Category"),
    ("count", "Count"),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_json_rows(path: Path) -> list[dict[str, object]]:
    return json.loads(path.read_text(encoding="utf-8"))


def percent(value: str) -> str:
    try:
        return f"{float(value) * 100:.2f}%"
    except (TypeError, ValueError):
        return value


def number(value: object) -> str:
    try:
        numeric = float(str(value))
    except (TypeError, ValueError):
        return str(value)
    if numeric.is_integer():
        return str(int(numeric))
    return f"{numeric:.2f}"


def markdown_escape(value: object) -> str:
    return str(value).replace("|", "\\|")


def markdown_table(
    rows: list[dict[str, object]],
    columns: list[tuple[str, str]],
    percent_keys: set[str] | None = None,
    number_keys: set[str] | None = None,
) -> str:
    percent_keys = percent_keys or set()
    number_keys = number_keys or set()
    header = "| " + " | ".join(label for _, label in columns) + " |"
    separator = "| " + " | ".join("---" if key in TEXT_COLUMNS else "---:" for key, _ in columns) + " |"
    lines = [header, separator]
    for row in rows:
        values = []
        for key, _ in columns:
            value = row.get(key, "")
            if key in percent_keys:
                values.append(percent(str(value)))
            elif key in number_keys:
                values.append(number(value))
            else:
                values.append(markdown_escape(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def sort_by_system(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(rows, key=lambda row: SYSTEM_ORDER.get(str(row.get("system")), 99))


def sort_by_dataset_and_system(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(
        rows,
        key=lambda row: (
            DATASET_ORDER.get(str(row.get("dataset")), 99),
            SYSTEM_ORDER.get(str(row.get("system")), 99),
        ),
    )


def top_error_rows(rows: list[dict[str, str]], dataset: str, system: str, limit: int = 8) -> list[dict[str, object]]:
    matching = [row for row in rows if row["dataset"] == dataset and row["system"] == system]
    return sorted(matching, key=lambda row: int(row["count"]), reverse=True)[:limit]


def run(results_dir: Path, output: Path) -> None:
    main_rows = sort_by_system(read_csv(results_dir / "main_results.csv"))
    stress_rows = sort_by_system(read_csv(results_dir / "singapore_stress_results.csv"))
    per_label_rows = read_csv(results_dir / "per_label_results.csv")
    error_rows = read_csv(results_dir / "error_categories.csv")
    runtime_rows = read_json_rows(results_dir / "runtime_summary.json")
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
    percent_keys = {
        "exact_typed_recall",
        "exact_protective_recall",
        "overlap_typed_recall",
        "overlap_protective_recall",
        "exact_typed_precision",
        "overlap_typed_precision",
        "abstention_rate",
    }
    number_keys = {
        "records",
        "gold_spans",
        "predicted_spans",
        "mean_ms",
        "p95_ms",
        "total_ms",
        "first_record_ms",
        "warm_records",
        "warm_mean_ms",
        "warm_p95_ms",
        "errors",
        "count",
    }
    runtime_rows = sort_by_dataset_and_system(runtime_rows)
    content = [
        "# SafePaste Report Tables",
        "",
        "## AI4Privacy Frozen Evaluation",
        "",
        markdown_table(main_rows, MAIN_COLUMNS, percent_keys, number_keys),
        "",
        "## Singapore Stress Set",
        "",
        markdown_table(stress_rows, MAIN_COLUMNS, percent_keys, number_keys),
        "",
        "## Runtime Summary",
        "",
        markdown_table(runtime_rows, RUNTIME_COLUMNS, number_keys=number_keys),
        "",
        "## Hybrid Per-Label Results: AI4Privacy Frozen",
        "",
        markdown_table(hybrid_frozen_labels, PER_LABEL_COLUMNS, percent_keys, number_keys),
        "",
        "## Hybrid Per-Label Results: Singapore Stress",
        "",
        markdown_table(hybrid_stress_labels, PER_LABEL_COLUMNS, percent_keys, number_keys),
        "",
        "## Top Hybrid Error Categories: AI4Privacy Frozen",
        "",
        markdown_table(top_error_rows(error_rows, "AI4Privacy frozen", "Hybrid"), ERROR_COLUMNS, number_keys=number_keys),
        "",
        "## Hybrid Error Categories: Singapore Stress",
        "",
        markdown_table(top_error_rows(error_rows, "Singapore stress", "Hybrid"), ERROR_COLUMNS, number_keys=number_keys),
        "",
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(content), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument("--output", type=Path, default=Path("results/report_tables.md"))
    args = parser.parse_args()
    run(args.results_dir, args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
