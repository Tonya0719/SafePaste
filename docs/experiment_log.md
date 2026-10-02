# SafePaste Experiment Log

本日志记录会影响系统设计、规则、阈值、评测或报告结论的实验与决策。失败实验也要记录。正式冻结评测开始后，不得根据 frozen evaluation 结果回改系统。

## EXP-001 Presidio Compatibility Mode

- Date: 2026-09-29
- Objective: Make the legacy `regex` mode route through Presidio while preserving an explicit legacy regex debug mode.
- Dataset: Synthetic unit-test strings only; no frozen evaluation data used.
- System: `presidio`, `regex`, `regex-legacy`, `hybrid`
- Configuration: Presidio registry with built-in structured recognizers plus custom Singapore NRIC, phone, unit and postal-code recognizers; NoOp NLP engine to avoid spaCy PERSON detection in the rule baseline.
- Code version: Local workspace, commit not yet recorded.
- Expected outcome: `regex` and `presidio` produce `source=presidio`; `regex-legacy` produces `source=regex`; ordinary order numbers are not masked.
- Actual result: Unit tests passed. CLI smoke test masked email and contextual phone while leaving an unrelated order number unmasked.
- Interpretation: Compatibility mode works and avoids mixing GLiNER or spaCy NER into the Presidio-only baseline.
- Decision: Use `presidio`, `gliner` and `hybrid` for formal experiments. Treat `regex` as a compatibility alias and `regex-legacy` as debug-only.
- Next action: Complete Phase A data audit and GLiNER local-loading verification before label mapping and threshold tuning.

## EXP-002 Phase A Dataset Audit

- Date: 2026-09-29
- Objective: Verify dataset record counts, basic span validity, overlap cases and SHA-256 hashes before detector tuning.
- Dataset: `development_2000.json`, `frozen_evaluation_3000.json`, `singapore_stress.json`
- System: Data audit only; no detector predictions or frozen-set scoring.
- Configuration: `scripts/audit_dataset.py --output-dir artifacts/data_audit`
- Code version: Local workspace; `.git` directory is absent, so no commit hash is available.
- Expected outcome: 2,000 development records, 3,000 frozen evaluation records and 30 stress records; no silent malformed spans.
- Actual result: Counts matched expected values. Development has 14,336 spans, 1 out-of-bounds span and 44 overlap relations. Frozen evaluation has 21,698 spans, 0 invalid spans and 82 overlap relations. Singapore stress has 53 spans, 0 invalid spans and 0 overlap relations.
- Interpretation: The datasets are present and count-valid. The development out-of-bounds `GEOCOORD` span and overlapping gold spans must be handled explicitly during label mapping and evaluation normalization, not silently ignored.
- Decision: Save audit outputs under `artifacts/data_audit/`, including `data_sha256_manifest.json`, `record_summary.csv`, `invalid_spans.csv`, `overlapping_gold_spans.csv`, `development_label_counts.csv` and `development_label_examples.csv`.
- Next action: Build label mapping from development labels only, with explicit include/exclude decisions.

## EXP-003 GLiNER Local Loading Smoke Test

- Date: 2026-09-29
- Objective: Confirm GLiNER uses a local model directory and can participate in Hybrid with Presidio.
- Dataset: Synthetic single-message smoke tests only.
- System: `gliner` and `hybrid`
- Configuration: `.env` points `SAFEPASTE_GLINER_MODEL` to `C:\Users\DELL\Desktop\safepaste\models\gliner_multi_pii-v1`; `GLiNERDetector(local_files_only=True)`.
- Code version: Local workspace; `.git` directory is absent, so no commit hash is available.
- Expected outcome: `GLiNERDetector.available=True`; sample person and address detected; Hybrid reports both detector sources.
- Actual result: GLiNER detected `Mei Tan` as `PERSON` and `Blk 123 Ang Mo Kio Ave 3` as `ADDRESS`. Hybrid output included `engines_used=["gliner", "presidio"]`.
- Interpretation: Local model files are present and the detector can run without relying on a remote model ID during inference. The current shell had a placeholder environment variable that can override `.env`; verification used `.env` by removing that process variable.
- Decision: Keep `local_files_only=True` as the default and avoid evaluating frozen data until label mapping and final config are frozen.
- Next action: Implement AI4Privacy label mapping and span-normalization policy using development audit outputs.

