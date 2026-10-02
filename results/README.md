# SafePaste Results

This directory contains report-ready aggregate results. On the author's machine it also contains row-level run outputs; those are excluded from the public repository under the AI4Privacy source license. The formal PII metrics come from frozen configuration runs, not smoke-test runs.

## Summary Files

| File | Meaning |
|---|---|
| `main_results.csv` | Aggregate AI4Privacy frozen metrics for Presidio-only, GLiNER-only and Hybrid. |
| `singapore_stress_results.csv` | Aggregate metrics for the separate 30-record Singapore stress set. |
| `per_label_results.csv` | Per-label recall and precision by dataset and system. |
| `error_categories.csv` | Error category counts by dataset and system. |
| `representative_errors.json` | Locally generated row-level qualitative examples; excluded from the public repository under the AI4Privacy redistribution terms. |
| `runtime_summary.json` | Runtime summary with total, first-record and warm-latency fields. |
| `report_tables.md` | Markdown tables ready to paste into the final report. |
| `main_results_v2.csv` | AI4Privacy frozen metrics re-scored with the post-evaluation V2 product-scope mapping. |
| `singapore_stress_results_v2.csv` | Singapore stress metrics re-scored with the V2 product-scope mapping. |
| `per_label_results_v2.csv` | V2 per-label metrics. |
| `report_tables_v2.md` | V2 product-scope Markdown tables. |
| `mapping_v2_summary.json` | Metadata proving V2 did not rerun detectors or replace V1. |

`representative_errors.json` can include AI4Privacy source text snippets. It is kept locally; `error_categories.csv` and `per_label_results.csv` provide aggregate error evidence in the repository. See `data/README.md` for the dataset license and reproduction procedure.

## Formal Run Directories

Official frozen AI4Privacy runs, generated or retained locally:

- `results/runs/presidio_frozen`
- `results/runs/gliner_frozen`
- `results/runs/hybrid_frozen`

Official Singapore stress runs, generated or retained locally:

- `results/runs/presidio_stress`
- `results/runs/gliner_stress`
- `results/runs/hybrid_stress`

Smoke runs, such as `smoke_*`, were used only to verify code paths. Their metrics are not final project results.

## Files Inside Each Run

| File | Meaning |
|---|---|
| `config.json` | Frozen experiment configuration copied into the run output. |
| `predictions.jsonl` | One JSON row per evaluated record, including mapped gold spans, predicted spans, warnings and `runtime_ms`. |
| `metrics.json` | Aggregate metrics for that run. |
| `errors.jsonl` | Runtime errors, if any. Formal runs have zero errors. |
| `runtime.json` | Runtime summary written at run time. |
| `run.log` | Lightweight run log with command context and completion notes. |

The prediction files do not preserve the full original text for every row, but they are row-level derivatives of the source dataset. They and the qualitative examples remain local pending redistribution permission. The included aggregate CSV/Markdown files show the recorded results; authorised users can regenerate row-level outputs from the source dataset.

## Regenerating Derived Results

From the project root:

```powershell
conda activate safepaste
$env:PYTHONPATH = "src;."
python scripts\analyse_errors.py --output-dir results
python scripts\export_report_tables.py --results-dir results --output results\report_tables.md
python scripts\reevaluate_saved_predictions.py --mapping configs\label_mapping_v2_product_scope.json --output-dir results --suffix v2
```

These commands use saved prediction artifacts. They do not rerun Presidio or GLiNER and do not change the formal predictions. The V2 command is a post-evaluation product-scope re-scoring view; it does not replace the official V1 result.

## Runtime Fields

`runtime_summary.json` includes:

- `total_ms`: end-to-end time over all records.
- `first_record_ms`: first-record latency, including cold start.
- `warm_records`: records remaining after excluding the first record.
- `warm_mean_ms`: mean latency after excluding the first record.
- `warm_p95_ms`: P95 latency after excluding the first record.
- `mean_ms` and `p95_ms`: original all-record summary fields retained for compatibility.

For the 30-record stress set, first-record model loading dominates the all-record mean. Use the warm fields when discussing steady-state local inference.
