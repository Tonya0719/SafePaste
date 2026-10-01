from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class Span:
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
    start: int
    end: int
    label: str
