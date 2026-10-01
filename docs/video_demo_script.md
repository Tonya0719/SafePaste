# Video Demo Script Outline

Recommended length: 5-7 minutes.

## 0:00-0:40 Problem Setup

- Introduce Tonya, an e-commerce support agent.
- Scenario: Tonya wants to paste customer support text into a public AI assistant.
- Risk: the text may contain names, phone numbers, emails, local addresses or NRIC-shaped IDs.
- State the project goal: local review and masking before paste.

## 0:40-1:30 Architecture

- Show repository or a simple diagram verbally:
  - Presidio-only for structured PII.
  - GLiNER-only for contextual names and addresses.
  - Hybrid combines both.
- Explain local-first design:
  - No external per-call API.
  - GLiNER model is stored locally.
  - Web server runs on `127.0.0.1`.
- Mention reversible placeholders and `[POSSIBLE_PII]`.

## 1:30-2:50 Live UI Demo

Start server:

```powershell
conda activate safepaste
cd C:\Users\DELL\Desktop\safepaste
$env:PYTHONPATH = "src;."
Remove-Item Env:SAFEPASTE_GLINER_MODEL -ErrorAction SilentlyContinue
python -m safepaste.server --mode hybrid
```

Open:

```text
http://127.0.0.1:8765
```

Paste this fictional example:

```text
Customer Mei Tan says parcel should go to Blk 123 Ang Mo Kio Ave 3, #12-34 Singapore 560123. Please call +65 9123 4567 or email mei.tan@example.com.
```

Show:

- Name detected by GLiNER.
- Address detected by GLiNER/Presidio components.
- Phone and email detected by Presidio.
- Redacted output.
- Restore all.
- Copy sanitised text.

## 2:50-3:40 Edge Case Demo

Paste:

```text
Customer gave NRIC S1234567D for verification. Please call 91234567. Do not mask order number 20240929.
```

Show:

- NRIC-shaped string is masked.
- Phone is masked.
- Ordinary order number should remain visible.
- This illustrates precision and over-redaction control.

## 3:40-4:50 Evaluation Method

- Show or mention:
  - `development_2000.json` for label mapping and threshold choice.
  - `frozen_evaluation_3000.json` for final evaluation.
  - `singapore_stress.json` for 30 separate local-style examples.
- Three systems:
  - Presidio-only.
  - GLiNER-only.
  - Hybrid.
- Metrics:
  - exact vs overlap recall.
  - typed vs protective recall.
  - precision and abstention rate.
- Explain why exact and overlap are both reported:
  - Exact measures boundary quality.
  - Overlap measures whether sensitive text was at least covered.

## 4:50-5:50 Results

AI4Privacy frozen:

- Presidio-only overlap protective recall: 21.85%.
- GLiNER-only overlap protective recall: 28.04%.
- Hybrid overlap protective recall: 47.44%.
- Say clearly: the 80% target was not reached on the broad frozen benchmark.

Singapore stress:

- Hybrid exact typed recall: 92.45%.
- Hybrid overlap protective recall: 96.23%.
- Explain: this better matches the intended Singapore support-text scenario.

## 5:50-6:40 Trade-Offs And Limitations

- Hybrid improves recall but lowers precision compared with Presidio-only.
- AI4Privacy is synthetic and broader than Tonya's real support text.
- The system is English-focused.
- It does not detect trade secrets.
- It does not replace enterprise DLP.
- Restore map contains original PII and must not be logged.

## 6:40-7:00 Closing

- Final message:
  - SafePaste did not hit the broad benchmark target.
  - It demonstrates a practical local-first architecture.
  - It performs strongly on the intended Singapore support-text stress test.
  - Future work: more recognizers and better address span normalization.
