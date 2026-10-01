from __future__ import annotations

import re
from dataclasses import dataclass

from .types import Span


PRESIDIO_LABEL_MAP = {
    "CREDIT_CARD": "FINANCIAL",
    "EMAIL_ADDRESS": "EMAIL",
    "IBAN_CODE": "FINANCIAL",
    "IP_ADDRESS": "IP_ADDRESS",
    "PHONE_NUMBER": "PHONE",
    "SG_NRIC": "GOVERNMENT_ID",
    "SG_PHONE": "PHONE",
    "POSTAL_CODE": "ADDRESS",
    "UNIT_NUMBER": "ADDRESS",
}

PRESIDIO_ENTITIES = tuple(PRESIDIO_LABEL_MAP)

PHONE_CONTEXT_RE = re.compile(r"\b(call|called|phone|mobile|tel|contact|whatsapp|sms|ring)\b", re.I)
POSTAL_CONTEXT_RE = re.compile(
    r"\b(singapore|sg|blk|block|street|st|road|rd|avenue|ave|lane|drive|dr|lorong|crescent|close|walk|#\d{1,3}-\d{1,4})\b",
    re.I,
)


@dataclass(frozen=True)
class CustomPattern:
    entity: str
    name: str
    regex: str
    score: float
    context: tuple[str, ...] = ()


CUSTOM_PATTERNS = (
    CustomPattern("SG_NRIC", "SafePasteSingaporeNricRecognizer", r"(?<![A-Z0-9])[STFGM]\d{7}[A-Z](?![A-Z0-9])", 0.96),
    CustomPattern("SG_PHONE", "SafePasteSingaporePhoneRecognizer", r"(?<!\d)(?:\+65[\s-]?)?[3689]\d{3}[\s-]?\d{4}(?!\d)", 0.94),
    CustomPattern("UNIT_NUMBER", "SafePasteSingaporeUnitRecognizer", r"(?<!\w)#\d{1,3}-\d{1,4}(?!\d)", 0.93),
    CustomPattern("POSTAL_CODE", "SafePasteSingaporePostalCodeRecognizer", r"(?<!\d)\d{6}(?!\d)", 0.70),
)


class PresidioDetector:
    name = "presidio"

    def __init__(self) -> None:
        self._analyzer = None

    def _load(self):
        if self._analyzer is not None:
            return self._analyzer
        try:
            from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer, RecognizerRegistry
            from presidio_analyzer.nlp_engine import NoOpNlpEngine
        except ImportError as exc:
            raise RuntimeError("Install presidio-analyzer to use Presidio detection") from exc

        nlp_engine = NoOpNlpEngine(models=[{"lang_code": "en", "model_name": "no_op"}])
        registry = RecognizerRegistry()
        registry.load_predefined_recognizers(languages=["en"], nlp_engine=nlp_engine)
        for item in CUSTOM_PATTERNS:
            registry.add_recognizer(
                PatternRecognizer(
                    supported_entity=item.entity,
                    name=item.name,
                    supported_language="en",
                    patterns=[Pattern(item.name, item.regex, item.score)],
                    context=list(item.context),
                )
            )
        self._analyzer = AnalyzerEngine(registry=registry, nlp_engine=nlp_engine, supported_languages=["en"])
        return self._analyzer

    def detect(self, text: str) -> list[Span]:
        raw_results = self._load().analyze(text=text, language="en", entities=list(PRESIDIO_ENTITIES))
        spans: list[Span] = []
        for result in raw_results:
            entity = str(result.entity_type)
            if entity not in PRESIDIO_LABEL_MAP:
                continue
            if not self._passes_local_filters(text, result.start, result.end, entity):
                continue
            metadata = getattr(result, "recognition_metadata", None) or {}
            recognizer_name = metadata.get("recognizer_name")
            spans.append(
                Span(
                    start=int(result.start),
                    end=int(result.end),
                    label=PRESIDIO_LABEL_MAP[entity],
                    score=float(result.score),
                    source=self.name,
                    recognizer_name=str(recognizer_name) if recognizer_name else None,
                )
            )
        return _remove_contained_duplicates(spans)

    def _passes_local_filters(self, text: str, start: int, end: int, entity: str) -> bool:
        value = text[start:end]
        if entity == "SG_PHONE":
            return _is_plausible_singapore_phone(text, start, end, value)
        if entity == "POSTAL_CODE":
            return bool(_context_window(text, start, end, width=36) and POSTAL_CONTEXT_RE.search(_context_window(text, start, end, width=36)))
        return True


def _is_plausible_singapore_phone(text: str, start: int, end: int, value: str) -> bool:
    if value.startswith("+65"):
        return True
    if "-" in value or " " in value:
        return True
    prefix = text[max(0, start - 24) : start]
    same_sentence_prefix = re.split(r"[.!?\n]", prefix)[-1]
    return bool(PHONE_CONTEXT_RE.search(same_sentence_prefix))


def _context_window(text: str, start: int, end: int, width: int) -> str:
    return text[max(0, start - width) : min(len(text), end + width)]


def _remove_contained_duplicates(spans: list[Span]) -> list[Span]:
    ranked = sorted(spans, key=lambda s: (-s.score, -(s.end - s.start), s.start, s.label))
    kept: list[Span] = []
    for candidate in ranked:
        if any(candidate.start >= item.start and candidate.end <= item.end for item in kept):
            continue
        kept.append(candidate)
    return sorted(kept, key=lambda s: (s.start, s.end, s.label))
