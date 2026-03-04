import { useEffect } from 'react'

export default function Dashboard({ summary, loading }) {
  if (loading) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
        <div className="animate-pulse flex gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 flex-1 rounded-lg bg-slate-700" />
          ))}
        </div>
      </div>
    )
  }

  const cx = summary?.cx_health_score ?? 0
  const churn = summary?.churn_risk ?? 0
  const nps = summary?.nps_score ?? 0
  const open = summary?.open_issues_count ?? 0

  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
      <h2 className="text-lg font-semibold text-slate-100 mb-4">Dashboard</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          label="CX Health Score"
          value={cx}
          suffix="%"
          color={cx >= 70 ? 'text-emerald-400' : cx >= 40 ? 'text-amber-400' : 'text-red-400'}
        />
        <MetricCard
          label="Churn Risk"
          value={churn}
          suffix="%"
          color={churn <= 30 ? 'text-emerald-400' : churn <= 60 ? 'text-amber-400' : 'text-red-400'}
        />
        <MetricCard label="Open Issues" value={open} color="text-slate-200" />
        <MetricCard label="NPS Score" value={nps} color="text-slate-200" />
      </div>
      {summary?.top_issues?.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-700">
          <h3 className="text-sm font-medium text-slate-400 mb-2">Top issues</h3>
          <ul className="flex flex-wrap gap-2">
            {summary.top_issues.map((i, idx) => (
              <li key={idx} className="text-sm text-slate-300">
                <span className="text-slate-500">{i.category}:</span> {i.count}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  )
}

function MetricCard({ label, value, suffix = '', color }) {
  return (
    <div className="rounded-lg bg-slate-800/80 p-4 border border-slate-700/50">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className={`text-2xl font-semibold mt-1 ${color}`}>
        {value}
        {suffix}
      </p>
    </div>
  )
}