## EXP-004 Development Label Mapping Draft

- Date: 2026-09-29
- Objective: Map AI4Privacy development labels into the SafePaste evaluation label space with explicit include/exclude decisions.
- Dataset: `development_2000.json` only.
- System: Label mapping only; no detector predictions or frozen-set scoring.
- Configuration: `scripts/build_label_mapping.py --development data\ai4privacy_split\development_2000.json --output configs\label_mapping.json --unmapped-output artifacts\data_audit\unmapped_labels.csv`
- Code version: Local workspace; `.git` directory is absent, so no commit hash is available.
- Expected outcome: Every raw development label has a target label or explicit `EXCLUDED` reason; `unmapped_labels.csv` has zero data rows.
- Actual result: 27 raw labels covered. Target labels are `ADDRESS`, `EMAIL`, `FINANCIAL`, `GOVERNMENT_ID`, `IP_ADDRESS`, `PERSON` and `PHONE`. Excluded labels are `BOD`, `DATE`, `PASS`, `SEX`, `TIME`, `TITLE` and `USERNAME`.
- Interpretation: The mapping keeps the project scope aligned with Presidio structured PII plus GLiNER person/address coverage. Excluded temporal, credential, demographic and username fields must be reported as limitations, not treated as missed detector failures.
- Decision: Use `configs/label_mapping.json` as the current mapping draft. Presidio custom outputs are normalized to the same target label space while retaining `recognizer_name`. Do not revise the mapping based on frozen evaluation results.
- Next action: Add span normalization/evaluation support so gold labels and detector labels share this target space.

## EXP-005 Typed Metric Semantics Fix

- Date: 2026-09-29
- Objective: Ensure typed metrics require the predicted label to match the gold label.
- Dataset: Unit-test synthetic records only.
- System: Evaluation code.
- Configuration: `evaluate_records()` now calls `score(..., require_label=True)` for typed metrics and keeps protective metrics label-agnostic.
- Code version: Local workspace; `.git` directory is absent, so no commit hash is available.
- Expected outcome: A correct span with the wrong label has zero typed recall but can still count for protective recall.
- Actual result: Added unit test passed; full test suite passed.
- Interpretation: Future exact/overlap typed metrics now measure type correctness instead of only span coverage.
- Decision: Keep protective recall as coverage-oriented, including abstained spans and label mismatch tolerance.
- Next action: Build experiment scripts on top of this corrected evaluator.

## EXP-006 Threshold Sweep Smoke Test

- Date: 2026-09-30
- Objective: Verify that the development threshold sweep script runs end to end without using frozen evaluation results.
- Dataset: First 5 records from `development_2000.json`.
- System: GLiNER-only cached predictions with mapped gold labels.
- Configuration: `scripts/tune_thresholds.py --limit 5 --typed-thresholds 0.55,0.60 --abstain-thresholds 0.30,0.35`
- Code version: Local workspace; `.git` directory is absent, so no commit hash is available.
- Expected outcome: Script writes threshold metrics, raw GLiNER prediction cache and runtime summary.
- Actual result: Wrote 4 threshold rows to `artifacts/threshold_tuning_smoke/threshold_sweep.csv`, plus `raw_gliner_predictions.jsonl` and `runtime_summary.json`.
- Interpretation: The sweep infrastructure works. The 5-record smoke output is not a valid threshold-selection basis.
- Decision: Keep `configs/final_experiment.draft.json` as not frozen. Full development sweep is still required before selecting thresholds.
- Next action: Run full 2,000-record development sweep when ready, then fill `artifacts/threshold_tuning/decision.md`.

