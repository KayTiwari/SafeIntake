# Architecture

```
              ┌───────────────────────┐
              │  React SPA (Vite)     │
              │  upload · review UI   │
              └──────────┬────────────┘
                         │ /api/*
              ┌──────────▼────────────┐
              │  Flask REST API       │
              │  (Gunicorn in prod)   │
              └──┬──────────┬─────────┘
                 │          │
                 │          │
   ┌─────────────▼──┐    ┌──▼────────────────┐
   │  Pipeline      │    │  SQLAlchemy ORM   │
   │  OCR -> detect │    │  documents        │
   │  -> redact     │    │  entities         │
   │  (PyMuPDF)     │    │  audit_events     │
   └────────────────┘    └───────────────────┘
                                  │
                         ┌────────▼────────┐
                         │ SQLite (dev)    │
                         │ Postgres (prod) │
                         └─────────────────┘
```

## Lifecycle of a document

1. **Upload** — `POST /api/documents` stores the PDF on disk, creates a `Document`
   row, and writes an `upload` audit event.
2. **Analyze** — `app/services/pipeline.py` extracts words + bboxes from each
   page (`ocr.py`), runs regex-based PHI detection (`detector.py`), then maps
   matches back to PDF coordinates. Each match becomes an `Entity` row in state
   `pending`. An `analyze_complete` audit event is written.
3. **Review** — A human reviewer opens the document in the UI, approves or
   rejects each detection. Every state transition writes an `entity_review`
   audit event with the actor, the entity type, and the state change.
4. **Redact** — `POST /api/documents/:id/redact` calls `redactor.py`, which uses
   PyMuPDF's `add_redact_annot` + `apply_redactions` to permanently strip the
   underlying content (not just paint over it). The output is saved to disk and
   served by `GET /api/documents/:id/redacted`. A `redact` audit event is written
   with the count of applied redactions.

## Why these choices

- **PyMuPDF for redaction**: real content-stream removal, not a visual overlay.
  Output PDFs cannot be un-redacted by copy/paste or text extraction.
- **Bbox-bound entities**: each detection carries its page + bounding box, so
  the reviewer's approve/reject choices map deterministically to what gets
  removed from the file.
- **Append-only audit log**: every state-changing action writes a row to
  `audit_events` with actor, action, and detail. Nothing is ever deleted from
  this table; document deletion cascades but the events still describe what
  happened.
- **Pluggable detector**: the `detect(text) -> list[Match]` boundary makes it
  trivial to swap in Presidio, spaCy NER, or an LLM pass without touching the
  pipeline glue or storage layer.

## What's deliberately out of scope (v1)

- Authentication and per-user permissions. The `X-Actor` header is honored on
  write actions so a reverse proxy can stamp identity, but there is no login
  flow.
- Async job processing. Analysis runs inline on upload. For large PDFs or
  batches this should move to Celery/RQ with Redis as the broker.
- Scanned-PDF OCR. The `ocr.py` layer is shaped to accept any word-with-bbox
  source, but only the embedded-text path is implemented.
- LLM enrichment. The detector is regex-only; a v2 pass would resolve
  free-text spans (clinical notes, addresses, names in narrative) where regex
  alone is brittle.
