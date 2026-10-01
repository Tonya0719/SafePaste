# Final English Analysis Outline

Target length: 1,050-1,150 words, leaving margin under the 1,200-word limit.

## 1. Problem And Significance, about 120 words

- User: Tonya, an e-commerce support agent.
- Problem: she may paste customer support text into a public AI assistant and accidentally expose PII.
- Why it matters: customer privacy, organisational risk and invisible failure.
- Scope: English workplace/support text before AI upload.
- Non-goals: trade secrets, legal compliance decisions, multilingual DLP and enterprise-grade enforcement.

## 2. Proposed Solution, about 150 words

- SafePaste runs locally before paste/upload.
- Presidio-based recognizers detect structured PII: email, phone, IP, credit card, Singapore NRIC-shaped strings, unit numbers and postal codes.
- Local GLiNER detects contextual PII such as names and addresses.
- Hybrid orchestration merges spans and resolves overlaps.
- Low-confidence GLiNER spans become `[POSSIBLE_PII]`.
- Reversible placeholders let Tonya restore false positives before copying.
- PrivacyScrubber is named as prior work; SafePaste does not claim category novelty.

## 3. Business And Technical Trade-Offs, about 280-320 words

- Local vs cloud:
  - Local avoids sending customer text to an external API.
  - No external per-call API fee.
  - Trade-off: local model setup, latency and model maintenance.
- Rules vs NER:
  - Presidio is precise for structured identifiers.
  - GLiNER is useful for names and addresses but weaker on exact boundaries and structured IDs.
  - Hybrid improves recall but reduces precision on the broad benchmark.
- Build vs reuse:
  - Reused Presidio and GLiNER.
  - Built UI, orchestration, abstention, reversible redaction and evaluation.
- No RAG or agent:
  - No retrieval or tool planning is needed.
  - The task is detection and masking, not knowledge synthesis.
- Product trade-off:
  - Over-redaction can reduce usefulness.
  - Under-redaction can leak PII.
  - Reversible placeholders and visible review reduce both risks.

## 4. Data And Evaluation, about 220 words

- AI4Privacy PII-Masking-300K is synthetic, not Tonya's real support text.
- Fixed seed 6201.
- 2,000 development records for label mapping, rule development and threshold selection.
- 3,000 frozen evaluation records for final comparison.
- 30 hand-authored fictional Singapore support messages separately reported.
- Three systems:
  - Presidio-only
  - GLiNER-only
  - Hybrid
- Metrics:
  - exact typed recall
  - exact protective recall
  - overlap typed recall
  - overlap protective recall
  - precision
  - abstention rate
- One-to-one matching prevents duplicate predictions from inflating results.

## 5. Results And Interpretation, about 220-260 words

- AI4Privacy frozen:
  - Presidio-only overlap protective recall: 21.85%.
  - GLiNER-only overlap protective recall: 28.04%.
  - Hybrid overlap protective recall: 47.44%.
  - Hybrid exact typed recall: 26.98%.
  - 80% target was not reached.
- Explain why:
  - AI4Privacy has broad, fine-grained labels.
  - Government IDs and address components are not fully covered.
  - GLiNER often detects broad contextual spans, while gold labels may mark smaller components.
- Singapore stress:
  - Hybrid overlap protective recall: 96.23%.
  - Hybrid exact typed recall: 92.45%.
  - This better matches the target product scenario.
- Interpretation:
  - The architecture is useful for Tonya-style support text.
  - The benchmark exposes limits in broad synthetic PII coverage.

## 6. Risks, Limitations And Responsible Use, about 150 words

- Silent failure remains the main risk.
- False positives may remove useful context.
- Synthetic-to-real domain gap.
- English-only scope.
- Does not detect trade secrets.
- Does not replace enterprise DLP or legal compliance review.
- Restore map contains original PII and must not be logged or persisted.
- Future work:
  - More recognizers for passport, driver licence and generic government IDs.
  - Better address span normalization.
  - Human review of false positives and false negatives.
  - Larger real-world but non-sensitive support-text evaluation.
