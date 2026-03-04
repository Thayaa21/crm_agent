// In dev, proxy /api to backend. In production, use VITE_API_URL (backend URL, no trailing slash, no /api).
const BASE = import.meta.env.DEV ? '/api' : (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

export async function runAgent() {
  const res = await fetch(`${BASE}/agent/run`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getAgentStatus(jobId) {
  const res = await fetch(`${BASE}/agent/status/${jobId}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getAgentTrace(jobId) {
  const res = await fetch(`${BASE}/agent/trace/${jobId}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getDashboardSummary() {
  const res = await fetch(`${BASE}/dashboard/summary`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getDashboardHeatmap() {
  const res = await fetch(`${BASE}/dashboard/heatmap`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getAlerts() {
  const res = await fetch(`${BASE}/alerts`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function chat(message) {
  const res = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getDataFormats() {
  const res = await fetch(`${BASE}/data/formats`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function uploadDataFile(kind, mode, file) {
  const form = new FormData()
  form.append('kind', kind)
  form.append('mode', mode)
  form.append('file', file)
  const res = await fetch(`${BASE}/data/upload`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}
