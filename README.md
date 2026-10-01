# SafePaste

SafePaste is a local-first prototype that checks English workplace text for personally identifiable information before it is pasted into a public AI assistant. It combines Presidio-based pattern recognizers for structured identifiers with an optional locally stored GLiNER model for contextual entities such as people and addresses. Detected spans are replaced with reversible placeholders and uncertain model results are shown as `[POSSIBLE_PII_n]`.

This repository implements the scope stated in the PE6201 milestone. PrivacyScrubber is prior work and positioning context; this code is not a fork of PrivacyScrubber. The implementation owns orchestration, review, reversible masking and evaluation, while allowing Presidio/GLiNER to be reused as local detection components.

## Run the working MVP

Install SafePaste in editable mode, then start the local server:

```powershell
conda activate safepaste
cd C:\Users\DELL\Desktop\safepaste
$env:PYTHONPATH = "src;."
python -m pip install -e .
python -m safepaste.server --mode hybrid
```

Open `http://127.0.0.1:8765`. The server binds only to the loopback interface and makes no network request during analysis.

CLI usage:

```powershell
$env:PYTHONPATH = "src"
python -m safepaste.cli analyze "Please call Mei at +65 9123 4567" --mode presidio
```

Supported modes:

- `presidio`: Presidio-only structured PII baseline.
- `regex`: compatibility alias for `presidio`, retained for earlier commands and reports that call this the regex/rule baseline.
- `gliner`: GLiNER-only contextual PII detector.
- `hybrid`: Presidio + GLiNER with shared overlap resolution.
- `regex-legacy`: old hand-written regex detector for debugging and comparison only; do not use it for the formal three-system experiment.

## Enable local GLiNER

Install the optional dependency and download a model deliberately during setup. Do not let the application fetch a model while processing user text.

```powershell
python -m pip install -e ".[ml]"
python -m safepaste.server --mode hybrid
```

Create a `.env` file in the project root to configure the local model:

```dotenv
SAFEPASTE_GLINER_MODEL=C:\path\to\local\gliner-model
```

SafePaste loads this file automatically. An environment variable set directly in
PowerShell still takes precedence over the value in `.env`.

The adapter calls `GLiNER.from_pretrained()` only with the configured local directory. If the package or directory is absent, hybrid mode reports the problem instead of silently claiming NER coverage.

## Evaluation

The evaluator reports the four combinations requested by the instructor:

- exact typed recall
- exact protective recall (includes abstentions)
- overlap typed recall
- overlap protective recall (includes abstentions)

It also reports precision and abstention rate. Predictions are matched one-to-one with gold spans, preventing duplicate predictions from inflating a score.

```powershell
$env:PYTHONPATH = "src"
python -m safepaste.cli evaluate data/singapore_stress.json --mode presidio
```

The 30 hand-authored Singapore-style examples are fictional and must remain a separate stress set. Do not tune thresholds or patterns against them if they are being reported as an independent test.

### Formal experiment commands

The final configuration is frozen in `configs/final_experiment.json`. After this file is frozen, do not change detector rules, thresholds, label mapping, overlap resolution or metrics based on frozen results.

```powershell
python scripts\run_experiment.py --dataset data\ai4privacy_split\frozen_evaluation_3000.json --system presidio --config configs\final_experiment.json --output results\runs\presidio_frozen
python scripts\run_experiment.py --dataset data\ai4privacy_split\frozen_evaluation_3000.json --system gliner --config configs\final_experiment.json --output results\runs\gliner_frozen
python scripts\run_experiment.py --dataset data\ai4privacy_split\frozen_evaluation_3000.json --system hybrid --config configs\final_experiment.json --output results\runs\hybrid_frozen

python scripts\run_experiment.py --dataset data\singapore_stress.json --system presidio --config configs\final_experiment.json --output results\runs\presidio_stress
python scripts\run_experiment.py --dataset data\singapore_stress.json --system gliner --config configs\final_experiment.json --output results\runs\gliner_stress
python scripts\run_experiment.py --dataset data\singapore_stress.json --system hybrid --config configs\final_experiment.json --output results\runs\hybrid_stress
```

Each run writes `config.json`, `predictions.jsonl`, `metrics.json`, `errors.jsonl`, `runtime.json` and `run.log`.

### Final results

AI4Privacy frozen evaluation, 3,000 records:

| System | Exact typed R | Exact protective R | Overlap typed R | Overlap protective R | Exact typed P | Abstention |
|---|---:|---:|---:|---:|---:|---:|
| Presidio-only | 15.46% | 19.74% | 16.36% | 21.85% | 68.55% | 0.00% |
| GLiNER-only | 11.60% | 17.98% | 17.59% | 28.04% | 23.41% | 14.61% |
| Hybrid | 26.98% | 37.03% | 33.85% | 47.44% | 38.41% | 10.05% |

Singapore-style stress set, 30 fictional hand-authored support messages:

| System | Exact typed R | Exact protective R | Overlap typed R | Overlap protective R | Exact typed P | Abstention |
|---|---:|---:|---:|---:|---:|---:|
| Presidio-only | 43.40% | 43.40% | 60.38% | 60.38% | 60.53% | 0.00% |
| GLiNER-only | 50.94% | 54.72% | 50.94% | 56.60% | 72.97% | 5.13% |
| Hybrid | 92.45% | 94.34% | 94.34% | 96.23% | 81.67% | 1.64% |

The 80% target was not reached on the broad AI4Privacy frozen benchmark. Hybrid still substantially improves recall over either single detector. On the project-specific Singapore support-text stress set, Hybrid reaches 96.23% overlap protective recall.

Generated analysis artifacts:

- `results/main_results.csv`
- `results/per_label_results.csv`
- `results/singapore_stress_results.csv`
- `results/error_categories.csv`
- `results/representative_errors.json`
- `results/runtime_summary.json`

## Prepare the AI4Privacy split

The milestone names `ai4privacy/pii-masking-300k` as the source. Install the data extra, then run:

```powershell
python -m pip install -e ".[data]"
python scripts/prepare_ai4privacy.py --output data/ai4privacy_split --seed 6201
```

The script creates 2,000 development records and 3,000 frozen evaluation records using a deterministic reservoir sample. Review the dataset license before redistribution or commercial use. Do not commit the downloaded records to a public repository without confirming the license terms.

## Project structure

- `src/safepaste`: detectors, hybrid orchestration, reversible redaction, evaluator, CLI and local web UI
- `data/singapore_stress.json`: 30 fictional Singapore support messages with character spans
- `scripts/prepare_ai4privacy.py`: deterministic AI4Privacy sample preparation
- `scripts/run_experiment.py`: reproducible batch experiments for Presidio-only, GLiNER-only and Hybrid
- `scripts/analyse_errors.py`: per-label metrics, error categories and representative examples
- `tests`: unit and integration tests using Python's standard library

## Important limitations

- Regex-only mode cannot reliably identify contextual names and addresses.
- GLiNER results depend on the selected model, label vocabulary and threshold.
- `[POSSIBLE_PII]` improves protective coverage but is not counted in typed recall.
- The AI4Privacy benchmark is synthetic and broader than the Tonya support-text scenario.
- The current system is English-focused and tuned for local structured PII plus person/address detection.
- SafePaste does not detect trade secrets, make legal compliance decisions or replace enterprise DLP.
- The restore map itself contains the original PII and must not be logged or persisted.
