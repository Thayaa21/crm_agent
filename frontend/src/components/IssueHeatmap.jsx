import { useState, useEffect } from 'react'
import { getDashboardHeatmap } from '../api'

export default function IssueHeatmap({ refreshTrigger }) {
  const [data, setData] = useState(null)

  const refresh = () => getDashboardHeatmap().then(setData).catch(() => setData(null))

  useEffect(() => {
    refresh()
  }, [refreshTrigger])

  useEffect(() => {
    refresh()
  }, [])

  if (!data) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
        <h2 className="text-lg font-semibold text-slate-100 mb-4">Issue Heatmap</h2>
        <div className="h-64 flex items-center justify-center text-slate-500">Loading…</div>
      </div>
    )
  }

  const { categories, time_buckets, matrix } = data
  const hasAlertsRow = categories?.includes?.('Alerts')
  const hasData =
    (categories?.length > 0 && matrix?.some((row) => row.some((v) => v > 0))) || hasAlertsRow
  const maxVal = hasData ? Math.max(...(matrix?.flat() ?? []), 1) : 1

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
      <h2 className="text-lg font-semibold text-slate-100 mb-4">Issue Heatmap (category × time)</h2>
      {!hasData ? (
        <div className="h-48 flex items-center justify-center text-slate-500 text-sm">
          No ticket or review data in the last 7 days. Seed data or upload your own to see the heatmap.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-xs">
            <thead>
              <tr>
                <th className="text-left p-2 text-slate-400 font-medium border border-slate-700">Category</th>
                {time_buckets.slice(-14).map((t) => (
                  <th key={t} className="p-1 text-slate-500 border border-slate-700 whitespace-nowrap" title={t}>
                    {t.slice(0, 5)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {categories.map((cat, i) => (
                <tr key={cat}>
                  <td className="p-2 text-slate-300 border border-slate-700 whitespace-nowrap">{cat}</td>
                  {time_buckets.slice(-14).map((t, j) => {
                    const idx = time_buckets.indexOf(t)
                    const val = matrix[i]?.[idx] ?? 0
                    const opacity = maxVal ? val / maxVal : 0
                    return (
                      <td
                        key={t}
                        className="border border-slate-700 p-0.5"
                        style={{ backgroundColor: `rgba(59, 130, 246, ${0.2 + 0.8 * opacity})` }}
                        title={`${cat} @ ${t}: ${val}`}
                      >
                        {val > 0 ? val : ''}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <p className="text-xs text-slate-500 mt-2">Categories vs time; intensity = volume. Last 14 buckets shown.</p>
    </div>
  )
}
