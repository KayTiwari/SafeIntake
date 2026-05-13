export default function DocumentList({ documents, activeId, onSelect }) {
  if (!documents.length) {
    return <div className="empty">No documents yet. Upload one to begin.</div>;
  }
  return (
    <ul className="doc-list">
      {documents.map((d) => (
        <li
          key={d.id}
          className={d.id === activeId ? "active" : ""}
          onClick={() => onSelect(d.id)}
        >
          <div className="filename">{d.filename}</div>
          <div className="meta">
            <span className={`status-pill status-${d.status}`}>{d.status}</span>
            {" · "}
            {d.entity_count} entities · {d.page_count} pages
          </div>
        </li>
      ))}
    </ul>
  );
}
