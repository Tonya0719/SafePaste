# SafePaste video demo script

Aim for about 6–7 minutes. Record your face in a small camera window while the screen remains readable. Use only the local SafePaste page, `README.md`, and `results/report_tables.md`; no slides are needed. Speak naturally rather than reading every number on screen.

## Before recording

1. Start the server from the project root: `python -m safepaste.server --mode hybrid` in the `safepaste` environment. Open `http://127.0.0.1:8765` and run one check before recording so the model is loaded.
2. Keep three tabs ready: SafePaste, `README.md` at **High-level architecture**, and `results/report_tables.md` at **AI4Privacy Frozen Evaluation**. Keep the three fictional inputs below ready to copy. Hide notifications and any `.env` or token.
3. Check the screen capture, face camera and microphone with a short trial. The final video should stay below eight minutes.

## 0:00–0:40 — Problem and value

**Screen:** SafePaste page, with face visible.

**Say:**

> Hi, I'm Fang Xinyi. This is SafePaste, a local privacy review tool for Tonya, an e-commerce support agent. Before she pastes a customer message into a public AI assistant, SafePaste checks it for personal information and offers a sanitised version to copy. It adds a visible review step at the point where a rushed user might miss a name, phone number or address. It reduces risk, but it cannot guarantee that every sensitive detail is found.

## 0:40–1:25 — What you built and why

**Screen:** README architecture diagram.

**Say:**

> The input is one English support message. Presidio finds structured identifiers, with extra patterns for Singapore forms, while a locally stored GLiNER model finds contextual entities such as names and addresses. My pipeline merges overlapping results, masks them with typed placeholders, and gives uncertain model detections a POSSIBLE PII placeholder. The user can review and restore the text. I reused pretrained components and calibrated thresholds; I did not fine-tune the model. Detection runs locally, so it does not send the message to a cloud LLM. RAG and agents would not help this span detection task.

## 1:25–3:45 — Three live cases

Use the SafePaste page for all three. Replace the left-hand input with each text, click **Check and mask**, and point to the sanitised text and detected-spans list. Do not read the full input aloud; let viewers scan it while you explain one finding. These examples were checked locally with the current Hybrid demo mode. Model output can vary, so describe what actually appears on your screen.

### Case 1 — Mixed PII in informal Singapore support text (about 50 seconds)

**Paste:**

```text
Hi, I am Aisha Rahman. My parcel still not here leh, and the courier said the address maybe incomplete. Can help check ah? It should go to Blk 456 Tampines Street 42, #08-21, Singapore 520456. If the rider cannot find the block, please ask them to call +65 8765 4321. I also sent an email from aisha.rahman@example.com yesterday, but I have not received a reply. Please confirm whether the delivery can be arranged again tomorrow.
```

**Observed locally:** Name and full address were masked by GLiNER; phone and email by Presidio. All four appeared as typed placeholders.

**Say:**

> This fictional customer message uses informal Singapore phrasing and contains four kinds of personal information. The contextual model detects the name and address; Presidio catches the structured phone number and email. The right side is the version Tonya could review and copy, while the list below shows what was changed and which detector found it.

### Case 2 — Partial address masking (about 50 seconds)

**Paste:**

```text
Hi support team, my name is Mei Tan. I ordered a blue jacket last week, but the tracking page still says it is being prepared. Could you check whether the parcel has left the warehouse? Please send any update to mei.tan@example.com or call me at +65 9123 4567. If delivery is attempted again, the address is Blk 123 Ang Mo Kio Ave 3, #12-34, Singapore 560123. I plan to paste your reply into an AI assistant to make it shorter.
```

**Observed locally:** The name, email, phone, unit number and postcode were masked; the street/block portion remained visible. GLiNER also labelled “support team” as an organisation. Do **not** copy this result to a public assistant: it demonstrates that review is necessary.

**Say:**

> The second message shows a real limitation of this prototype. It catches the obvious identifiers and parts of the address, but leaves the block and street visible. It also treats “support team” as an organisation. Tonya should not trust this output as safe to send. The case explains why our overlap metric can overstate protection: touching one part of an address does not mean the whole address was hidden.

### Case 3 — False positives and uncertain masking (about 40 seconds)

**Paste:**

```text
Hello support team, I ordered a blue jacket and received the wrong size. The item is still sealed and the return label has not been used. Could you explain the exchange process, whether I need to include the packaging, and how long a replacement usually takes? I want to summarise your instructions in an AI assistant before replying to the customer. Please keep the answer brief and avoid adding a delivery date until the warehouse confirms one.
```

**Observed locally:** The model masked “support team” as `ORGANIZATION`, “customer” as `PERSON`, and “warehouse” as `[POSSIBLE_PII]`. These are ordinary words in this context. Click **Restore all** to show that the text can be recovered; explain that this button restores *all* masks, so the user must inspect the result before copying.

**Say:**

> This message contains no intended customer PII, yet the model over-masks several ordinary words. “Warehouse” appears as POSSIBLE PII because the model is uncertain. This is why we also measure precision and abstention, not only recall. I can restore the text, but Restore all reverses every mask; it is a review aid, not an automatic safety decision.

## 3:45–5:20 — Evaluation and results

**Screen:** `results/report_tables.md`, first the AI4Privacy table, then the Singapore stress table. Zoom so numbers are readable.

**Say:**

> I used 2,000 development examples to choose rules, label mapping and GLiNER thresholds. I then froze the configuration and compared Presidio-only, GLiNER-only and Hybrid on the same 3,000 AI4Privacy examples. The original target was 80 percent exact-span recall and better performance than the rule baseline. On this broad frozen benchmark, Hybrid reached 26.98 percent exact typed recall and 47.44 percent overlap protective recall. It improved on both single detectors, but it missed the 80 percent target. Its exact typed precision was only 38.41 percent, so more coverage also meant more false alarms.

> The separate set of 30 fictional Singapore-style messages gave Hybrid 92.45 percent exact typed recall and 96.23 percent overlap protective recall. That is encouraging for Tonya's scenario, but the set is small and hand-authored. I would not present it as real-world accuracy.

## 5:20–6:20 — Critique and course decisions

**Screen:** `results/report_tables.md` per-label results, then README architecture or limitations.

**Say:**

> I report exact and overlap recall because a boundary mismatch can still show that a detector noticed the region. However, any overlap does not prove every sensitive character was hidden. I also report typed and protective recall separately so POSSIBLE PII masks cannot silently inflate the main score. The broad benchmark exposed serious gaps: government IDs were not covered in that label space, and address boundaries were weak. The local architecture avoids external per-call API fees, but model loading and review time still have costs. My next steps would be broader ID recognisers, better address handling and a larger independent support-text evaluation.

## 6:20–6:40 — Close

**Screen:** SafePaste page with the case 3 review result and face visible.

**Say:**

> SafePaste is a working local checkpoint before sharing text with a public assistant. The hybrid design improved coverage, and the evaluation shows both its value and its current limits. Thank you.

## Recording notes

- Keep the face visible throughout, as requested by the instructor.
- Show the browser and existing repository files; no presentation slides are required.
- Use the actual output on screen. If a live detection differs, describe what happened rather than claiming a specific placeholder appeared.
- Avoid describing the 30-example result as overall accuracy or a production guarantee.
