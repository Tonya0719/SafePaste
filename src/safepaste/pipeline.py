from __future__ import annotations

from .gliner_detector import GLiNERDetector
from .presidio_detector import PresidioDetector
from .redaction import redact
from .regex_detector import RegexDetector
from .types import Span


class SafePastePipeline:
    def __init__(self, mode: str = "hybrid", gliner: GLiNERDetector | None = None):
        if mode not in {"presidio", "regex", "regex-legacy", "gliner", "hybrid"}:
            raise ValueError("mode must be presidio, regex, regex-legacy, gliner, or hybrid")
        self.mode = mode
        self.presidio = PresidioDetector()
        self.regex_legacy = RegexDetector()
        self.gliner = gliner or GLiNERDetector()

    def detect(self, text: str) -> tuple[list[Span], list[str]]:
        warnings: list[str] = []
        spans: list[Span] = []
        if self.mode in {"presidio", "regex", "hybrid"}:
            spans.extend(self.presidio.detect(text))
        if self.mode == "regex-legacy":
            spans.extend(self.regex_legacy.detect(text))
        if self.mode in {"gliner", "hybrid"}:
            try:
                spans.extend(self.gliner.detect(text))
            except RuntimeError as exc:
                if self.mode == "gliner":
                    raise
                warnings.append(f"GLiNER unavailable; regex-only result shown: {exc}")
        return resolve_overlaps(spans), warnings

    def analyze(self, text: str) -> dict:
        spans, warnings = self.detect(text)
        redacted, restore_map = redact(text, spans)
        return {
            "original": text,
            "redacted": redacted,
            "spans": [span.to_dict(text) for span in spans],
            "restore_map": restore_map,
            "warnings": warnings,
            "mode_requested": self.mode,
            "engines_used": sorted({span.source for span in spans}),
        }


def resolve_overlaps(spans: list[Span]) -> list[Span]:
    """Prefer non-abstained, higher-confidence, longer spans, then restore text order."""
    ranked = sorted(spans, key=lambda s: (s.abstained, -s.score, -(s.end - s.start), s.start))
    chosen: list[Span] = []
    for candidate in ranked:
        if any(candidate.start < current.end and current.start < candidate.end for current in chosen):
            continue
        chosen.append(candidate)
    return sorted(chosen, key=lambda s: (s.start, s.end))