## EXP-007 Full Development Threshold Sweep

- Date: 2026-09-30
- Objective: Sweep GLiNER typed and abstention thresholds on the development set only.
- Dataset: `development_2000.json`
- System: GLiNER-only cached predictions with mapped gold labels.
- Configuration: `scripts/tune_thresholds.py --dataset data\ai4privacy_split\development_2000.json --label-mapping configs\label_mapping.json --output-dir artifacts\threshold_tuning`
- Code version: Local workspace; `.git` directory is absent, so no commit hash is available.
- Expected outcome: Complete threshold CSV, GLiNER raw prediction cache and runtime summary for 2,000 development records.
- Actual result: Wrote 30 threshold rows. Runtime summary reports 2,000 records, mean 199.75 ms, P95 251.71 ms and total 399.51 s. Mapped gold spans: 9,708; excluded gold spans: 4,627; invalid gold spans: 1.
- Interpretation: GLiNER-only performance is weak on this mapped AI4Privacy label space. The strongest exact typed recall is about 0.1178 at `typed_threshold=0.45`, but precision is lower. Stricter thresholds improve precision modestly while reducing typed recall and increasing abstention.
- Decision: Recommend `typed_threshold=0.55` and `abstain_threshold=0.40`, pending human confirmation. This keeps abstention lower than stricter typed thresholds while controlling over-redaction with the highest tested abstain threshold.
- Next action: Human confirmation is required before creating `configs/final_experiment.json` and running formal frozen experiments.

## EXP-008 Final Config Freeze and Run Script Smoke

- Date: 2026-09-30
- Objective: Freeze the experiment configuration and verify batch experiment outputs without running formal frozen evaluation.
- Dataset: Development smoke subsets only: first 10 records for Presidio and first 2 records for GLiNER.
- System: `presidio`, `gliner`
- Configuration: `configs/final_experiment.json` with `typed_threshold=0.55` and `abstain_threshold=0.40`; `scripts/run_experiment.py`
- Code version: Local workspace; `.git` directory is absent, so no commit hash is available.
- Expected outcome: Each run directory contains `config.json`, `predictions.jsonl`, `metrics.json`, `errors.jsonl`, `runtime.json` and `run.log`.
- Actual result: Smoke outputs were created under `results/runs/smoke_presidio_dev10` and `results/runs/smoke_gliner_dev2`. Unit tests passed.
- Interpretation: The frozen config and batch runner are ready for formal three-system evaluation. The smoke metrics are not reportable final results.
- Decision: Do not change label mapping, Presidio rules, GLiNER thresholds, overlap resolver or metrics implementation after this point.
- Next action: Run `presidio`, `gliner` and `hybrid` on `frozen_evaluation_3000.json`, then run all three systems on `singapore_stress.json` separately.

## EXP-009 Frozen Evaluation and Singapore Stress Runs

- Date: 2026-09-30
- Objective: Run the frozen three-system comparison and the separate 30-record Singapore stress test.
- Dataset: `frozen_evaluation_3000.json` and `singapore_stress.json`
- System: `presidio`, `gliner`, `hybrid`
- Configuration: `configs/final_experiment.json`
- Code version: Local workspace; `.git` directory is absent, so no commit hash is available.
- Expected outcome: Three complete frozen runs and three separate stress runs, each with predictions, metrics, runtime and logs.
- Actual result: Frozen runs completed with 3,000 records and 0 errors per system. Hybrid had the highest frozen recall: exact typed 0.2698, exact protective 0.3703, overlap typed 0.3385 and overlap protective 0.4744. Stress runs completed with 30 records and 0 errors per system after correcting stress gold-label normalization. Hybrid stress overlap protective recall was 0.9623.
- Interpretation: Hybrid improves recall substantially over either individual detector, but the AI4Privacy frozen result does not reach the 80% target. Stress performance is much stronger because the hand-authored examples align with the Singapore-focused recognizers and GLiNER person/address strengths.
- Decision: Preserve these results as the official frozen and stress outputs. Do not tune based on them.
- Next action: Generate per-label metrics and error analysis tables for the final report.

