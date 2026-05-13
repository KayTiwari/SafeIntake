"""Apply approved entity bboxes as true PDF redactions.

PyMuPDF's add_redact_annot + apply_redactions removes the underlying
content stream, not just an overlay, so the redacted text is not
recoverable from the output file.
"""

from __future__ import annotations

from collections.abc import Iterable

import fitz


def redact(source_pdf: str, output_pdf: str, boxes: Iterable[dict]) -> None:
    """boxes: iterable of {page, x0, y0, x1, y1, entity_type}."""

    by_page: dict[int, list[dict]] = {}
    for b in boxes:
        by_page.setdefault(int(b["page"]), []).append(b)

    with fitz.open(source_pdf) as doc:
        for page_index in range(doc.page_count):
            page = doc.load_page(page_index)
            for b in by_page.get(page_index, []):
                rect = fitz.Rect(b["x0"], b["y0"], b["x1"], b["y1"])
                page.add_redact_annot(
                    rect,
                    fill=(0, 0, 0),
                    text=f"[{b.get('entity_type', 'REDACTED')}]",
                    fontsize=8,
                    align=fitz.TEXT_ALIGN_CENTER,
                )
            page.apply_redactions()
        doc.save(output_pdf, garbage=4, deflate=True, clean=True)
