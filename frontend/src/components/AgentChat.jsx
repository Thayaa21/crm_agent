import { useState } from 'react'
import { chat } from '../api'

export default function AgentChat() {
  const [message, setMessage] = useState('')
  const [reply, setReply] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const send = (e) => {
    e?.preventDefault()
    if (!message.trim() || loading) return
    setError(null)
    setLoading(true)
    chat(message.trim())
      .then((r) => {
        setReply(r)
        setMessage('')
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
      <h2 className="text-lg font-semibold text-slate-100 mb-4">Agent Chat (Q&A with citations)</h2>
      <form onSubmit={send} className="flex gap-2 mb-4">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="e.g. Should we roll back the iOS deployment?"
          className="flex-1 rounded-lg border border-slate-700 bg-slate-800 text-slate-200 px-3 py-2 text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium disabled:opacity-50"
        >
          {loading ? '…' : 'Ask'}
        </button>
      </form>
      {error && <p className="text-red-400 text-sm mb-2">{error}</p>}
      {reply && (
        <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
          <p className="text-slate-200 text-sm whitespace-pre-wrap">{reply.answer}</p>
          {reply.sources?.length > 0 && (
            <div className="mt-3 pt-3 border-t border-slate-700">
              <p className="text-xs text-slate-500 mb-1">Sources</p>
              <ul className="text-xs text-slate-400 space-y-0.5">
                {reply.sources.map((s, i) => (
                  <li key={i}>[{s.index}] {JSON.stringify(s.metadata)}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
