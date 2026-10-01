"""Build the SafePaste label mapping from the development split labels."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

try:
    from audit_dataset import label_counts, load_records
except ModuleNotFoundError:
    from scripts.audit_dataset import label_counts, load_records


MAPPING_VERSION = "safepaste-label-mapping-v1"
SUPPORTED_TARGET_LABELS = ["ADDRESS", "EMAIL", "FINANCIAL", "GOVERNMENT_ID", "IP_ADDRESS", "PERSON", "PHONE"]

DEFAULT_LABEL_DECISIONS = {
    "BOD": {
        "target": "EXCLUDED",
        "reason": "Temporal attribute outside the current SafePaste detector scope.",
    },
    "BUILDING": {
        "target": "ADDRESS",
        "reason": "Building numbers are address components.",
    },
    "CITY": {
        "target": "ADDRESS",
        "reason": "Cities are retained as address/location components for this experiment.",
    },
    "COUNTRY": {
        "target": "ADDRESS",
        "reason": "Countries are retained as address/location components for consistent address evaluation.",
    },
    "DATE": {
        "target": "EXCLUDED",
        "reason": "General dates are outside the current SafePaste PII scope.",
    },
    "DRIVERLICENSE": {
        "target": "GOVERNMENT_ID",
        "reason": "Driver license values are government-issued identifiers.",
    },
    "EMAIL": {
        "target": "EMAIL",
        "reason": "Direct email address PII.",
    },
    "GEOCOORD": {
        "target": "ADDRESS",
        "reason": "Geographic coordinates can reveal precise location.",
    },
    "GIVENNAME1": {
        "target": "PERSON",
        "reason": "Given names are person-name components.",
    },
    "GIVENNAME2": {
        "target": "PERSON",
        "reason": "Given names are person-name components.",
    },
    "IDCARD": {
        "target": "GOVERNMENT_ID",
        "reason": "ID card values are government-issued identifiers.",
    },
    "IP": {
        "target": "IP_ADDRESS",
        "reason": "IP addresses are structured network identifiers.",
    },
    "LASTNAME1": {
        "target": "PERSON",
        "reason": "Last names are person-name components.",
    },
    "LASTNAME2": {
        "target": "PERSON",
        "reason": "Last names are person-name components.",
    },
    "LASTNAME3": {
        "target": "PERSON",
        "reason": "Last names are person-name components.",
    },
    "PASS": {
        "target": "EXCLUDED",
        "reason": "Passwords are credentials; this project reports that credentials are outside the PII detector scope.",
    },
    "PASSPORT": {
        "target": "GOVERNMENT_ID",
        "reason": "Passport values are government-issued identifiers.",
    },
    "POSTCODE": {
        "target": "ADDRESS",
        "reason": "Postal codes are address components.",
    },
    "SECADDRESS": {
        "target": "ADDRESS",
        "reason": "Secondary address fields are address components.",
    },
    "SEX": {
        "target": "EXCLUDED",
        "reason": "Demographic attributes are outside the current direct-PII detector scope.",
    },
    "SOCIALNUMBER": {
        "target": "GOVERNMENT_ID",
        "reason": "Social number values are government-issued identifiers.",
    },
    "STATE": {
        "target": "ADDRESS",
        "reason": "States are retained as address/location components for this experiment.",
    },
    "STREET": {
        "target": "ADDRESS",
        "reason": "Street names are address components.",
    },
    "TEL": {
        "target": "PHONE",
        "reason": "Direct telephone number PII.",
    },
    "TIME": {
        "target": "EXCLUDED",
        "reason": "Standalone times are outside the current SafePaste PII scope.",
    },
    "TITLE": {
        "target": "EXCLUDED",
        "reason": "Honorifics or job titles alone are not treated as PII in this scope.",
    },
    "USERNAME": {
        "target": "EXCLUDED",
        "reason": "Account usernames are outside the current detector scope and are reported as a limitation.",
    },
}


def build_mapping(counts: Counter[str]) -> tuple[dict, list[str]]:
    labels = sorted(counts)
    unmapped = [label for label in labels if label not in DEFAULT_LABEL_DECISIONS]
    entries = {}
    for label in labels:
        if label in DEFAULT_LABEL_DECISIONS:
            decision = DEFAULT_LABEL_DECISIONS[label]
            entries[label] = {
                "target": decision["target"],
                "count": counts[label],
                "reason": decision["reason"],
            }
    excluded_labels = sorted(label for label, entry in entries.items() if entry["target"] == "EXCLUDED")
    mapping = {
        "version": MAPPING_VERSION,
        "generated_date": datetime.now(timezone.utc).date().isoformat(),
        "source_dataset": "development_2000.json",
        "policy": {
            "frozen_evaluation_used": False,
            "invalid_spans": "Exclude invalid gold spans during normalized evaluation and report their counts.",
            "overlapping_gold_spans": "Preserve spans during audit; normalized evaluation must use one-to-one matching.",
        },
        "target_labels": SUPPORTED_TARGET_LABELS,
        "entries": entries,
        "excluded_labels": excluded_labels,
    }
    return mapping, unmapped


def write_unmapped(path: Path, unmapped: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["label"])
        writer.writeheader()
        for label in unmapped:
            writer.writerow({"label": label})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--development", type=Path, default=Path("data/ai4privacy_split/development_2000.json"))
    parser.add_argument("--output", type=Path, default=Path("configs/label_mapping.json"))
    parser.add_argument("--unmapped-output", type=Path, default=Path("artifacts/data_audit/unmapped_labels.csv"))
    args = parser.parse_args()
    records = load_records(args.development)
    mapping, unmapped = build_mapping(label_counts(records))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    write_unmapped(args.unmapped_output, unmapped)
    print(json.dumps({"labels": len(mapping["entries"]), "unmapped": len(unmapped), "output": str(args.output)}, indent=2))
    if unmapped:
        raise SystemExit("Unmapped labels remain; update DEFAULT_LABEL_DECISIONS")


if __name__ == "__main__":
    main()