## EXP-010 Per-Label Results And Error Analysis

- Date: 2026-10-01
- Objective: Generate report-ready per-label metrics, error categories and representative examples from saved predictions.
- Dataset: Saved prediction files for AI4Privacy frozen and Singapore stress runs.
- System: `presidio`, `gliner`, `hybrid`
- Configuration: `scripts/analyse_errors.py --output-dir results`
- Code version: Local workspace; `.git` directory is absent, so no commit hash is available.
- Expected outcome: `results/per_label_results.csv`, `results/error_categories.csv` and `results/representative_errors.json`.
- Actual result: Generated 42 per-label rows, 44 error-category rows and 121 representative examples. Hybrid frozen errors were dominated by missed gold spans, false positives, boundary-too-long cases and label errors. Hybrid stress performance remained strong, with main residual issues around address boundary components and GLiNER false positives.
- Interpretation: Per-label analysis confirms that broad AI4Privacy government IDs and address components are the main gap, while the Singapore stress set aligns well with the project target scenario.
- Decision: Use these artifacts for the final report and demo. Do not revise detector rules or thresholds based on frozen errors.
- Next action: Draft final written analysis and record demo.

## EXP-011 Report Tables And Final Analysis Draft

- Date: 2026-10-01
- Objective: Generate report-ready Markdown tables and complete the final English analysis draft.
- Dataset: Saved result artifacts under `results`.
- System: Reporting scripts and documentation.
- Configuration: `scripts/export_report_tables.py --results-dir results --output results/report_tables.md`
- Code version: Local workspace; `.git` directory is absent, so no commit hash is available.
- Expected outcome: A reusable Markdown table export, a final English analysis draft under 1,200 words, updated Todo tracking and passing tests.
- Actual result: Generated `results/report_tables.md` with frozen, stress, runtime, per-label and Hybrid error-category tables. Added `docs/final_analysis.md` at 1,114 words.
- Interpretation: The final report now has reproducible tables and a concise analysis draft grounded in the saved evaluation outputs.
- Decision: Keep these report artifacts as generated from frozen outputs. Do not revise detector behavior based on report-writing observations.
- Next action: Run the full test suite and then record the demo.

## EXP-012 Submission Documentation And Runtime Clarification

