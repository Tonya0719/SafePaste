# SafePaste Evaluation

This document explains how SafePaste was evaluated. The public repository includes code, configuration, aggregate results and hashes. AI4Privacy source records and row-level prediction files are regenerated locally because the source license requires written permission for redistribution; see `data/README.md`.

## Formal Systems

The formal comparison uses three systems:

| System | Mode | Definition |
|---|---|---|
| Presidio-only | `presidio` | Structured PII baseline using Presidio recognizers plus SafePaste's Singapore-specific recognizers. |
| GLiNER-only | `gliner` | Local GLiNER contextual detector for labels such as person and address. |
| Hybrid | `hybrid` | Presidio plus GLiNER with shared overlap resolution and reversible redaction. |

`regex` is a compatibility alias for `presidio`. `regex-legacy` is the older hand-written detector retained for debugging only; it is not part of the formal three-system experiment.

## Development And Frozen Boundaries

The development split, `data/ai4privacy_split/development_2000.json`, was used for label mapping, rule development and threshold selection. The frozen evaluation split, `data/ai4privacy_split/frozen_evaluation_3000.json`, was used only after the final configuration was frozen.

The final configuration is `configs/final_experiment.json`, frozen on 2026-09-30. It uses:

- GLiNER typed threshold: `0.55`
- GLiNER abstention threshold: `0.40`
- Label mapping: `configs/label_mapping.json`
- Matching policy: one-to-one prediction/gold matching

The development sweep tested 30 threshold combinations. The selected `0.55 / 0.40` threshold pair was not the highest possible protective-recall setting. It was chosen because lower abstention thresholds created more over-redaction, while higher typed thresholds increased abstention and reduced useful typed PERSON/ADDRESS detections. This is threshold calibration, not model fine-tuning. GLiNER weights were not trained or modified.

## Metrics

Recall:

```text
Recall = matched gold spans / all eligible gold spans
```

Precision:

```text
Precision = matched predictions / all eligible predictions
```

Abstention rate:

```text
Abstention rate = abstained predictions / all predictions
```

Boundary modes:

- Exact-span matching requires `prediction.start == gold.start` and `prediction.end == gold.end`.
- Overlap matching requires the prediction and gold span ranges to overlap by at least one character.

Prediction modes:

- Typed matching requires the SafePaste label to match the gold label.
- Protective matching includes typed predictions and abstained `[POSSIBLE_PII]` predictions. Abstained predictions can protect text ranges but do not count as typed-label success.

The evaluator uses one-to-one matching. A prediction can match at most one gold span, and a gold span can match at most one prediction. This prevents duplicate predictions from inflating recall or precision.

Label mapping is applied before scoring. Gold labels mapped to `EXCLUDED` are removed from the eligible denominator and are not counted as detector failures. Invalid gold spans are also excluded and counted separately.

## Formal Commands

From the project root:

```powershell
conda activate safepaste
$env:PYTHONPATH = "src;."

python scripts\run_experiment.py --dataset data\ai4privacy_split\frozen_evaluation_3000.json --system presidio --config configs\final_experiment.json --output results\runs\presidio_frozen
python scripts\run_experiment.py --dataset data\ai4privacy_split\frozen_evaluation_3000.json --system gliner --config configs\final_experiment.json --output results\runs\gliner_frozen
python scripts\run_experiment.py --dataset data\ai4privacy_split\frozen_evaluation_3000.json --system hybrid --config configs\final_experiment.json --output results\runs\hybrid_frozen

python scripts\run_experiment.py --dataset data\singapore_stress.json --system presidio --config configs\final_experiment.json --output results\runs\presidio_stress
python scripts\run_experiment.py --dataset data\singapore_stress.json --system gliner --config configs\final_experiment.json --output results\runs\gliner_stress
python scripts\run_experiment.py --dataset data\singapore_stress.json --system hybrid --config configs\final_experiment.json --output results\runs\hybrid_stress
```

Each run directory contains:

- `config.json`: the frozen configuration copied into the run output.
- `predictions.jsonl`: one row per record with gold spans, predicted spans, warnings and runtime.
- `metrics.json`: aggregate recall, precision, abstention and count metrics.
- `errors.jsonl`: runtime failures, if any.
- `runtime.json`: per-run runtime summary.
- `run.log`: command-level run notes.

After generating the source split and running the six formal commands locally, regenerate the derived result summaries from the saved predictions:

```powershell
python scripts\analyse_errors.py --output-dir results
python scripts\export_report_tables.py --results-dir results --output results\report_tables.md
```

This regenerates `per_label_results.csv`, `error_categories.csv`, local `representative_errors.json`, `runtime_summary.json` and `report_tables.md` without rerunning the detectors. The row-level `representative_errors.json` must remain local unless redistribution permission is obtained.

## Final Results

AI4Privacy frozen evaluation and Singapore stress results must be reported separately.

AI4Privacy frozen, 3,000 records and 14,685 mapped gold spans:

- Presidio-only overlap protective recall: 21.85%.
- GLiNER-only overlap protective recall: 28.04%.
- Hybrid exact typed recall: 26.98%.
- Hybrid overlap protective recall: 47.44%.

Singapore stress set, 30 fictional records and 53 gold spans:

- Hybrid exact typed recall: 92.45%.
- Hybrid overlap protective recall: 96.23%.

The original target was 80% exact-span recall and better performance than the rule-only baseline. The 80% target was not reached on the broad AI4Privacy frozen benchmark. Hybrid did improve recall over either single detector. The Singapore stress result is much stronger because it is closer to the target support-agent scenario, but it is small, fictional and hand-authored, so it is not production evidence.

## Runtime Interpretation

`results/runtime_summary.json` separates first-record latency from warm latency. The first record includes detector/model cold start and can dominate small sets such as the 30-record stress set. Warm metrics exclude the first record and better describe steady-state local inference. The original end-to-end total runtime is still preserved.

## Evaluation Limitations

- AI4Privacy is synthetic and broader than the Tonya e-commerce support scenario.
- The Singapore stress set is fictional, small and manually designed.
- Exact boundary scoring is strict and penalizes broad contextual spans.
- Protective scoring is useful for privacy review but can increase user review burden.
- GLiNER and Presidio cover different label types; broad government IDs and address components remain major gaps.
- Results do not prove legal compliance or enterprise DLP readiness.

## V2 Product-Scope Mapping

After the official V1 frozen evaluation, a separate V2 product-scope mapping was added for diagnosis. V2 keeps V1 unchanged and re-scores the same saved prediction files with `configs/label_mapping_v2_product_scope.json`. It excludes generic multi-country government-ID labels and broad location-only labels that the current product did not claim to cover, while retaining direct support-text PII such as names, email, phone, IP addresses and direct address components.

V2 outputs are:

- `results/main_results_v2.csv`
- `results/singapore_stress_results_v2.csv`
- `results/per_label_results_v2.csv`
- `results/report_tables_v2.md`
- `results/mapping_v2_summary.json`

See `docs/V2_PRODUCT_SCOPE_MAPPING.md` for rationale and reproduction commands. V2 is a post-evaluation analysis view; it does not replace the official V1 benchmark and does not rerun detectors.
