from __future__ import annotations

from flask import Blueprint, abort, jsonify, request

from ..models import AuditEvent, Entity, db

bp = Blueprint("entities", __name__, url_prefix="/api/entities")

_ALLOWED_STATES = {"pending", "approved", "rejected"}


def _actor() -> str:
    return request.headers.get("X-Actor", "anonymous")


@bp.patch("/<int:entity_id>")
def update_entity(entity_id: int):
    entity = db.session.get(Entity, entity_id) or abort(404)
    body = request.get_json(silent=True) or {}
    new_state = body.get("review_state")
    if new_state not in _ALLOWED_STATES:
        abort(400, description=f"review_state must be one of {_ALLOWED_STATES}")
    old_state = entity.review_state
    entity.review_state = new_state
    db.session.add(
        AuditEvent(
            document_id=entity.document_id,
            actor=_actor(),
            action="entity_review",
            detail=(
                f"entity_id={entity.id} type={entity.entity_type} "
                f"{old_state}->{new_state}"
            ),
        )
    )
    db.session.commit()
    return jsonify(entity.to_dict())
