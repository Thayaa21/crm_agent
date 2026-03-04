import { useState, useEffect } from 'react'
import { getAgentTrace, getAgentStatus } from '../api'

export default function AgentTracer({ jobId, running }) {
  const [trace, setTrace] = useState([])
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!jobId) {
      setTrace([])
      setStatus(null)
      setError(null)
      return
    }
    const poll = () => {
      getAgentTrace(jobId)
        .then((r) => setTrace(r.trace || []))
        .catch(() => {})
      getAgentStatus(jobId)
        .then((s) => {
          setStatus(s.status)
          setError(s.error || null)
        })
        .catch(() => {})
    }
    poll()
    const id = setInterval(poll, 1500)
    return () => clearInterval(id)
  }, [jobId])

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
      <h2 className="text-lg font-semibold text-slate-100 mb-4">Agent Tracer</h2>
      {!jobId && (
        <p className="text-slate-500 text-sm">Click &quot;Run Agent Now&quot; to see step-by-step reasoning.</p>
      )}
      {jobId && (
        <div className="flex items-center gap-2 mb-3 text-sm">
          <span className="text-slate-500">Job:</span>
          <span className="font-mono text-slate-400 truncate">{jobId.slice(0, 8)}…</span>
          {status === 'running' && <span className="text-amber-400">Running…</span>}
          {status === 'completed' && <span className="text-emerald-400">Completed</span>}
          {status === 'failed' && <span className="text-red-400">Failed</span>}
        </div>
      )}
      {error && (
        <div className="mb-3 p-3 rounded-lg bg-red-900/30 border border-red-800 text-red-300 text-sm">
          {error}
        </div>
      )}
      <div className="space-y-2 max-h-72 overflow-y-auto">
        {trace.map((step, i) => (
          <div
            key={i}
            className="rounded-lg border border-slate-700 bg-slate-800/50 p-3 text-sm"
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="text-slate-500 font-mono">{step.step}</span>
              <span className="px-2 py-0.5 rounded bg-slate-700 text-slate-300 text-xs">
                {step.agent}
              </span>
              <span className="text-slate-500 text-xs">{step.action}</span>
            </div>
            <p className="text-slate-300 text-xs whitespace-pre-wrap line-clamp-3">{step.summary}</p>
            {step.timestamp && (
              <p className="text-slate-500 text-xs mt-1">
                {typeof step.timestamp === 'string' ? step.timestamp.slice(0, 19) : ''}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
