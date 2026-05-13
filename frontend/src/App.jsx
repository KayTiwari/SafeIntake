import { useEffect, useState } from "react";
import { api } from "./api.js";
import Upload from "./components/Upload.jsx";
import DocumentList from "./components/DocumentList.jsx";
import DocumentReview from "./components/DocumentReview.jsx";
import AuditLog from "./components/AuditLog.jsx";

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [error, setError] = useState(null);
  const [tick, setTick] = useState(0);

  async function refresh() {
    try {
      const list = await api.listDocuments();
      setDocuments(list);
      setTick((t) => t + 1);
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  function handleUploaded(doc) {
    setError(null);
    setActiveId(doc.id);
    refresh();
  }

  function handleMutate(nextId) {
    if (nextId === null) setActiveId(null);
    refresh();
  }

  return (
    <div className="app">
      <div className="topbar">
        <div className="brand">
          SafeIntake
          <small>AI-assisted PHI redaction & document intake</small>
        </div>
        <div style={{ fontSize: 12, color: "var(--muted)" }}>
          Reviewer-in-the-loop · Audit logged
        </div>
      </div>
      <div className="layout">
        <aside className="sidebar">
          <div className="section">
            <h2>Upload</h2>
            <Upload onUploaded={handleUploaded} onError={setError} />
          </div>
          <div className="section">
            <h2>Documents</h2>
            <DocumentList
              documents={documents}
              activeId={activeId}
              onSelect={setActiveId}
            />
          </div>
        </aside>
        <main className="main">
          {error && <div className="errbar">{error}</div>}
          <DocumentReview
            documentId={activeId}
            onMutate={handleMutate}
            onError={setError}
          />
        </main>
        <aside className="inspector">
          <div className="section">
            <h2>Audit Trail</h2>
            <AuditLog documentId={activeId} version={tick} />
          </div>
        </aside>
      </div>
    </div>
  );
}
