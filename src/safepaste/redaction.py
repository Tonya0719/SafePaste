from __future__ import annotations

import re

from .types import Span


TOKEN_RE = re.compile(r"\[(?:POSSIBLE_PII|[A-Z][A-Z0-9_]*)_\d+\]")


def redact(text: str, spans: list[Span]) -> tuple[str, dict[str, str]]:
    result = text
    restore_map: dict[str, str] = {}
    counts: dict[str, int] = {}
    for span in sorted(spans, key=lambda s: s.start, reverse=True):
        base = "POSSIBLE_PII" if span.abstained else span.label
        counts[base] = counts.get(base, 0) + 1
        token = f"[{base}_{counts[base]}]"
        restore_map[token] = text[span.start : span.end]
        result = result[: span.start] + token + result[span.end :]
    return result, restore_map


def restore(redacted_text: str, restore_map: dict[str, str], selected: list[str] | None = None) -> str:
    allowed = set(selected) if selected is not None else set(restore_map)

    def replace(match: re.Match[str]) -> str:
        token = match.group(0)
        return restore_map.get(token, token) if token in allowed else token

    return TOKEN_RE.sub(replace, redacted_text)

