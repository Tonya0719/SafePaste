# SafePaste Data

This directory holds the datasets used to build and evaluate SafePaste on the author's machine. A public checkout contains the project-authored `singapore_stress.json`; regenerate the AI4Privacy splits locally with the commands below. The project uses synthetic or fictional records only, not real customer support conversations or real customer PII.

## Source Dataset

The broad benchmark source is `ai4privacy/pii-masking-300k` on Hugging Face:

https://huggingface.co/datasets/ai4privacy/pii-masking-300k

SafePaste uses this dataset because it provides text spans for many PII-like labels and is suitable for testing a masking pipeline. It is still a synthetic benchmark, not real e-commerce support data. Results on this dataset should be treated as a coverage stress test, not as proof of production safety.

The [AI4Privacy license](https://huggingface.co/datasets/ai4privacy/pii-masking-300k/blob/main/LICENSE.md) grants academic non-commercial use and states that redistribution, sharing and dissemination of derivative works require explicit written permission. Accordingly, the public repository provides generation/evaluation code, seed, hashes and aggregate outputs, while the downloaded records and row-level prediction/error examples remain local. This limits how much of the exact evaluation can be inspected from a public checkout alone; an authorised user can regenerate those artifacts using the documented commands.

## Files And Splits

The AI4Privacy split was created with fixed random seed `6201`:

| File | Records | Purpose |
|---|---:|---|
| `data/ai4privacy_split/development_2000.json` | 2,000 | Generated locally; development-only label mapping, rule work and threshold selection. |
| `data/ai4privacy_split/frozen_evaluation_3000.json` | 3,000 | Generated locally; final frozen comparison for Presidio-only, GLiNER-only and Hybrid. |
| `data/singapore_stress.json` | 30 | Included in the repository; fictional Singapore-style support messages for a scenario-focused stress test. |

The 30 Singapore-style examples are hand-authored fictional text. They should be manually reviewed by the student before submission and must not be described as production data or as representative of real customer traffic.

## Record Format

Each JSON file contains a list of records. Each record has:

- `id`: a stable record identifier when present.
- `text`: the synthetic or fictional message text.
- `spans`: gold labels with `start`, `end` and `label`.

Span offsets use Python-style half-open intervals: `[start, end)`. The character at `start` is included, and the character at `end` is excluded.

## Label Mapping

AI4Privacy source labels are mapped into the SafePaste evaluation label space by `configs/label_mapping.json`.

Target labels:

- `ADDRESS`
- `EMAIL`
- `FINANCIAL`
- `GOVERNMENT_ID`
- `IP_ADDRESS`
- `PERSON`
- `PHONE`

Mapped examples:

- `BUILDING`, `CITY`, `COUNTRY`, `GEOCOORD`, `POSTCODE`, `SECADDRESS`, `STATE`, `STREET` -> `ADDRESS`
- `GIVENNAME1`, `GIVENNAME2`, `LASTNAME1`, `LASTNAME2`, `LASTNAME3` -> `PERSON`
- `DRIVERLICENSE`, `IDCARD`, `PASSPORT`, `SOCIALNUMBER` -> `GOVERNMENT_ID`
- `EMAIL` -> `EMAIL`
- `IP` -> `IP_ADDRESS`
- `TEL` -> `PHONE`

Excluded labels:

- `BOD`
- `DATE`
- `PASS`
- `SEX`
- `TIME`
- `TITLE`
- `USERNAME`

Excluded gold labels are not counted as detector failures in the normalized evaluation. They are outside the current SafePaste project scope and are reported as limitations.

## Data Audit Notes

The data audit artifacts are under `artifacts/data_audit`.

- `record_summary.csv` records the row counts, gold span counts and audit issue counts.
- A locally generated `invalid_spans.csv` records one development-set out-of-bounds span: `development-00543`, label `GEOCOORD`, range `197:229`.
- `overlapping_gold_spans.csv` records source gold-span overlaps. The development split has 44 overlap relations, the frozen evaluation split has 82 and the Singapore stress set has none.
- `data_sha256_manifest.json` records file sizes, record counts, span counts and SHA-256 hashes.

Invalid gold spans are excluded during normalized evaluation and counted explicitly. Overlapping gold spans are preserved in the source data audit, while evaluation uses one-to-one prediction/gold matching to avoid duplicate predictions inflating metrics.

## Reproduction Commands

From the project root:

```powershell
conda activate safepaste
$env:PYTHONPATH = "src;."
python -m pip install -e ".[data]"
python scripts/prepare_ai4privacy.py --output data/ai4privacy_split --seed 6201
python scripts/audit_dataset.py --output artifacts/data_audit
```

The locally generated split manifest is `data/ai4privacy_split/manifest.json`. The included SHA-256 manifest is `artifacts/data_audit/data_sha256_manifest.json`. Compare the hashes below after regeneration; an upstream dataset revision can change the sampled files, so a mismatch must be documented rather than silently treated as the same frozen set.

Current SHA-256 values:

| File | SHA-256 |
|---|---|
| `data/ai4privacy_split/development_2000.json` | `164cb9cc78edc45994a3b50ce6b95c1e8cd9db071290cd2a2c6a49c1e58edb81` |
| `data/ai4privacy_split/frozen_evaluation_3000.json` | `05917b6e4f68edc7cd10f1808c1982f0550cfc63fbd0ed8c5ebcdc493a854ef1` |
| `data/singapore_stress.json` | `88e08f7ff492333ec19f3360a326461b31c8c83b6a88ad047c06b12fd97a5ace` |
