from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utcnow():
    return datetime.now(timezone.utc)


class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(512), nullable=False)
    stored_path = db.Column(db.String(1024), nullable=False)
    redacted_path = db.Column(db.String(1024))
    status = db.Column(db.String(32), nullable=False, default="uploaded")
    page_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    entities = db.relationship(
        "Entity", backref="document", cascade="all, delete-orphan", lazy="dynamic"
    )
    audit_events = db.relationship(
        "AuditEvent", backref="document", cascade="all, delete-orphan", lazy="dynamic"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "status": self.status,
            "page_count": self.page_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "entity_count": self.entities.count(),
            "has_redacted": bool(self.redacted_path),
        }


class Entity(db.Model):
    """A detected PHI/PII span in a document."""

    __tablename__ = "entities"

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(
        db.Integer, db.ForeignKey("documents.id"), nullable=False, index=True
    )
    page = db.Column(db.Integer, nullable=False)
    entity_type = db.Column(db.String(64), nullable=False)
    text = db.Column(db.String(1024), nullable=False)
    # Bounding box on the page in PDF points
    x0 = db.Column(db.Float, nullable=False)
    y0 = db.Column(db.Float, nullable=False)
    x1 = db.Column(db.Float, nullable=False)
    y1 = db.Column(db.Float, nullable=False)
    confidence = db.Column(db.Float, default=1.0)
    source = db.Column(db.String(32), default="regex")
    # Reviewer state: pending, approved, rejected
    review_state = db.Column(db.String(16), default="pending", nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "document_id": self.document_id,
            "page": self.page,
            "entity_type": self.entity_type,
            "text": self.text,
            "bbox": [self.x0, self.y0, self.x1, self.y1],
            "confidence": self.confidence,
            "source": self.source,
            "review_state": self.review_state,
        }


class AuditEvent(db.Model):
    """Immutable record of actions taken against a document."""

    __tablename__ = "audit_events"

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(
        db.Integer, db.ForeignKey("documents.id"), nullable=False, index=True
    )
    actor = db.Column(db.String(128), nullable=False, default="system")
    action = db.Column(db.String(64), nullable=False)
    detail = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "document_id": self.document_id,
            "actor": self.actor,
            "action": self.action,
            "detail": self.detail,
            "created_at": self.created_at.isoformat(),
        }
