"""PHI/PII detection over text spans extracted from a PDF.

v1 uses tuned regex patterns covering the core HIPAA Safe Harbor identifiers
that show up in clinical and legal intake documents. The detector returns
candidate spans which are later mapped to PDF bounding boxes by the OCR layer.

The detector is intentionally pluggable: a future v2 can swap in Presidio,
spaCy NER, or an LLM pass behind the same `detect(text)` signature.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Match:
    entity_type: str
    start: int
    end: int
    text: str
    confidence: float


_PATTERNS: list[tuple[str, re.Pattern[str], float]] = [
    (
        "US_SSN",
        re.compile(r"\b(?!000|666|9\d{2})\d{3}[- ]?(?!00)\d{2}[- ]?(?!0000)\d{4}\b"),
        0.98,
    ),
    (
        "EMAIL",
        re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
        0.99,
    ),
    (
        "PHONE",
        re.compile(
            r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
        ),
        0.9,
    ),
    (
        "DATE",
        re.compile(
            r"\b(?:0?[1-9]|1[0-2])[/-](?:0?[1-9]|[12]\d|3[01])[/-](?:19|20)\d{2}\b"
        ),
        0.95,
    ),
    (
        "DATE",
        re.compile(
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+(?:19|20)\d{2}\b",
            re.IGNORECASE,
        ),
        0.92,
    ),
    (
        "MRN",
        re.compile(r"\bMRN[:#\s]*([A-Z0-9-]{4,16})\b", re.IGNORECASE),
        0.95,
    ),
    (
        "ZIP",
        re.compile(r"\b\d{5}(?:-\d{4})?\b"),
        0.7,
    ),
    (
        "URL",
        re.compile(r"\bhttps?://\S+\b"),
        0.95,
    ),
    (
        "CREDIT_CARD",
        re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
        0.6,
    ),
]


def _is_overlap(a: Match, b: Match) -> bool:
    return not (a.end <= b.start or b.end <= a.start)


def detect(text: str) -> list[Match]:
    """Return non-overlapping PHI matches, preferring higher-confidence types."""

    raw: list[Match] = []
    for entity_type, pattern, conf in _PATTERNS:
        for m in pattern.finditer(text):
            raw.append(
                Match(
                    entity_type=entity_type,
                    start=m.start(),
                    end=m.end(),
                    text=m.group(0),
                    confidence=conf,
                )
            )

    # Resolve overlaps: prefer higher confidence, then longer span.
    raw.sort(key=lambda m: (-m.confidence, -(m.end - m.start)))
    kept: list[Match] = []
    for m in raw:
        if any(_is_overlap(m, k) for k in kept):
            continue
        kept.append(m)

    kept.sort(key=lambda m: m.start)
    return kept
