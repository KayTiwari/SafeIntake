# SafeIntake

AI-assisted PHI redaction and document intake for regulated workflows.

> **Demo:** [60-second walkthrough on Loom](https://www.loom.com/) <!-- replace with your Loom URL -->

SafeIntake ingests a PDF (think intake forms, clinical notes, claims paperwork,
discovery exhibits), detects HIPAA/PII identifiers, and presents the matches
in a reviewer UI where a human can approve or skip each detection before
applying permanent PDF redactions. Every action is written to an append-only
audit log.

It is built as a portfolio reference for the kind of work regulated industries
actually need: trustworthy AI-assisted document workflows with a human in the
loop, a real audit story, and a clean full-stack architecture.

## Why this project exists

Industries like healthcare, legal, insurance, and government deal with the same
unglamorous bottleneck: paperwork full of identifiers that legally cannot leave
the building unredacted. Off-the-shelf tools either dump everything to a
third-party API or hide their decisions from the reviewer. SafeIntake takes the
opposite stance: every detection is visible, every approval is logged, and the
redaction itself is a true content-stream removal, not a black rectangle drawn
over text that can still be selected.

## Features

- **PDF intake** with size limits and MIME validation
- **PHI/PII detection** for SSN, MRN, email, phone, dates, ZIP, URL, credit card
- **Bounding-box mapped detections** so each match is anchored to a specific
  region of a specific page
- **Reviewer-in-the-loop UI** for approve/reject per detection
- **True PDF redaction** via PyMuPDF (`apply_redactions`), not an overlay
- **Immutable audit trail** of every action, with actor attribution via the
  `X-Actor` header
- **REST API** that the frontend uses and that integrations can drive directly
- **Docker Compose** for one-command spin-up
- **GitHub Actions CI** running pytest and the Vite build on every push

## Architecture

A diagram and full lifecycle walkthrough live in [docs/architecture.md](docs/architecture.md).

```
React SPA  ──HTTP──>  Flask API  ──>  Pipeline (PyMuPDF OCR + regex detector + redactor)
                          │
                          └──>  SQLAlchemy: documents · entities · audit_events
```

## Quickstart

### Docker (recommended)

```bash
docker compose up --build
```

- Frontend: http://localhost:8080
- API:      http://localhost:5001/api/health

### Local dev

Backend:

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. python wsgi.py            # http://localhost:5001
```

Frontend:

```bash
cd frontend
npm install
npm run dev                            # http://localhost:5173 (proxies /api to :5001)
```

## API

| Method | Path                                | Description                                  |
| ------ | ----------------------------------- | -------------------------------------------- |
| GET    | `/api/health`                       | Liveness check                               |
| GET    | `/api/documents`                    | List documents                               |
| POST   | `/api/documents`                    | Upload + analyze a PDF (multipart `file`)    |
| GET    | `/api/documents/:id`                | Document detail with entity list             |
| GET    | `/api/documents/:id/file`           | Original PDF                                 |
| POST   | `/api/documents/:id/redact`         | Apply approved + pending redactions          |
| GET    | `/api/documents/:id/redacted`       | Redacted PDF                                 |
| DELETE | `/api/documents/:id`                | Delete document, file, and entities          |
| PATCH  | `/api/entities/:id`                 | Set `review_state` to approved/rejected      |
| GET    | `/api/documents/:id/audit`          | Audit events for this document               |

All write endpoints honor an `X-Actor: <name>` request header for audit
attribution. A real deployment would put this behind an auth layer that stamps
the header from a verified session.

## Tests

```bash
cd backend
PYTHONPATH=. .venv/bin/pytest -q
```

The suite covers:

- Detector behavior across the supported PHI types
- Overlap resolution between conflicting patterns
- End-to-end upload, analyze, review, and redact through the HTTP API
- Audit log writes for each lifecycle step

## Roadmap

- v2 detector: Presidio + spaCy NER for narrative fields (names, addresses)
- LLM enrichment for clinical notes where regex is brittle
- Auth + per-user permissions, signed audit log export
- Async pipeline (Celery + Redis) for large PDFs and batches
- Postgres in prod, with row-level encryption for stored entity text
- Optional structured JSON extraction alongside redaction
- Scanned-PDF OCR via Tesseract or a managed service

## License

MIT. See [LICENSE](LICENSE).
