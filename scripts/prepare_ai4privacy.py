"""Create the milestone's deterministic 2,000/3,000 English split."""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


def is_english(row: dict) -> bool:
    value = str(row.get("language", row.get("lang", ""))).lower()
    return value in {"en", "eng", "english"}


def normalize(row: dict) -> dict:
    text = row.get("source_text") or row.get("text") or row.get("unmasked_text")
    raw_spans = row.get("privacy_mask") or row.get("spans") or []
    if not isinstance(text, str) or not isinstance(raw_spans, list):
        raise ValueError("Unexpected AI4Privacy schema; inspect the dataset card and update normalize()")
    spans = []
    for item in raw_spans:
        spans.append({
            "start": int(item["start"]),
            "end": int(item["end"]),
            "label": str(item.get("label", item.get("type", "PII"))).upper(),
        })
    return {"text": text, "spans": spans}


def reservoir(rows, count: int, rng: random.Random) -> list[dict]:
    sample = []
    seen = 0
    for row in rows:
        if not is_english(row):
            continue
        try:
            item = normalize(row)
        except (KeyError, TypeError, ValueError):
            continue
        if not item["spans"]:
            continue
        seen += 1
        if len(sample) < count:
            sample.append(item)
        else:
            index = rng.randrange(seen)
            if index < count:
                sample[index] = item
    if len(sample) != count:
        raise RuntimeError(f"Only found {len(sample)} usable English records; expected {count}")
    return sample


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=6201)
    parser.add_argument("--split", default="train")
    args = parser.parse_args()
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise SystemExit("Install the data extra: python -m pip install -e '.[data]'") from exc
    rows = load_dataset("ai4privacy/pii-masking-300k", split=args.split, streaming=True)
    sample = reservoir(rows, 5000, random.Random(args.seed))
    rng = random.Random(args.seed)
    rng.shuffle(sample)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "development_2000.json").write_text(json.dumps(sample[:2000], ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output / "frozen_evaluation_3000.json").write_text(json.dumps(sample[2000:], ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {"dataset": "ai4privacy/pii-masking-300k", "seed": args.seed, "development": 2000, "frozen_evaluation": 3000}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

