import { useState } from 'react'
import type { ExtractResponse } from './types'
import { extractJobs } from './api'

export default function App() {
  const [job, setJob] = useState('Data Scientist')
  const [city, setCity] = useState('Milano')
  const [data, setData] = useState<ExtractResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  async function onSearch(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setErr(null)
    setData(null)
    try {
      const res = await extractJobs(job, city)
      setData(res)
    } catch (e: any) {
      setErr(e?.message ?? 'Errore')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 900, margin: '32px auto', padding: '0 12px' }}>
      <h1>Orchestratore Agent</h1>

      <form onSubmit={onSearch} style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        <input value={job} onChange={(e) => setJob(e.target.value)} placeholder="Professione (es. Data Scientist)" />
        <input value={city} onChange={(e) => setCity(e.target.value)} placeholder="Città (es. Milano)" />
        <button type="submit" disabled={loading}>Cerca</button>
      </form>

      {loading && <div style={{ padding: 12 }}>⏳ Elaborazione…</div>}
      {err && <p style={{ color: 'red' }}>{err}</p>}

      {data && (
        <>
          <p style={{ marginTop: 12 }}>
            Totale: <b>{data.count}</b>{' '}
            {data.report_path && (
              <>
                — <a href="#" onClick={(e) => { e.preventDefault(); alert('Report salvato su backend: ' + data.report_path) }}>
                  Vedi percorso report
                </a>
              </>
            )}
          </p>

          <table border={1} cellPadding={6} style={{ marginTop: 12, width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th>Titolo</th>
                <th>Azienda</th>
                <th>Città</th>
                <th>Link</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((it, i) => (
                <tr key={i}>
                  <td>{it.title}</td>
                  <td>{it.company ?? '-'}</td>
                  <td>{it.city ?? data.city}</td>
                  <td>{it.url ? <a href={it.url} target="_blank">Apri</a> : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  )
}