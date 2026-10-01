from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.audit_dataset import audit, sha256_file, validate_records
from scripts.build_label_mapping import build_mapping
from scripts.export_report_tables import run as export_report_tables
from scripts.run_experiment import run_experiment
from scripts.tune_thresholds import predictions_for_thresholds, run_sweep
from safepaste.evaluation import evaluate_predictions, evaluate_records, gold_spans_from_record, score
from safepaste.gliner_detector import GLiNERDetector
from safepaste.pipeline import SafePastePipeline, resolve_overlaps
from safepaste.presidio_detector import PresidioDetector
from safepaste.redaction import redact, restore
from safepaste.regex_detector import RegexDetector
from safepaste.types import GoldSpan, Span


ROOT = Path(__file__).parents[1]


class SafePasteTests(unittest.TestCase):
    def test_gliner_model_path_is_loaded_from_dotenv(self):
        expected = os.getenv("SAFEPASTE_GLINER_MODEL", "")
        self.assertEqual(GLiNERDetector().model_path, expected)

    def test_gliner_loads_local_files_only_once(self):
        class FakeModel:
            def predict_entities(self, text, labels, threshold):
                return [{"start": 9, "end": 16, "label": "person", "score": 0.6}]

        with tempfile.TemporaryDirectory() as tmp, patch("gliner.GLiNER.from_pretrained", return_value=FakeModel()) as loader:
            detector = GLiNERDetector(model_path=tmp)
            first = detector.detect("Customer Mei Tan called.")
            second = detector.detect("Customer Mei Tan called.")
            self.assertEqual(loader.call_count, 1)
            self.assertEqual(loader.call_args.kwargs["local_files_only"], True)
            self.assertEqual(first[0].label, "PERSON")
            self.assertEqual(second[0].source, "gliner")

    def test_gliner_marks_low_confidence_as_abstained(self):
        class FakeModel:
            def predict_entities(self, text, labels, threshold):
                return [{"start": 9, "end": 16, "label": "person", "score": 0.4}]

        with tempfile.TemporaryDirectory() as tmp, patch("gliner.GLiNER.from_pretrained", return_value=FakeModel()):
            spans = GLiNERDetector(model_path=tmp, typed_threshold=0.55, abstain_threshold=0.35).detect("Customer Mei Tan called.")
            self.assertTrue(spans[0].abstained)

    def test_regex_detects_local_identifiers(self):
        text = "Email mei@example.com. Call +65 9123 4567, NRIC S1234567D."
        labels = {item.label for item in RegexDetector().detect(text)}
        self.assertTrue({"EMAIL", "PHONE", "SG_NRIC"}.issubset(labels))

    def test_presidio_detects_structured_identifiers(self):
        text = "Email mei@example.com. Call +65 9123 4567, NRIC S1234567D, unit #12-34 Singapore 560123."
        spans = PresidioDetector().detect(text)
        labels = {item.label for item in spans}
        recognizers = {item.recognizer_name for item in spans}
        self.assertTrue({"EMAIL", "PHONE", "GOVERNMENT_ID", "ADDRESS"}.issubset(labels))
        self.assertTrue(
            {
                "SafePasteSingaporeNricRecognizer",
                "SafePasteSingaporeUnitRecognizer",
                "SafePasteSingaporePostalCodeRecognizer",
            }.issubset(recognizers)
        )
        self.assertEqual({item.source for item in spans}, {"presidio"})
        self.assertTrue(all(item.recognizer_name for item in spans))

    def test_presidio_accepts_contextual_local_phone(self):
        spans = PresidioDetector().detect("Please call 91234567 today.")
        self.assertIn("PHONE", {item.label for item in spans})

    def test_presidio_rejects_plain_order_number_as_phone(self):
        spans = PresidioDetector().detect("Order 91234567 is ready for pickup.")
        self.assertFalse(spans)

    def test_presidio_phone_context_does_not_leak_across_sentences(self):
        text = "Call 91234567. Order 81234567 is ready."
        spans = PresidioDetector().detect(text)
        phones = [item for item in spans if item.label == "PHONE"]
        self.assertEqual([text[item.start : item.end] for item in phones], ["91234567"])

    def test_regex_mode_is_presidio_compatibility_alias(self):
        result = SafePastePipeline("regex").analyze("Email mei@example.com")
        self.assertEqual(result["engines_used"], ["presidio"])

    def test_presidio_mode_is_explicit_baseline(self):
        result = SafePastePipeline("presidio").analyze("Email mei@example.com")
        self.assertEqual(result["engines_used"], ["presidio"])

    def test_legacy_regex_mode_remains_available_for_debugging(self):
        result = SafePastePipeline("regex-legacy").analyze("Email mei@example.com")
        self.assertEqual(result["engines_used"], ["regex"])

    def test_redaction_round_trip(self):
        text = "Call 91234567."
        spans = RegexDetector().detect(text)
        masked, mapping = redact(text, spans)
        self.assertNotIn("91234567", masked)
        self.assertEqual(restore(masked, mapping), text)

    def test_overlap_resolution_prefers_typed(self):
        spans = [Span(0, 5, "PERSON", .40, "gliner", True), Span(0, 4, "EMAIL", .90, "regex")]
        self.assertEqual(resolve_overlaps(spans)[0].label, "EMAIL")

    def test_abstention_changes_protective_recall(self):
        predictions = [Span(0, 4, "PERSON", .4, "gliner", True)]
        gold = [GoldSpan(0, 4, "PERSON")]
        self.assertEqual(score(predictions, gold, boundary="exact", include_abstained=False).recall, 0)
        self.assertEqual(score(predictions, gold, boundary="exact", include_abstained=True).recall, 1)

    def test_evaluate_records_typed_metrics_require_correct_label(self):
        records = [{"text": "Mei", "spans": [{"start": 0, "end": 3, "label": "PERSON"}]}]
        metrics = evaluate_records(records, lambda text: [Span(0, 3, "ADDRESS", 0.9, "test")])
        self.assertEqual(metrics["exact_typed_recall"], 0)
        self.assertEqual(metrics["exact_protective_recall"], 1)

    def test_gold_spans_use_label_mapping_and_skip_exclusions(self):
        mapping = {
            "target_labels": ["PERSON"],
            "entries": {
                "GIVENNAME1": {"target": "PERSON"},
                "TIME": {"target": "EXCLUDED"},
            }
        }
        record = {
            "text": "Mei 10am",
            "spans": [
                {"start": 0, "end": 3, "label": "GIVENNAME1"},
                {"start": 4, "end": 8, "label": "TIME"},
                {"start": 10, "end": 15, "label": "GIVENNAME1"},
            ],
        }
        gold, skipped = gold_spans_from_record(record, mapping)
        self.assertEqual(gold, [GoldSpan(0, 3, "PERSON")])
        self.assertEqual(skipped["excluded_gold_spans"], 1)
        self.assertEqual(skipped["invalid_gold_spans"], 1)

    def test_gold_spans_accept_target_labels_and_local_aliases(self):
        mapping = {"target_labels": ["PERSON", "ADDRESS", "GOVERNMENT_ID"], "entries": {}}
        record = {
            "text": "Mei S1234567D #12-34",
            "spans": [
                {"start": 0, "end": 3, "label": "PERSON"},
                {"start": 4, "end": 13, "label": "SG_NRIC"},
                {"start": 14, "end": 20, "label": "UNIT_NUMBER"},
            ],
        }
        gold, skipped = gold_spans_from_record(record, mapping)
        self.assertEqual([item.label for item in gold], ["PERSON", "GOVERNMENT_ID", "ADDRESS"])
        self.assertEqual(skipped["unmapped_gold_spans"], 0)

    def test_evaluate_predictions_reports_mapped_gold_counts(self):
        mapping = {"entries": {"GIVENNAME1": {"target": "PERSON"}, "TIME": {"target": "EXCLUDED"}}}
        records = [{"text": "Mei 10am", "spans": [{"start": 0, "end": 3, "label": "GIVENNAME1"}, {"start": 4, "end": 8, "label": "TIME"}]}]
        metrics = evaluate_predictions(records, [[Span(0, 3, "PERSON", 0.9, "test")]], mapping)
        self.assertEqual(metrics["gold_spans"], 1)
        self.assertEqual(metrics["excluded_gold_spans"], 1)
        self.assertEqual(metrics["exact_typed_recall"], 1)

    def test_stress_set_has_valid_spans(self):
        records = json.loads((ROOT / "data" / "singapore_stress.json").read_text(encoding="utf-8"))
        self.assertEqual(len(records), 30)
        for record in records:
            for span in record["spans"]:
                self.assertLess(span["start"], span["end"])
                self.assertTrue(record["text"][span["start"]:span["end"]])

    def test_hybrid_degrades_transparently(self):
        unavailable_gliner = GLiNERDetector(model_path=str(ROOT / "models" / "missing"))
        result = SafePastePipeline("hybrid", gliner=unavailable_gliner).analyze("Call 91234567")
        self.assertTrue(result["warnings"])
        self.assertIn("presidio", result["engines_used"])

    def test_dataset_audit_detects_span_problems(self):
        records = [
            {
                "text": "abc def",
                "spans": [
                    {"start": 0, "end": 3, "label": "A"},
                    {"start": 0, "end": 3, "label": "A"},
                    {"start": 2, "end": 6, "label": "B"},
                    {"start": 9, "end": 10, "label": "C"},
                ],
            }
        ]
        issues, relations = validate_records("sample", records)
        self.assertIn("duplicate_span", {item.issue for item in issues})
        self.assertIn("out_of_bounds", {item.issue for item in issues})
        self.assertIn("overlap", {item.relation for item in relations})

    def test_dataset_audit_writes_manifest_and_csvs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = root / "records.json"
            dataset.write_text(
                json.dumps([{"text": "email a@b.co", "spans": [{"start": 6, "end": 12, "label": "EMAIL"}]}]),
                encoding="utf-8",
            )
            output = root / "audit"
            result = audit({"development": dataset}, output)
            self.assertEqual(result["manifest"]["files"]["development"]["sha256"], sha256_file(dataset))
            self.assertTrue((output / "record_summary.csv").exists())
            self.assertTrue((output / "development_label_counts.csv").exists())
            self.assertTrue((output / "data_sha256_manifest.json").exists())

    def test_label_mapping_requires_explicit_decisions(self):
        mapping, unmapped = build_mapping({"EMAIL": 2, "TEL": 1, "UNKNOWN_LABEL": 1})
        self.assertEqual(mapping["entries"]["EMAIL"]["target"], "EMAIL")
        self.assertEqual(mapping["entries"]["TEL"]["target"], "PHONE")
        self.assertEqual(unmapped, ["UNKNOWN_LABEL"])

    def test_label_mapping_covers_development_labels(self):
        records = json.loads((ROOT / "data" / "ai4privacy_split" / "development_2000.json").read_text(encoding="utf-8"))
        labels = {}
        for record in records:
            for span in record["spans"]:
                labels[span["label"]] = labels.get(span["label"], 0) + 1
        mapping, unmapped = build_mapping(labels)
        self.assertFalse(unmapped)
        self.assertIn("PERSON", mapping["target_labels"])
        self.assertIn("ADDRESS", mapping["target_labels"])
        self.assertIn("FINANCIAL", mapping["target_labels"])

    def test_threshold_predictions_filter_and_abstain(self):
        cached = [
            [
                {"start": 0, "end": 3, "label": "PERSON", "score": 0.6, "source": "gliner", "recognizer_name": None},
                {"start": 4, "end": 8, "label": "ADDRESS", "score": 0.3, "source": "gliner", "recognizer_name": None},
            ]
        ]
        predictions = predictions_for_thresholds(cached, typed_threshold=0.55, abstain_threshold=0.35)
        self.assertEqual(len(predictions[0]), 1)
        self.assertFalse(predictions[0][0].abstained)

    def test_threshold_sweep_uses_mapped_gold(self):
        records = [{"text": "Mei", "spans": [{"start": 0, "end": 3, "label": "GIVENNAME1"}]}]
        cached = [[{"start": 0, "end": 3, "label": "PERSON", "score": 0.6, "source": "gliner", "recognizer_name": None}]]
        mapping = {"target_labels": ["PERSON"], "entries": {"GIVENNAME1": {"target": "PERSON"}}}
        rows = run_sweep(records, cached, mapping, [0.55], [0.35])
        self.assertEqual(rows[0]["exact_typed_recall"], 1)
        self.assertEqual(rows[0]["overlap_typed_recall_PERSON"], 1)

    def test_run_experiment_writes_standard_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = root / "dataset.json"
            mapping = root / "mapping.json"
            config = root / "config.json"
            output = root / "run"
            dataset.write_text(
                json.dumps([{"id": "r1", "text": "Email mei@example.com", "spans": [{"start": 6, "end": 21, "label": "EMAIL"}]}]),
                encoding="utf-8",
            )
            mapping.write_text(json.dumps({"target_labels": ["EMAIL"], "entries": {"EMAIL": {"target": "EMAIL"}}}), encoding="utf-8")
            config.write_text(
                json.dumps(
                    {
                        "label_mapping": {"path": str(mapping)},
                        "gliner": {"typed_threshold": 0.55, "abstain_threshold": 0.4, "local_files_only": True},
                    }
                ),
                encoding="utf-8",
            )
            result = run_experiment(dataset, "presidio", config, output, progress_every=0)
            self.assertEqual(result["metrics"]["records"], 1)
            self.assertTrue((output / "config.json").exists())
            self.assertTrue((output / "predictions.jsonl").exists())
            self.assertTrue((output / "metrics.json").exists())
            self.assertTrue((output / "runtime.json").exists())

    def test_export_report_tables_writes_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            results = root / "results"
            results.mkdir()
            header = (
                "dataset,system,records,gold_spans,predicted_spans,exact_typed_recall,"
                "exact_protective_recall,overlap_typed_recall,overlap_protective_recall,"
                "exact_typed_precision,overlap_typed_precision,abstention_rate,mean_ms,p95_ms,errors\n"
            )
            main_row = "AI4Privacy frozen,Hybrid,1,2,3,0.5,0.5,0.75,0.75,0.8,0.9,0.1,12.345,20,0\n"
            stress_row = "Singapore stress,Hybrid,1,2,3,0.5,0.5,0.75,0.75,0.8,0.9,0.1,12.345,20,0\n"
            (results / "main_results.csv").write_text(header + main_row, encoding="utf-8")
            (results / "singapore_stress_results.csv").write_text(header + stress_row, encoding="utf-8")
            (results / "per_label_results.csv").write_text(
                "dataset,system,label,gold_spans,typed_predictions,protective_predictions,"
                "exact_typed_recall,exact_protective_recall,overlap_typed_recall,"
                "overlap_protective_recall,exact_typed_precision,overlap_typed_precision\n"
                "AI4Privacy frozen,Hybrid,PERSON,2,2,2,0.5,0.5,0.75,0.75,0.8,0.9\n"
                "Singapore stress,Hybrid,PHONE,2,2,2,0.5,0.5,0.75,0.75,0.8,0.9\n",
                encoding="utf-8",
            )
            (results / "error_categories.csv").write_text(
                "dataset,system,category,count\n"
                "AI4Privacy frozen,Hybrid,missed_gold,4\n"
                "Singapore stress,Hybrid,false_positive,1\n",
                encoding="utf-8",
            )
            (results / "runtime_summary.json").write_text(
                json.dumps(
                    [
                        {
                            "dataset": "AI4Privacy frozen",
                            "system": "Hybrid",
                            "records": 1,
                            "mean_ms": 12.345,
                            "p95_ms": 20.0,
                            "errors": 0,
                        }
                    ]
                ),
                encoding="utf-8",
            )
            output = root / "report.md"
            export_report_tables(results, output)
            content = output.read_text(encoding="utf-8")
            self.assertIn("## Runtime Summary", content)
            self.assertIn("| Hybrid | 1 | 2 | 3 | 50.00% | 50.00% | 75.00% | 75.00% | 80.00% | 90.00% | 10.00% |", content)
            self.assertIn("| AI4Privacy frozen | Hybrid | missed_gold | 4 |", content)


if __name__ == "__main__":
    unittest.main()
