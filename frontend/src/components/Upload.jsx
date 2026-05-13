import { useRef, useState } from "react";
import { api } from "../api.js";

export default function Upload({ onUploaded, onError }) {
  const inputRef = useRef(null);
  const [dragover, setDragover] = useState(false);
  const [busy, setBusy] = useState(false);

  async function handleFiles(files) {
    if (!files || !files.length) return;
    const file = files[0];
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      onError?.("Only PDF files are supported.");
      return;
    }
    setBusy(true);
    try {
      const doc = await api.uploadDocument(file);
      onUploaded?.(doc);
    } catch (e) {
      onError?.(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className={`dropzone ${dragover ? "dragover" : ""}`}
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        setDragover(true);
      }}
      onDragLeave={() => setDragover(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragover(false);
        handleFiles(e.dataTransfer.files);
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        style={{ display: "none" }}
        onChange={(e) => handleFiles(e.target.files)}
      />
      {busy ? "Uploading and analyzing…" : "Drop a PDF here or click to choose"}
    </div>
  );
}
