import type { ExtractResponse } from './types'

const BASE = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000'

export async function extractJobs(job_title: string, city: string): Promise<ExtractResponse> {
  const res = await fetch(`${BASE}/extract_jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job_title, city })
  })

  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`Errore API ${res.status}${text ? `: ${text}` : ''}`)
  }

  return res.json() as Promise<ExtractResponse>
}