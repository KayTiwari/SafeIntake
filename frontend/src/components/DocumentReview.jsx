import { useEffect, useState } from "react";
import { api } from "../api.js";
import EntityList from "./EntityList.jsx";

export default function DocumentReview({ documentId, onMutate, onError }) {
  const [doc, setDoc] = useState(null);
  const [busy, setBusy] = useState(false);

  async function refresh() {
    if (!documentId) return;
    try {
      setDoc(await api.getDocument(documentId));
    } catch (e) {
      onError?.(e.message);
    }
  }

  useEffect(() => {
    refresh();
  }, [documentId]);

  if (!documentId) {
    return <div className="empty">Select or upload a document to begin review.</div>;
  }
  if (!doc) return <div className="empty">Loading…</div>;

  async function handleRedact() {
    setBusy(true);
    try {
      await api.redact(doc.id);
      await refresh();
      onMutate?.();
    } catch (e) {
      onError?.(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    if (!confirm(`Delete "${doc.filename}"? This removes the file and all audit history.`)) return;
    try {
      await api.deleteDocument(doc.id);
      onMutate?.(null);
    } catch (e) {
      onError?.(e.message);
    }
  }

  return (
    <div className="review-card">
      <h1>{doc.filename}</h1>
      <dl className="kv">
        <dt>Status</dt>
        <dd>
          <span className={`status-pill status-${doc.status}`}>{doc.status}</span>
        </dd>
        <dt>Pages</dt>
        <dd>{doc.page_count}</dd>
        <dt>Detections</dt>
        <dd>{doc.entities.length}</dd>
        <dt>Uploaded</dt>
        <dd>{new Date(doc.created_at).toLocaleString()}</dd>
      </dl>
      <div className="actions">
        <button className="btn primary" onClick={handleRedact} disabled={busy}>
          {busy ? "Redacting…" : "Apply Redactions"}
        </button>
        {doc.has_redacted && (
          <a className="btn" href={api.redactedUrl(doc.id)} target="_blank" rel="noreferrer">
            Download Redacted PDF
          </a>
        )}
        <button className="btn danger" onClick={handleDelete}>
          Delete
        </button>
      </div>
      <div style={{ marginTop: 18 }}>
        <h2 style={{ fontSize: 12, textTransform: "uppercase", color: "var(--muted)", letterSpacing: 1 }}>
          Detected Entities
        </h2>
        <EntityList
          entities={doc.entities}
          onChange={refresh}
          onError={onError}
        />
      </div>
    </div>
  );
}