- Date: 2026-10-01
- Objective: Close final submission gaps for report structure, data/evaluation explainability, result documentation, module-level code documentation and runtime interpretation.
- Dataset: Existing data and saved prediction artifacts only.
- System: Documentation, reporting scripts and tests.
- Configuration: No detector, threshold, label mapping, overlap resolution or frozen experiment configuration changes. `configs/final_experiment.json` SHA-256: `34B457479DAA048C851E92475074D2CA2068809C29DF64A81360B0E34C06F8BD`.
- Code version: Local workspace; `.git` directory is absent, so no commit hash is available.
- Expected outcome: Add submission explainer files, improve README product documentation, restructure the final report draft, clarify cold-start runtime, preserve official predictions and pass the full test suite.
- Actual result: Added `data/README.md`, `docs/EVALUATION.md` and `results/README.md`; expanded README with persona, input/output, architecture, target/reached metrics, documentation map and test command; rewrote `docs/final_analysis.md` with structured headings and 1,028 words; added module/API docstrings; updated `scripts/analyse_errors.py` to derive first-record and warm runtime from saved predictions; regenerated `results/runtime_summary.json` and `results/report_tables.md`; removed accidental root file `4.25.0`.
- Hash check: data hashes match `artifacts/data_audit/data_sha256_manifest.json`: development `164CB9CC78EDC45994A3B50CE6B95C1E8CD9DB071290CD2A2C6A49C1E58EDB81`, frozen `05917B6E4F68EDC7CD10F1808C1982F0550CFC63FBD0ED8C5EBCDC493A854EF1`, Singapore stress `88E08F7FF492333EC19F3360A326461B31C8C83B6A88AD047C06B12FD97A5ACE`.
- Prediction hash check: formal predictions were not regenerated. Current SHA-256 values are Presidio frozen `34FBC149DA7E68BB811117392AB43239245B7CF4C808FCE05BE312DB69C9951D`, GLiNER frozen `BBD1E123930CF26609A755E5896C0F8281BDE40562BD2DDDB2EA51D332B5219F`, Hybrid frozen `56FF3D048EC6FC8473909DB0AD7531322D5C5A70663EE16B0C43B862F6DC7568`, Presidio stress `1293009964A34FE4A51DE8575807B00A641B8561429DAE2093870F22C1383295`, GLiNER stress `1DDF9B4127DA45C3D72EB1CD760383B5CAE6410EF7BB782DDC0A65A58C611D37`, Hybrid stress `A655D3965790474EECD50FFFEF89FE5693D2F471BFB27CB8A894E57DBC5F80BA`.
- Test result: `conda run -n safepaste python -m unittest discover -s tests -v` ran 29 tests in 10.143 s; all passed.
- Interpretation: Submission materials now explain the product, data, evaluation, results and limitations without claiming production readiness. Runtime reporting distinguishes cold-start effects from warm local inference.
- Decision: Preserve frozen metrics and official prediction files. Do not tune or rerun formal detector experiments for this documentation pass.
- Next action: Student should record/check in the required face-and-screen demo video and manually review the 30 fictional stress records before submission.

## EXP-013 V2 Product-Scope Mapping Re-Score

- Date: 2026-10-01
- Objective: Preserve the official V1 broad benchmark while adding a V2 product-scope mapping view after the low V1 frozen score exposed label-scope mismatch.
- Dataset: Existing source datasets and saved prediction files under `results/runs`; detectors were not rerun.
- System: Re-scoring script and alternate label mapping.
- Configuration: `configs/label_mapping_v2_product_scope.json`; `scripts/reevaluate_saved_predictions.py --mapping configs/label_mapping_v2_product_scope.json --output-dir results --suffix v2`.
- Code version: Local workspace; `.git` directory is absent, so no commit hash is available.
- Expected outcome: V1 remains unchanged; V2 writes separate result files and clearly states it is a post-evaluation diagnostic view, not the official frozen baseline.
- Actual result: Added `configs/label_mapping_v2_product_scope.json`, `scripts/reevaluate_saved_predictions.py` and `docs/V2_PRODUCT_SCOPE_MAPPING.md`. Generated `results/main_results_v2.csv`, `results/singapore_stress_results_v2.csv`, `results/per_label_results_v2.csv`, `results/report_tables_v2.md` and `results/mapping_v2_summary.json`.
- V2 result: AI4Privacy frozen Hybrid exact typed recall is 47.86% and overlap protective recall is 65.14% over 8,268 product-scope gold spans. Singapore stress metrics are unchanged: Hybrid exact typed recall 92.45% and overlap protective recall 96.23%.
- Interpretation: V2 confirms that part of the V1 low score comes from generic government-ID and broad location labels outside current product-scope recognizer coverage. It still does not reach the original 80% target on AI4Privacy frozen, so address boundary, phone generalization and precision issues remain.
- Decision: Keep V1 as the official broad benchmark. Use V2 only as a post-evaluation product-scope analysis and improvement narrative.
- Test result: `conda run -n safepaste python -m unittest discover -s tests -v` ran 30 tests in 10.655 s; all passed.
- Next action: If further code work is allowed, implement a true V3 recognizer coverage improvement for generic government IDs and address normalization, then evaluate it as a separate post-baseline experiment.

## Template

```markdown
## EXP-XXX Title

- Date:
- Objective:
- Dataset:
- System:
- Configuration:
- Code version:
- Expected outcome:
- Actual result:
- Interpretation:
- Decision:
- Next action:
```
