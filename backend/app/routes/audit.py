from flask import Blueprint, abort, jsonify

from ..models import AuditEvent, Document, db

bp = Blueprint("audit", __name__, url_prefix="/api/documents")


@bp.get("/<int:doc_id>/audit")
def list_audit(doc_id: int):
    doc = db.session.get(Document, doc_id) or abort(404)
    events = (
        AuditEvent.query
        .filter_by(document_id=doc.id)
        .order_by(AuditEvent.created_at.asc())
        .all()
    )
    return jsonify([e.to_dict() for e in events])
