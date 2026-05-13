"""Glue: OCR words + detector matches -> Entity rows with bboxes."""

from __future__ import annotations

from dataclasses import dataclass

from .detector import Match, detect
from .ocr import Word, extract_words


@dataclass(frozen=True)
class Detection:
    page: int
    entity_type: str
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    confidence: float


def _bbox_for_match(words_on_page: list[Word], match: Match) -> tuple[float, float, float, float] | None:
    overlapping = [
        w for w in words_on_page
        if not (w.char_end <= match.start or w.char_start >= match.end)
    ]
    if not overlapping:
        return None
    x0 = min(w.x0 for w in overlapping)
    y0 = min(w.y0 for w in overlapping)
    x1 = max(w.x1 for w in overlapping)
    y1 = max(w.y1 for w in overlapping)
    return x0, y0, x1, y1


def analyze(pdf_path: str) -> tuple[list[Detection], int]:
    words, page_text = extract_words(pdf_path)
    page_count = len(page_text)
    by_page: dict[int, list[Word]] = {}
    for w in words:
        by_page.setdefault(w.page, []).append(w)

    detections: list[Detection] = []
    for page, text in page_text.items():
        for m in detect(text):
            bbox = _bbox_for_match(by_page.get(page, []), m)
            if bbox is None:
                continue
            x0, y0, x1, y1 = bbox
            detections.append(
                Detection(
                    page=page,
                    entity_type=m.entity_type,
                    text=m.text,
                    x0=x0,
                    y0=y0,
                    x1=x1,
                    y1=y1,
                    confidence=m.confidence,
                )
            )
    return detections, page_count
