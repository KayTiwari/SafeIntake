from __future__ import annotations

import os
import uuid
from pathlib import Path

from flask import Blueprint, abort, current_app, jsonify, request, send_file

from ..models import AuditEvent, Document, Entity, db
from ..services.pipeline import analyze
from ..services.redactor import redact

bp = Blueprint("documents", __name__, url_prefix="/api/documents")


def _actor() -> str:
    return request.headers.get("X-Actor", "anonymous")


@bp.get("")
def list_documents():
    docs = Document.query.order_by(Document.created_at.desc()).all()
    return jsonify([d.to_dict() for d in docs])


@bp.post("")
def upload_document():
    if "file" not in request.files:
        abort(400, description="file field required")
    f = request.files["file"]
    if not f.filename or not f.filename.lower().endswith(".pdf"):
        abort(400, description="only PDF uploads are supported")

    stored_name = f"{uuid.uuid4().hex}.pdf"
    stored_path = Path(current_app.config["UPLOAD_DIR"]) / stored_name
    f.save(stored_path)

    doc = Document(
        filename=f.filename,
        stored_path=str(stored_path),
        status="processing",
    )
    db.session.add(doc)
    db.session.flush()
    db.session.add(
        AuditEvent(
            document_id=doc.id,
            actor=_actor(),
            action="upload",
            detail=f"filename={f.filename} size={stored_path.stat().st_size}",
        )
    )
    db.session.commit()

    try:
        detections, page_count = analyze(str(stored_path))
    except Exception as exc:
        doc.status = "failed"
        db.session.add(
            AuditEvent(
                document_id=doc.id,
                actor="system",
                action="analyze_failed",
                detail=str(exc)[:500],
            )
        )
        db.session.commit()
        abort(500, description=f"analysis failed: {exc}")

    doc.page_count = page_count
    for d in detections:
        db.session.add(
            Entity(
                document_id=doc.id,
                page=d.page,
                entity_type=d.entity_type,
                text=d.text,
                x0=d.x0,
                y0=d.y0,
                x1=d.x1,
                y1=d.y1,
                confidence=d.confidence,
                source="regex",
            )
        )
    doc.status = "review"
    db.session.add(
        AuditEvent(
            document_id=doc.id,
            actor="system",
            action="analyze_complete",
            detail=f"entities={len(detections)} pages={page_count}",
        )
    )
    db.session.commit()
    return jsonify(doc.to_dict()), 201


@bp.get("/<int:doc_id>")
def get_document(doc_id: int):
    doc = db.session.get(Document, doc_id) or abort(404)
    payload = doc.to_dict()
    payload["entities"] = [e.to_dict() for e in doc.entities.all()]
    return jsonify(payload)


@bp.get("/<int:doc_id>/file")
def download_original(doc_id: int):
    doc = db.session.get(Document, doc_id) or abort(404)
    if not os.path.exists(doc.stored_path):
        abort(404)
    return send_file(doc.stored_path, mimetype="application/pdf")


@bp.get("/<int:doc_id>/redacted")
def download_redacted(doc_id: int):
    doc = db.session.get(Document, doc_id) or abort(404)
    if not doc.redacted_path or not os.path.exists(doc.redacted_path):
        abort(404, description="redacted file not generated yet")
    return send_file(
        doc.redacted_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"redacted_{doc.filename}",
    )


@bp.post("/<int:doc_id>/redact")
def apply_redactions(doc_id: int):
    doc = db.session.get(Document, doc_id) or abort(404)
    approved = [
        {
            "page": e.page,
            "x0": e.x0,
            "y0": e.y0,
            "x1": e.x1,
            "y1": e.y1,
            "entity_type": e.entity_type,
        }
        for e in doc.entities.filter(Entity.review_state.in_(("approved", "pending"))).all()
    ]
    if not approved:
        abort(400, description="no entities to redact")

    out_path = Path(current_app.config["REDACTED_DIR"]) / f"{doc.id}_redacted.pdf"
    redact(doc.stored_path, str(out_path), approved)
    doc.redacted_path = str(out_path)
    doc.status = "redacted"
    db.session.add(
        AuditEvent(
            document_id=doc.id,
            actor=_actor(),
            action="redact",
            detail=f"applied {len(approved)} redactions",
        )
    )
    db.session.commit()
    return jsonify(doc.to_dict())


@bp.delete("/<int:doc_id>")
def delete_document(doc_id: int):
    doc = db.session.get(Document, doc_id) or abort(404)
    for path in (doc.stored_path, doc.redacted_path):
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass
    db.session.delete(doc)
    db.session.commit()
    return "", 204
