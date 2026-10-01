from __future__ import annotations

import re
from dataclasses import dataclass

from .types import Span


@dataclass(frozen=True)
class Rule:
    label: str
    pattern: re.Pattern[str]
    score: float


RULES = (
    Rule("EMAIL", re.compile(r"(?<![\w.+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![\w-])", re.I), 0.99),
    Rule("SG_NRIC", re.compile(r"(?<![A-Z0-9])[STFGM]\d{7}[A-Z](?![A-Z0-9])", re.I), 0.96),
    Rule("PHONE", re.compile(r"(?<!\d)(?:\+?65[\s-]?)?[3689]\d{3}[\s-]?\d{4}(?!\d)"), 0.94),
    Rule("CREDIT_CARD", re.compile(r"(?<!\d)(?:\d[ -]*?){13,19}(?!\d)"), 0.90),
    Rule("IP_ADDRESS", re.compile(r"(?<!\d)(?:25[0-5]|2[0-4]\d|1?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}(?!\d)"), 0.95),
    Rule("POSTAL_CODE", re.compile(r"(?i)(?<=Singapore\s)\d{6}\b"), 0.92),
    Rule("UNIT_NUMBER", re.compile(r"(?<!\w)#\d{1,3}-\d{1,4}(?!\d)"), 0.93),
)


class RegexDetector:
    name = "regex"

    def detect(self, text: str) -> list[Span]:
        spans: list[Span] = []
        for rule in RULES:
            for match in rule.pattern.finditer(text):
                spans.append(Span(match.start(), match.end(), rule.label, rule.score, self.name))
        return _remove_contained_duplicates(spans)


def _remove_contained_duplicates(spans: list[Span]) -> list[Span]:
    ranked = sorted(spans, key=lambda s: (-s.score, -(s.end - s.start), s.start))
    kept: list[Span] = []
    for candidate in ranked:
        if any(candidate.start >= item.start and candidate.end <= item.end for item in kept):
            continue
        kept.append(candidate)
    return sorted(kept, key=lambda s: (s.start, s.end))
