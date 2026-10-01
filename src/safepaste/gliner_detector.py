from __future__ import annotations

import os
from pathlib import Path

from .types import Span


LABEL_MAP = {
    "person": "PERSON",
    "address": "ADDRESS",
    "location": "LOCATION",
    "organization": "ORGANIZATION",
}


class GLiNERDetector:
    name = "gliner"

    def __init__(
        self,
        model_path: str | None = None,
        typed_threshold: float = 0.55,
        abstain_threshold: float = 0.35,
        local_files_only: bool = True,
    ):
        self.model_path = model_path or os.getenv("SAFEPASTE_GLINER_MODEL", "")
        self.typed_threshold = typed_threshold
        self.abstain_threshold = abstain_threshold
        self.local_files_only = local_files_only
        self._model = None

    @property
    def available(self) -> bool:
        return bool(self.model_path and Path(self.model_path).is_dir())

    def _load(self):
        if not self.available:
            raise RuntimeError("Set SAFEPASTE_GLINER_MODEL to an existing local model directory")
        if self._model is None:
            try:
                from gliner import GLiNER
            except ImportError as exc:
                raise RuntimeError("Install the optional 'gliner' package to use local NER") from exc
            self._model = GLiNER.from_pretrained(self.model_path, local_files_only=self.local_files_only)
        return self._model

    def detect(self, text: str) -> list[Span]:
        model = self._load()
        raw = model.predict_entities(text, list(LABEL_MAP), threshold=self.abstain_threshold)
        spans = []
        for entity in raw:
            score = float(entity["score"])
            spans.append(
                Span(
                    start=int(entity["start"]),
                    end=int(entity["end"]),
                    label=LABEL_MAP.get(str(entity["label"]).lower(), str(entity["label"]).upper()),
                    score=score,
                    source=self.name,
                    abstained=score < self.typed_threshold,
                )
            )
        return spans
