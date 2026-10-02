"""Shared span data structures for detection and evaluation.

Inputs are character offsets and SafePaste labels produced by detectors or loaded
from gold data. Outputs are immutable span objects used by redaction, overlap
resolution and metric code. Offsets use half-open intervals, [start, end).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class Span:
    """A predicted text span from a detector.

    `abstained=True` means the span should be masked as possible PII but should
    not be counted as a typed-label success in evaluation.
    """

    start: int
    end: int
    label: str
    score: float
    source: str
    abstained: bool = False
    recognizer_name: str | None = None

    def __post_init__(self) -> None:
        if self.start < 0 or self.end <= self.start:
            raise ValueError(f"Invalid span [{self.start}, {self.end})")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be between 0 and 1")

    def to_dict(self, text: str | None = None) -> dict:
        value = asdict(self)
        if text is not None:
            value["text"] = text[self.start : self.end]
        return value


@dataclass(frozen=True, slots=True)
class GoldSpan:
    """A normalized gold span used by the evaluator after label mapping."""

    start: int
    end: int
    label: str
