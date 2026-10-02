# V2 Product-Scope Mapping

This document explains the V2 mapping added after the official V1 frozen evaluation.

## Purpose

V1 remains the official broad benchmark result. It maps a wide range of AI4Privacy labels into SafePaste targets, including generic multi-country government identifiers and broad address/location components. That broad mapping is useful because it exposed major coverage gaps.

V2 is a separate post-evaluation analysis view. It asks a narrower question:

> How do the same saved predictions score when the gold labels are limited to the product scope SafePaste actually claimed to handle for Tonya-style support text?

V2 does not rerun detectors, change thresholds, change overlap resolution or replace the official V1 result.

## Files

- Mapping: `configs/label_mapping_v2_product_scope.json`
- Re-score script: `scripts/reevaluate_saved_predictions.py`
- Main frozen V2 results: `results/main_results_v2.csv`
- Singapore stress V2 results: `results/singapore_stress_results_v2.csv`
- Per-label V2 results: `results/per_label_results_v2.csv`
- Report tables: `results/report_tables_v2.md`
- Run summary: `results/mapping_v2_summary.json`

## Mapping Changes From V1

V2 keeps direct support-text PII:

- `EMAIL` -> `EMAIL`
- `TEL` -> `PHONE`
- `IP` -> `IP_ADDRESS`
- Given and last-name labels -> `PERSON`
- `BUILDING`, `GEOCOORD`, `POSTCODE`, `SECADDRESS`, `STREET` -> `ADDRESS`

V2 excludes broad or currently unsupported labels:

- Generic government ID labels: `DRIVERLICENSE`, `IDCARD`, `PASSPORT`, `SOCIALNUMBER`
- Broad location-only labels: `CITY`, `COUNTRY`, `STATE`
- Already out-of-scope labels: `BOD`, `DATE`, `PASS`, `SEX`, `TIME`, `TITLE`, `USERNAME`

`GOVERNMENT_ID` remains a target label for local aliases and the Singapore stress set. The point is not that government IDs are unimportant; it is that the current V1 detector does not yet claim generic multi-country government-ID coverage. That remains a future recognizer-pack task.

## Results

On AI4Privacy frozen, the V2 product-scope denominator is 8,268 gold spans instead of V1's 14,685 mapped gold spans.

Hybrid V2 AI4Privacy frozen results:

- Exact typed recall: 47.86%
- Exact protective recall: 51.26%
- Overlap typed recall: 59.91%
- Overlap protective recall: 65.14%
- Exact typed precision: 38.36%
- Overlap typed precision: 48.02%

The Singapore stress results are unchanged because those labels already match the product-scope target set:

- Hybrid exact typed recall: 92.45%
- Hybrid overlap protective recall: 96.23%

## Interpretation

V2 shows that a large part of the low V1 score came from evaluating against labels outside the implemented product-scope recognizer coverage. It also shows that V2 is still not enough to reach the original 80% target on AI4Privacy frozen. Address boundary issues, phone-format generalization and person-name false positives remain.

The honest conclusion is:

- V1 is the official broad benchmark and should stay in the report.
- V2 is a diagnostic product-scope view created after discovering the low V1 result.
- V2 supports the argument that SafePaste is more aligned with Tonya-style support text than with all AI4Privacy labels.
- V2 does not remove the need for a future generic government-ID and address-normalization recognizer pack.

## Reproduction

From the project root:

```powershell
conda activate safepaste
$env:PYTHONPATH = "src;."
python scripts\reevaluate_saved_predictions.py --mapping configs\label_mapping_v2_product_scope.json --output-dir results --suffix v2
```

This command reads the saved prediction files under `results/runs`. It does not call Presidio or GLiNER.
