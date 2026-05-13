"""Text extraction with PDF coordinates.

For a digital PDF this is straight `page.get_text("words")`. For a scanned
PDF you'd plug Tesseract or a managed OCR service into the same return
shape and the rest of the pipeline is unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass

import fitz  # PyMuPDF


@dataclass(frozen=True)
class Word:
    page: int
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    char_start: int  # position within the page's reconstructed text
    char_end: int


def extract_words(pdf_path: str) -> tuple[list[Word], dict[int, str]]:
    """Return all words with bboxes plus reconstructed per-page text.

    The reconstructed text is a space-joined concatenation of words in
    reading order. char_start/char_end on each Word point back into the
    corresponding page string so detector matches can be mapped to bboxes.
    """

    words: list[Word] = []
    page_text: dict[int, str] = {}

    with fitz.open(pdf_path) as doc:
        for page_index in range(doc.page_count):
            page = doc.load_page(page_index)
            raw = page.get_text("words")  # [x0, y0, x1, y1, word, b, l, w]
            raw.sort(key=lambda w: (round(w[1], 1), w[0]))

            offset = 0
            chunks: list[str] = []
            for w in raw:
                x0, y0, x1, y1, text = w[0], w[1], w[2], w[3], w[4]
                if not text:
                    continue
                if chunks:
                    chunks.append(" ")
                    offset += 1
                start = offset
                chunks.append(text)
                offset += len(text)
                words.append(
                    Word(
                        page=page_index,
                        text=text,
                        x0=x0,
                        y0=y0,
                        x1=x1,
                        y1=y1,
                        char_start=start,
                        char_end=offset,
                    )
                )
            page_text[page_index] = "".join(chunks)

    return words, page_text


def page_count(pdf_path: str) -> int:
    with fitz.open(pdf_path) as doc:
        return doc.page_count
