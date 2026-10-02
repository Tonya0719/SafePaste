"""Command-line interface for local SafePaste analysis and quick evaluation.

The CLI accepts either a text string for one-off analysis or a JSON dataset for
evaluation. It is a thin wrapper around `SafePastePipeline` and the evaluator,
intended for reproducible local commands rather than a hosted service.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .evaluation import evaluate_records
from .pipeline import SafePastePipeline


MODES = ["presidio", "regex", "regex-legacy", "gliner", "hybrid"]


def main() -> None:
    parser = argparse.ArgumentParser(prog="safepaste")
    sub = parser.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze")
    analyze.add_argument("text")
    analyze.add_argument("--mode", choices=MODES, default="hybrid")
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("dataset", type=Path)
    evaluate.add_argument("--mode", choices=MODES, default="hybrid")
    args = parser.parse_args()
    pipeline = SafePastePipeline(args.mode)
    if args.command == "analyze":
        print(json.dumps(pipeline.analyze(args.text), indent=2, ensure_ascii=False))
    else:
        records = json.loads(args.dataset.read_text(encoding="utf-8"))
        metrics = evaluate_records(records, lambda text: pipeline.detect(text)[0])
        print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
