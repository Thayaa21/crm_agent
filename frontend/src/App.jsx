import { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import DataRequestBox from './components/DataRequestBox'
import YourDataUpload from './components/YourDataUpload'
import IssueHeatmap from './components/IssueHeatmap'
import AlertFeed from './components/AlertFeed'
import AgentChat from './components/AgentChat'
import AgentTracer from './components/AgentTracer'
import { runAgent, getAgentStatus, getDashboardSummary } from './api'

export default function App() {
  const [summary, setSummary] = useState(null)
  const [jobId, setJobId] = useState(null)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState(null)

  const refreshSummary = () => {
    getDashboardSummary().then(setSummary).catch(() => setSummary(null))
  }

  useEffect(() => {
    refreshSummary()
    const t = setInterval(refreshSummary, 15000)
    return () => clearInterval(t)
  }, [])

  const [alertsRefresh, setAlertsRefresh] = useState(0)
  useEffect(() => {
    if (!jobId || !running) return
    const poll = () => {
      getAgentStatus(jobId)
        .then((s) => {
          if (s.status === 'completed' || s.status === 'failed') {
            setRunning(false)
            refreshSummary()
            setAlertsRefresh((n) => n + 1)
          }
        })
        .catch(() => setRunning(false))
    }
    const id = setInterval(poll, 2000)
    return () => clearInterval(id)
  }, [jobId, running])

  const handleRunAgent = () => {
    setError(null)
    setRunning(true)
    runAgent()
      .then((r) => setJobId(r.job_id))
      .catch((e) => {
        setError(e.message)
        setRunning(false)
      })
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans">
      <header className="border-b border-slate-800 bg-slate-900/50 px-6 py-4">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <h1 className="text-xl font-semibold text-white">CRM Agent — CX Intelligence</h1>
          <button
            onClick={handleRunAgent}
            disabled={running}
            className="px-4 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            {running ? 'Running…' : 'Run Agent Now'}
          </button>
        </div>
        {error && <p className="text-red-400 text-sm mt-2">{error}</p>}
      </header>

      <main className="max-w-7xl mx-auto p-6 space-y-6">
        <Dashboard summary={summary} loading={!summary} />
        <YourDataUpload />
        <DataRequestBox />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <IssueHeatmap refreshTrigger={alertsRefresh} />
          <AlertFeed refreshTrigger={alertsRefresh} />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <AgentChat />
          <AgentTracer jobId={jobId} running={running} />
        </div>
      </main>
    </div>
  )
}
