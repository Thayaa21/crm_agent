import { useState, useEffect } from 'react'
import { getAlerts } from '../api'

const severityClass = {
  P0: 'bg-red-500/90 text-white animate-pulse-slow',
  P1: 'bg-amber-500/90 text-slate-900',
  P2: 'bg-slate-500/90 text-slate-200',
}

export default function AlertFeed({ refreshTrigger }) {
  const [alerts, setAlerts] = useState([])

  const refresh = () => getAlerts().then(setAlerts).catch(() => {})

  useEffect(() => {
    refresh()
  }, [refreshTrigger])

  useEffect(() => {
    const t = setInterval(refresh, 10000)
    return () => clearInterval(t)
  }, [])

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-slate-100">Alert Feed</h2>
        <button onClick={refresh} className="text-xs text-slate-500 hover:text-slate-300">
          Refresh
        </button>
      </div>
      <div className="space-y-2 max-h-72 overflow-y-auto">
        {alerts.length === 0 && (
          <p className="text-slate-500 text-sm">No alerts yet. Run the agent to generate alerts.</p>
        )}
        {alerts.map((a) => (
          <div
            key={a.id}
            className="rounded-lg border border-slate-700 bg-slate-800/50 p-3 hover:border-slate-600 transition"
          >
            <div className="flex items-center gap-2 mb-1">
              <span
                className={`px-2 py-0.5 rounded text-xs font-medium ${severityClass[a.severity] || severityClass.P2}`}
              >
                {a.severity}
              </span>
              {a.routed_to && (
                <span className="text-xs text-slate-500">→ {a.routed_to}</span>
              )}
            </div>
            <p className="text-sm font-medium text-slate-200">{a.title}</p>
            <p className="text-xs text-slate-400 mt-0.5 line-clamp-2">{a.body}</p>
            <p className="text-xs text-slate-500 mt-1">
              {typeof a.created_at === 'string' ? a.created_at.slice(0, 19) : a.created_at?.toISOString?.()?.slice(0, 19) ?? ''}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
