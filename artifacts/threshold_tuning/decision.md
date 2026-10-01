# Threshold Tuning Decision

Status: Frozen for evaluation on 2026-09-30.

This file must be completed after running the full development-set sweep. Do not use frozen evaluation results to edit this decision.

## Inputs

- Dataset: `data/ai4privacy_split/development_2000.json`
- Label mapping: `configs/label_mapping.json`
- Sweep output: `artifacts/threshold_tuning/threshold_sweep.csv`
- Raw prediction cache: `artifacts/threshold_tuning/raw_gliner_predictions.jsonl`

## Candidate Thresholds

| typed_threshold | abstain_threshold | Exact typed R | Overlap typed R | Typed P | Protective R | Abstention |
|---:|---:|---:|---:|---:|---:|---:|
| 0.55 | 0.40 | 0.1114 | 0.1680 | 0.2322 exact / 0.3503 overlap | 0.1814 exact / 0.2746 overlap | 0.1539 |
| 0.65 | 0.40 | 0.1028 | 0.1561 | 0.2447 exact / 0.3715 overlap | 0.1814 exact / 0.2746 overlap | 0.2589 |
| 0.70 | 0.40 | 0.0987 | 0.1504 | 0.2541 exact / 0.3873 overlap | 0.1814 exact / 0.2746 overlap | 0.3149 |

## Selection Criteria

1. Maintain acceptable typed precision and avoid excessive over-redaction.
2. Improve exact typed recall under that precision constraint.
3. Compare protective recall gain against abstention rate.
4. Check PERSON and ADDRESS per-label behavior.
5. Read representative false positives and false negatives from development results.

## Final Choice

- typed_threshold: 0.55
- abstain_threshold: 0.40

## Rationale

The recommendation is based only on the 2,000-record development sweep. No frozen evaluation result was used.

`abstain_threshold=0.40` is recommended because it controls over-redaction better than lower abstain thresholds. Compared with `0.35`, it lowers predicted spans from 5,826 to 5,503 and keeps abstention lower while giving up only about 1.1 percentage points of overlap protective recall.

`typed_threshold=0.55` is recommended because raising the typed threshold gives only modest precision gains but costs typed recall and substantially increases the abstention rate. At `0.55/0.40`, GLiNER has exact typed recall 0.1114, overlap typed recall 0.1680, exact typed precision 0.2322, overlap typed precision 0.3503 and abstention rate 0.1539. This is a weak GLiNER-only result, but it preserves more useful typed PERSON/ADDRESS detections for Hybrid than the stricter 0.65 or 0.70 options.

The result also shows a clear limitation: GLiNER-only is not a strong detector for the mapped AI4Privacy label space. It mainly helps PERSON and some ADDRESS cases, while Presidio remains necessary for structured PII.

## Freeze Checklist

- [x] Label mapping frozen.
- [x] Presidio rules frozen.
- [x] GLiNER thresholds frozen.
- [x] Overlap resolver frozen.
- [x] Metrics implementation frozen.
- [x] `configs/final_experiment.json` created from the draft config.
