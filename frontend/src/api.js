const BASE = "";

async function handle(res) {
  if (!res.ok) {
    let msg = res.statusText;
    try {
      const body = await res.json();
      if (body?.error) msg = body.error;
    } catch (_) {}
    throw new Error(msg);
  }
  if (res.status === 204) return null;
  const ctype = res.headers.get("content-type") || "";
  return ctype.includes("application/json") ? res.json() : res.blob();
}

export const api = {
  listDocuments: () => fetch(`${BASE}/api/documents`).then(handle),
  getDocument: (id) => fetch(`${BASE}/api/documents/${id}`).then(handle),
  uploadDocument: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return fetch(`${BASE}/api/documents`, { method: "POST", body: fd }).then(handle);
  },
  deleteDocument: (id) =>
    fetch(`${BASE}/api/documents/${id}`, { method: "DELETE" }).then(handle),
  redact: (id) =>
    fetch(`${BASE}/api/documents/${id}/redact`, { method: "POST" }).then(handle),
  updateEntity: (id, review_state) =>
    fetch(`${BASE}/api/entities/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ review_state }),
    }).then(handle),
  audit: (docId) => fetch(`${BASE}/api/documents/${docId}/audit`).then(handle),
  redactedUrl: (id) => `${BASE}/api/documents/${id}/redacted`,
};
