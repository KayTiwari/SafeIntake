import { api } from "../api.js";

const ENTITY_COLORS = {
  US_SSN: "var(--bad)",
  EMAIL: "var(--accent-2)",
  PHONE: "var(--accent-2)",
  DATE: "var(--warn)",
  MRN: "var(--bad)",
  ZIP: "var(--muted)",
  URL: "var(--accent-2)",
  CREDIT_CARD: "var(--bad)",
};

export default function EntityList({ entities, onChange, onError }) {
  async function setState(id, state) {
    try {
      const updated = await api.updateEntity(id, state);
      onChange?.(updated);
    } catch (e) {
      onError?.(e.message);
    }
  }

  const grouped = entities.reduce((acc, e) => {
    (acc[e.entity_type] ||= []).push(e);
    return acc;
  }, {});

  return (
    <div>
      <div className="legend">
        {Object.entries(grouped).map(([type, items]) => (
          <span key={type} style={{ color: ENTITY_COLORS[type] || "var(--text)" }}>
            <b>{type}</b>
            {items.length}
          </span>
        ))}
      </div>
      {entities.map((e) => (
        <div key={e.id} className={`entity-row ${e.review_state}`}>
          <span className="type" style={{ color: ENTITY_COLORS[e.entity_type] || "var(--accent-2)" }}>
            {e.entity_type}
          </span>
          <span className="text" title={e.text}>
            p{e.page + 1} · {e.text}
          </span>
          <span className="actions">
            <button
              className="btn"
              disabled={e.review_state === "approved"}
              onClick={() => setState(e.id, "approved")}
              title="Keep this redaction"
            >
              ✓
            </button>
            <button
              className="btn"
              disabled={e.review_state === "rejected"}
              onClick={() => setState(e.id, "rejected")}
              title="Skip this redaction"
            >
              ✕
            </button>
          </span>
        </div>
      ))}
    </div>
  );
}
