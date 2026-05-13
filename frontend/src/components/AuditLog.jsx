import { useEffect, useState } from "react";
import { api } from "../api.js";

export default function AuditLog({ documentId, version }) {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    if (!documentId) return;
    api.audit(documentId).then(setEvents).catch(() => setEvents([]));
  }, [documentId, version]);

  if (!documentId) return null;
  if (!events.length) return <div className="empty">No audit events yet.</div>;

  return (
    <div className="audit">
      {events.map((ev) => (
        <div className="row" key={ev.id}>
          <div>
            <span className="action">{ev.action}</span>
            {" · "}
            <span>{ev.actor}</span>
          </div>
          {ev.detail && <div>{ev.detail}</div>}
          <div className="ts">{new Date(ev.created_at).toLocaleString()}</div>
        </div>
      ))}
    </div>
  );
}
