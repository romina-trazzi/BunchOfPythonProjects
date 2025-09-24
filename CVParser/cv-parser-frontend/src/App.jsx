import React, { useRef, useState, useEffect } from "react";
import "./style.css";

function downloadJSON(obj, filename = "parsed_resume.json") {
  const blob = new Blob([JSON.stringify(obj, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function safeFilename(base = "parsed_resume", fallbackExt = "json") {
  const cleaned = String(base).replace(/[\\/:*?"<>|]+/g, "_").trim() || "parsed_resume";
  const dt = new Date();
  const stamp = [
    dt.getFullYear(),
    String(dt.getMonth() + 1).padStart(2, "0"),
    String(dt.getDate()).padStart(2, "0"),
    String(dt.getHours()).padStart(2, "0"),
    String(dt.getMinutes()).padStart(2, "0")
  ].join("");
  return `${cleaned}_${stamp}.${fallbackExt}`;
}

function Spinner() {
  return <div className="spinner" aria-hidden="true" />;
}

export default function App() {
  const fileInputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [mode, setMode] = useState("local");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";



  useEffect(() => {
    function onKeyDown(e) {
      const isMac = /Mac|iPod|iPhone|iPad/.test(window.navigator.platform);
      const saveCombo = (isMac && e.metaKey && e.key.toLowerCase() === "s") ||
                        (!isMac && e.ctrlKey && e.key.toLowerCase() === "s");
      if (saveCombo) {
        e.preventDefault();
        if (!result) {
          setError("Non c'è alcun JSON da salvare. Carica ed elabora un CV prima di salvare.");
          return;
        }
        const base = file?.name?.replace(/\.pdf$/i, "") || "parsed_resume";
        downloadJSON(result, safeFilename(base, "json"));
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [result, file]);

  function onFileSelected(e) {
    setError("");
    const f = e.target.files?.[0] ?? null;
    if (f && f.type !== "application/pdf") {
      setError("Seleziona un file PDF.");
      setFile(null);
      return;
    }
    setFile(f);
  }

  function onDrop(e) {
    e.preventDefault();
    setError("");
    const f = e.dataTransfer.files?.[0];
    if (!f) return;
    if (f.type !== "application/pdf") {
      setError("Trascina un file PDF.");
      return;
    }
    setFile(f);
  }
  function onDragOver(e) { e.preventDefault(); }

  async function handleUpload() {
  setError("");
  setResult(null);

  if (!file) {
    setError("Nessun file selezionato.");
    return;
  }

  setLoading(true);
  try {
    const fd = new FormData();
    fd.append("file", file, file.name);

    // Il backend si aspetta "local" | "external" (non "ocr")
    const apiMode = mode === "external" ? "external" : "local";

    const res = await fetch(`${API}/parse?mode=${apiMode}&language=ita`, {
      method: "POST",
      body: fd,
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Server: ${res.status} — ${text}`);
    }

    const data = await res.json(); // body: { schema: {...} }
    // leggo le percentuali dagli header (esposti dal CORS)
    const core = Number(res.headers.get("X-Completion-Core"));
    const global = Number(res.headers.get("X-Completion-Global"));

    setResult({
      schema: data?.schema ?? {},
      completamento_percentuale: Number.isFinite(core) ? core : undefined,
      completamento_schema_percentuale: Number.isFinite(global) ? global : undefined,
    });
  } catch (err) {
    console.error(err);
    setError(err.message || "Errore sconosciuto durante l'upload.");
  } finally {
    setLoading(false);
  }
}

  function resetAll() {
    setFile(null);
    setError("");
    setResult(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  return (
    <div className="page">
      <header className="card-header container">
        <h1>CV → JSON</h1>
        <p className="muted">Carica il tuo CV in PDF e ottieni il JSON strutturato.</p>
      </header>

      <main className="card container">
        <section
          className={`dropzone ${file ? "has-file" : ""}`}
          onDrop={onDrop}
          onDragOver={onDragOver}
          onClick={() => fileInputRef.current?.click()}
          role="button"
          aria-label="Trascina qui il CV o clicca per selezionarlo"
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            onChange={onFileSelected}
            className="file-input-hidden"
            aria-hidden
          />

          {!file && (
            <div className="dropzone-empty">
              <svg className="icon" viewBox="0 0 24 24" aria-hidden>
                <path d="M12 3v9m0 0l-3-3m3 3 3-3"/>
                <path d="M20.4 14.6A5 5 0 0 0 12 10H11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
              </svg>
              <div className="drop-title">Trascina qui il PDF del tuo CV</div>
              <div className="drop-sub">oppure clicca per selezionarlo</div>
            </div>
          )}

          {file && (
            <div className="file-preview">
              <div className="file-meta">
                <strong>{file.name}</strong>
                <div className="muted">{(file.size / 1024).toFixed(1)} KB</div>
              </div>
              <button
                className="btn small ghost"
                onClick={(e) => { e.stopPropagation(); resetAll(); }}
                aria-label="Rimuovi file"
              >
                Rimuovi
              </button>
            </div>
          )}
        </section>

        <div className="controls">
          <div className="modes" role="radiogroup" aria-label="Modalità parsing">
            <label className={`chip ${mode === "local" ? "active" : ""}`}>
              <input name="mode" type="radio" value="local" checked={mode === "local"} onChange={() => setMode("local")} />
              Locale
            </label>
            <label className={`chip ${mode === "external" ? "active" : ""}`}>
              <input name="mode" type="radio" value="external" checked={mode === "external"} onChange={() => setMode("external")} />
              Esterno
            </label>
          </div>

          <div className="actions">
            <button className="btn" onClick={handleUpload} disabled={loading}>
              {loading ? (<><Spinner />Elaborazione...</>) : "Invia e genera JSON"}
            </button>
            <button className="btn ghost" onClick={resetAll} disabled={loading}>Reset</button>
          </div>
        </div>

        {error && <div className="alert error" role="alert">{error}</div>}

        {result && (
          <section className="result">
            <div className="result-header">
              <div className="result-title">
                <h2>Risultato <span className="hint">(Ctrl+S / ⌘S per salvare)</span></h2>
              </div>
              <div className="result-actions">
                <button className="btn small" onClick={() => {
                  const base = file?.name?.replace(/\.pdf$/i, "") || "parsed_resume";
                  downloadJSON(result?.schema, safeFilename(base, "json"));
                }}>
                  
                  Salva JSON
                </button>
                <button className="btn small ghost" onClick={() => {
                  navigator.clipboard?.writeText(JSON.stringify(result?.schema, null, 2));
                }}>
                  Copia JSON
                </button>
              </div>
            </div>

            <pre className="json">
              {JSON.stringify(result?.schema, null, 2)}
            </pre>

            {(typeof result.completamento_percentuale === "number" ||
              typeof result.completamento_schema_percentuale === "number") && (
              <div className="progress-stack" aria-label="Indicatori di completezza">
                {/* Core */}
                {typeof result.completamento_percentuale === "number" && (
                  <div className="progress-wrap" aria-label="Completamento core">
                    <div className="progress-meta">
                      <div>Completamento (core)</div>
                      <div className="progress-value">
                        {result.completamento_percentuale}%
                      </div>
                    </div>
                    <progress
                      className={`progress ${
                        result.completamento_percentuale >= 80
                          ? "ok"
                          : result.completamento_percentuale >= 50
                          ? "warn"
                          : "bad"
                      }`}
                      max="100"
                      value={Math.min(100, Math.max(0, result.completamento_percentuale))}
                    />
                  </div>
                )}

                {/* Schema */}
                {typeof result.completamento_schema_percentuale === "number" && (
                  <div className="progress-wrap" aria-label="Completezza schema">
                    <div className="progress-meta">
                      <div>Completezza schema</div>
                      <div className="progress-value">
                        {result.completamento_schema_percentuale}%
                      </div>
                    </div>
                    <progress
                      className={`progress ${
                        result.completamento_schema_percentuale >= 80
                          ? "ok"
                          : result.completamento_schema_percentuale >= 50
                          ? "warn"
                          : "bad"
                      }`}
                      max="100"
                      value={Math.min(100, Math.max(0, result.completamento_schema_percentuale))}
                    />
                  </div>
                )}
              </div>
            )}
          </section>
        )}

        <section className="card-footer container muted">
          Genera JSON: <code>{API}/parse</code>
        </section>
      </main>

      <footer>
        Svolto da: Romina Trazzi nel corso di Python e Machine Learning di BID 2024-2026
      </footer>
    </div>
  );
}