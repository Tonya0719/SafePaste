# SafePaste Implementation Todo

This checklist summarizes `SAFEPaste_PROJECT_EXECUTION_PLAN_ZH.md` and
`SafePaste_Implementation_Plan.md`. After the frozen evaluation configuration is
locked, do not change detector rules, thresholds, label mapping, overlap
resolution or metric logic based on `frozen_evaluation_3000.json` results.

## Phase A: Environment And Baseline Audit

- [x] Run the current test suite and record command, environment and result.
- [x] Verify record counts for `development_2000.json`, `frozen_evaluation_3000.json` and `singapore_stress.json`.
- [x] Audit span validity for empty spans, out-of-bounds spans, duplicate spans and overlapping spans.
- [x] Generate a SHA-256 manifest for dataset files.
- [x] Create and maintain `docs/experiment_log.md`.
- [x] Record GLiNER model path, Presidio version and Python version.

## Phase B: Detectors And Pipeline Modes

- [x] Add `PresidioDetector`.
- [x] Keep `regex` as a compatibility alias for Presidio.
- [x] Support explicit modes: `presidio`, `regex`, `regex-legacy`, `gliner` and `hybrid`.
- [x] Retain the old `RegexDetector` as `regex-legacy` for debugging only.
- [x] Add optional `recognizer_name` to `Span` for Presidio error analysis.
- [x] Use NoOp NLP for the Presidio baseline to avoid adding spaCy PERSON NER.
- [x] Register Singapore custom recognizers for NRIC-shaped strings, local phones, unit numbers and postal codes.
- [x] Add negative order-number examples to avoid masking plain eight-digit order IDs as phones.
- [x] Ensure GLiNER loads only from a local path with `local_files_only=True`.
- [x] Add GLiNER typed and abstained unit tests.
- [x] Confirm Hybrid reports both `presidio` and `gliner` in `engines_used`.

## Phase C: Label Mapping And Dataset Audit

- [x] Write `scripts/audit_dataset.py`.
- [x] Use only the development set for label counts, label examples, invalid spans and unmapped labels.
- [x] Write `configs/label_mapping.json`; every source label must be mapped or explicitly excluded.
- [x] Decide which cities, countries, organisations, URLs and dates are in project PII scope.
- [x] Make all three systems output the final SafePaste label space.

## Phase D: Development Tuning And Config Freeze

- [x] Write `scripts/tune_thresholds.py`.
- [x] Run a development threshold-sweep smoke test for infrastructure only.
- [x] Sweep GLiNER typed and abstention thresholds on the 2,000-record development set only.
- [x] Record exact/overlap, typed/protective, precision, abstention, per-label metrics and runtime.
- [ ] Manually review a sample of false positives and false negatives.
- [x] Write `artifacts/threshold_tuning/decision.md`.
- [x] Generate `configs/final_experiment.draft.json`.
- [x] Generate and freeze `configs/final_experiment.json`.

## Phase E: Formal Batch Experiments

- [x] Write `scripts/run_experiment.py`.
- [x] Support `--system presidio|gliner|hybrid`.
- [x] Save config, predictions, metrics, errors, runtime and run log for every run.
- [x] Run smoke tests before formal evaluation.
- [x] Run Presidio, GLiNER and Hybrid once on the 3,000-record frozen evaluation set.
- [x] Run Presidio, GLiNER and Hybrid separately on the 30-record Singapore stress set.

## Phase F: Metrics, Error Analysis And Report

- [x] Write `scripts/analyse_errors.py`.
- [x] Write `scripts/export_report_tables.py`.
- [x] Output `results/main_results.csv`.
- [x] Output `results/per_label_results.csv`.
- [x] Output `results/singapore_stress_results.csv`.
- [x] Output `results/error_categories.csv`.
- [x] Output `results/representative_errors.json`.
- [x] Output `results/runtime_summary.json`.
- [x] Output `results/report_tables.md`.
- [x] Add final result tables, experiment commands, dataset license notes and limitations to README.
- [x] Draft the final English problem statement and trade-off analysis under 1,200 words.
- [x] Prepare the 5-7 minute demo script outline using only fictional text.
