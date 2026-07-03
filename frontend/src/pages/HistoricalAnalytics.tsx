import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import Plot from 'react-plotly.js'
import { BarChart3, Search, Filter } from 'lucide-react'
import { getHistoricalResults, getRaces } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

const PLOT_LAYOUT = {
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  font: { color: 'rgba(255,255,255,0.6)', family: 'Inter', size: 11 },
  margin: { l: 48, r: 20, t: 16, b: 80 },
  xaxis: { gridcolor: 'rgba(255,255,255,0.05)', tickangle: -35 },
  yaxis: { gridcolor: 'rgba(255,255,255,0.05)' },
  legend: { bgcolor: 'transparent' },
}

export default function HistoricalAnalytics() {
  const [filters, setFilters] = useState({ driver_code: '', season: '', grand_prix: '', limit: 50 })
  const [applied, setApplied] = useState({ driver_code: '', season: undefined as number | undefined, grand_prix: '', limit: 50 })

  const { data, isLoading, error } = useQuery({
    queryKey: ['historical', applied],
    queryFn: () => getHistoricalResults({
      driver_code: applied.driver_code || undefined,
      season: applied.season,
      grand_prix: applied.grand_prix || undefined,
      limit: applied.limit,
    }),
  })

  const applyFilters = () => setApplied({
    driver_code: filters.driver_code,
    season: filters.season ? +filters.season : undefined,
    grand_prix: filters.grand_prix,
    limit: filters.limit,
  })

  // Chart data: finish position distribution
  const chartData = data ? (() => {
    const grouped: Record<string, number[]> = {}
    data.forEach((r: any) => {
      const key = r.driver_code || 'Unknown'
      if (!grouped[key]) grouped[key] = []
      grouped[key].push(r.finish_position)
    })
    return grouped
  })() : {}

  const traces = Object.entries(chartData).slice(0, 5).map(([code, positions], i) => ({
    name: code,
    y: positions,
    type: 'box' as const,
    boxmean: true,
    marker: { color: ['#E10600', '#27F4D2', '#FF8000', '#F59E0B', '#8B5CF6'][i] },
  }))

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-3xl font-display font-black text-white flex items-center gap-3">
          <BarChart3 className="w-8 h-8 text-f1-red" />
          Historical Analytics
        </h1>
        <p className="text-white/50 mt-1">Query and visualize historical race results from 2022–2026</p>
      </div>

      {/* Filters */}
      <div className="card grid grid-cols-2 md:grid-cols-5 gap-4">
        <div>
          <label className="text-[10px] text-white/40 uppercase tracking-wider mb-1 block">Driver Code</label>
          <input className="input-field" placeholder="VER" maxLength={4}
            value={filters.driver_code} onChange={e => setFilters(f => ({ ...f, driver_code: e.target.value.toUpperCase() }))} />
        </div>
        <div>
          <label className="text-[10px] text-white/40 uppercase tracking-wider mb-1 block">Season</label>
          <select className="select-field" value={filters.season} onChange={e => setFilters(f => ({ ...f, season: e.target.value }))}>
            <option value="">All</option>
            {[2022, 2023, 2024, 2025, 2026].map(y => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>
        <div className="col-span-2">
          <label className="text-[10px] text-white/40 uppercase tracking-wider mb-1 block">Grand Prix</label>
          <input className="input-field" placeholder="British Grand Prix"
            value={filters.grand_prix} onChange={e => setFilters(f => ({ ...f, grand_prix: e.target.value }))} />
        </div>
        <div>
          <label className="text-[10px] text-white/40 uppercase tracking-wider mb-1 block">Limit</label>
          <select className="select-field" value={filters.limit} onChange={e => setFilters(f => ({ ...f, limit: +e.target.value }))}>
            {[25, 50, 100, 200].map(l => <option key={l} value={l}>{l}</option>)}
          </select>
        </div>
        <div className="flex items-end">
          <button onClick={applyFilters} className="btn-primary w-full justify-center">
            <Search className="w-4 h-4" /> Search
          </button>
        </div>
      </div>

      {isLoading && <LoadingSpinner message="Querying historical database..." />}

      {data && !isLoading && (
        <>
          {/* Stats */}
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: 'Results Found', value: data.length },
              { label: 'Unique Drivers', value: new Set(data.map((r: any) => r.driver_code)).size },
              { label: 'DNF Rate', value: `${(data.filter((r: any) => r.dnf).length / data.length * 100).toFixed(1)}%` },
            ].map(({ label, value }) => (
              <div key={label} className="card-glow text-center py-4">
                <div className="metric-value">{value}</div>
                <div className="metric-label">{label}</div>
              </div>
            ))}
          </div>

          {/* Box plot */}
          {traces.length > 0 && (
            <div className="card">
              <h3 className="section-title mb-4">Finish Position Distribution</h3>
              <Plot
                data={traces}
                layout={{ ...PLOT_LAYOUT, yaxis: { ...PLOT_LAYOUT.yaxis, title: 'Finishing Position', autorange: 'reversed' as const } }}
                config={{ displayModeBar: false, responsive: true }}
                style={{ width: '100%', height: 320 }}
              />
            </div>
          )}

          {/* Results table */}
          <div className="card overflow-hidden">
            <h3 className="section-title mb-4"><Filter className="w-4 h-4 text-blue-400" /> Results ({data.length})</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-f1-border">
                    {['Season', 'Round', 'Grand Prix', 'Driver', 'Constructor', 'Grid', 'Finish', 'Points', 'Status'].map(h => (
                      <th key={h} className="text-left py-2 px-3 text-[10px] text-white/40 uppercase tracking-wider font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.slice(0, 100).map((r: any, i: number) => (
                    <motion.tr
                      key={i}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.01 }}
                      className="table-row"
                    >
                      <td className="py-2 px-3 font-mono text-white/60">{r.season}</td>
                      <td className="py-2 px-3 font-mono text-white/60">{r.round_number}</td>
                      <td className="py-2 px-3 text-white truncate max-w-[160px]">{r.grand_prix_name}</td>
                      <td className="py-2 px-3">
                        <span className="badge badge-blue">{r.driver_code}</span>
                      </td>
                      <td className="py-2 px-3 text-white/60 text-xs">{r.constructor}</td>
                      <td className="py-2 px-3 font-mono text-white/60">P{r.grid_position}</td>
                      <td className={`py-2 px-3 font-mono font-bold ${r.finish_position === 1 ? 'pos-1' : r.finish_position === 2 ? 'pos-2' : r.finish_position === 3 ? 'pos-3' : 'text-white'}`}>
                        {r.dnf ? <span className="badge badge-red">DNF</span> : `P${r.finish_position}`}
                      </td>
                      <td className="py-2 px-3 font-mono text-white/60">{r.points_scored}</td>
                      <td className="py-2 px-3 text-white/50 text-xs">{r.status}</td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
