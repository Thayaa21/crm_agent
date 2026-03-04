import { useState, useEffect } from 'react'
import { uploadDataFile, getDataFormats } from '../api'

const KINDS = [
  { value: 'tickets', label: 'Tickets (support tickets)' },
  { value: 'reviews', label: 'Reviews (customer reviews)' },
  { value: 'nps', label: 'NPS (Net Promoter responses)' },
]
const MODES = [
  { value: 'replace', label: 'Replace existing data' },
  { value: 'append', label: 'Append to existing data' },
]

export default function YourDataUpload() {
  const [kind, setKind] = useState('tickets')
  const [mode, setMode] = useState('replace')
  const [file, setFile] = useState(null)
  const [formats, setFormats] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    getDataFormats()
      .then(setFormats)
      .catch(() => setFormats(null))
  }, [])

  const handleFileChange = (e) => {
    const f = e.target.files?.[0]
    setFile(f || null)
    setResult(null)
    setError(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file) {
      setError('Please choose a file.')
      return
    }
    setError(null)
    setResult(null)
    setLoading(true)
    try {
      const res = await uploadDataFile(kind, mode, file)
      setResult(res)
      setFile(null)
      e.target.reset()
    } catch (err) {
      setError(err.message || 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  const formatHelp = formats?.[kind]

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
      <h2 className="text-lg font-semibold text-slate-100 mb-1">Your data</h2>
      <p className="text-slate-500 text-sm mb-4">
        Upload your own CSV or JSON file. The agent will use this data instead of (or with) generated data.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex flex-wrap gap-4 items-end">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Data type</label>
            <select
              value={kind}
              onChange={(e) => { setKind(e.target.value); setResult(null); setError(null); }}
              className="rounded-lg border border-slate-700 bg-slate-800 text-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 min-w-[180px]"
            >
              {KINDS.map((k) => (
                <option key={k.value} value={k.value}>{k.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Mode</label>
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value)}
              className="rounded-lg border border-slate-700 bg-slate-800 text-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 min-w-[180px]"
            >
              {MODES.map((m) => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">File (CSV or JSON)</label>
            <input
              type="file"
              accept=".csv,.json,text/csv,application/json"
              onChange={handleFileChange}
              className="block w-full text-sm text-slate-400 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:bg-slate-700 file:text-slate-200 hover:file:bg-slate-600"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !file}
            className="px-4 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Uploading…' : 'Upload'}
          </button>
        </div>

        {formatHelp && (
          <div className="rounded-lg bg-slate-800/60 border border-slate-700 p-3 text-sm">
            <p className="text-slate-400 font-medium mb-1">Expected format for {kind}</p>
            <p className="text-slate-500 text-xs mb-1">Required: {formatHelp.required.join(', ')}</p>
            <p className="text-slate-500 text-xs mb-1">Optional: {formatHelp.optional.join(', ')}</p>
            <p className="text-slate-500 text-xs">{formatHelp.note}</p>
          </div>
        )}

        {error && (
          <div className="p-3 rounded-lg bg-red-900/30 border border-red-800 text-red-300 text-sm">
            {error}
          </div>
        )}
        {result && (
          <div className="p-3 rounded-lg bg-emerald-900/20 border border-emerald-800 text-emerald-300 text-sm">
            Uploaded {result.rows_uploaded} {result.kind}. Total now: {result.total_now}.
          </div>
        )}
      </form>
    </div>
  )
}
