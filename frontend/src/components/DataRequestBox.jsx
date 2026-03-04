import { useState } from 'react'

const DATA_TYPES = [
  'string',
  'number',
  'integer',
  'boolean',
  'date',
  'datetime',
  'email',
  'phone',
  'url',
  'text',
  'id',
]

const defaultColumn = () => ({ name: '', type: 'string' })

export default function DataRequestBox() {
  const [description, setDescription] = useState('')
  const [columns, setColumns] = useState([defaultColumn()])
  const [submitted, setSubmitted] = useState(null)

  const addColumn = () => setColumns((c) => [...c, defaultColumn()])
  const removeColumn = (i) => setColumns((c) => c.filter((_, j) => j !== i))
  const updateColumn = (i, field, value) =>
    setColumns((c) => c.map((col, j) => (j === i ? { ...col, [field]: value } : col)))

  const handleSubmit = (e) => {
    e.preventDefault()
    const payload = {
      description: description.trim() || undefined,
      columns: columns.filter((col) => col.name.trim()).map((col) => ({ name: col.name.trim(), type: col.type })),
    }
    setSubmitted(payload)
    try {
      localStorage.setItem('crm-agent-data-request', JSON.stringify(payload, null, 2))
    } catch (_) {}
  }

  const clearForm = () => {
    setDescription('')
    setColumns([defaultColumn()])
    setSubmitted(null)
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
      <h2 className="text-lg font-semibold text-slate-100 mb-1">Data request</h2>
      <p className="text-slate-500 text-sm mb-4">
        Describe the data you need and define columns with names and types.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">
            What kind of data do you need?
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g. Customer support tickets with issue category, priority, and region for the last 30 days"
            rows={2}
            className="w-full rounded-lg border border-slate-700 bg-slate-800 text-slate-200 px-3 py-2 text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
          />
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-sm font-medium text-slate-400">Columns (name + type)</label>
            <button
              type="button"
              onClick={addColumn}
              className="text-xs text-brand-400 hover:text-brand-300 font-medium"
            >
              + Add column
            </button>
          </div>
          <div className="space-y-2">
            {columns.map((col, i) => (
              <div key={i} className="flex gap-2 items-center">
                <input
                  type="text"
                  value={col.name}
                  onChange={(e) => updateColumn(i, 'name', e.target.value)}
                  placeholder="Column name"
                  className="flex-1 rounded-lg border border-slate-700 bg-slate-800 text-slate-200 px-3 py-2 text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
                <select
                  value={col.type}
                  onChange={(e) => updateColumn(i, 'type', e.target.value)}
                  className="rounded-lg border border-slate-700 bg-slate-800 text-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 min-w-[120px]"
                >
                  {DATA_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={() => removeColumn(i)}
                  disabled={columns.length === 1}
                  className="p-2 rounded text-slate-500 hover:text-red-400 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed"
                  title="Remove column"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="flex gap-2 pt-2">
          <button
            type="submit"
            className="px-4 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium"
          >
            Save data request
          </button>
          <button
            type="button"
            onClick={clearForm}
            className="px-4 py-2 rounded-lg border border-slate-600 text-slate-400 hover:text-slate-200 text-sm font-medium"
          >
            Clear
          </button>
        </div>
      </form>

      {submitted && (
        <div className="mt-4 pt-4 border-t border-slate-700">
          <p className="text-xs text-slate-500 mb-2">Saved request (column name + data type):</p>
          <pre className="text-xs text-slate-400 bg-slate-800/80 rounded-lg p-3 overflow-x-auto max-h-40 overflow-y-auto">
            {JSON.stringify(submitted, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}
