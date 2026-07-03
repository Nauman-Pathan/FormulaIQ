import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import Plot from 'react-plotly.js'
import { Users, Search, TrendingUp, Target, Zap } from 'lucide-react'
import { getDriverAnalysis } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

const METRIC_CONFIG = [
  { key: 'consistency_score',       label: 'Consistency',       color: '#E10600', max: 100 },
  { key: 'overtaking_efficiency',   label: 'Overtaking',        color: '#3B82F6', max: 100 },
  { key: 'tyre_management_score',   label: 'Tyre Management',   color: '#10B981', max: 100 },
  { key: 'qualifying_performance',  label: 'Qualifying',        color: '#F59E0B', max: 100 },
  { key: 'racecraft_score',         label: 'Racecraft',         color: '#8B5CF6', max: 100 },
]

const PLOT_LAYOUT = {
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  font: { color: 'rgba(255,255,255,0.6)', family: 'Inter', size: 11 },
  margin: { l: 48, r: 20, t: 16, b: 40 },
  xaxis: { gridcolor: 'rgba(255,255,255,0.05)' },
  yaxis: { gridcolor: 'rgba(255,255,255,0.05)' },
  legend: { bgcolor: 'transparent' },
}

function DriverPanel({ driverCode, color }: { driverCode: string; color: string }) {
  const [code, setCode] = useState(driverCode)
  const [season, setSeason] = useState<number | undefined>(undefined)
  const [search, setSearch] = useState(driverCode)

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['driver-analysis', code, season],
    queryFn: () => getDriverAnalysis(code, season),
    enabled: false,
  })

  return (
    <div className="space-y-4">
      {/* Search bar */}
      <div className="card flex gap-3">
        <input
          className="input-field"
          placeholder="Driver code e.g. VER"
          value={search}
          maxLength={4}
          onChange={e => setSearch(e.target.value.toUpperCase())}
          onKeyDown={e => { if (e.key === 'Enter') { setCode(search); setTimeout(() => refetch(), 0) } }}
        />
        <select className="select-field w-28" value={season || ''} onChange={e => setSeason(e.target.value ? +e.target.value : undefined)}>
          <option value="">All</option>
          {[2022, 2023, 2024, 2025, 2026].map(y => <option key={y} value={y}>{y}</option>)}
        </select>
        <button
          className="btn-primary shrink-0"
          onClick={() => { setCode(search); setTimeout(() => refetch(), 0) }}
        >
          <Search className="w-4 h-4" />
        </button>
      </div>

      {isLoading && <LoadingSpinner />}
      {error && <div className="card text-red-400 text-sm">{(error as any).message}</div>}

      {data && (
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          {/* Driver header */}
          <div className="card" style={{ borderLeftColor: color, borderLeftWidth: 3 }}>
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-xl font-display font-black text-white">{data.full_name}</h3>
                <p className="text-white/40 text-sm">{data.season} Season · {data.races_analyzed} races</p>
              </div>
              <div className="text-right">
                <div className="text-3xl font-display font-black" style={{ color }}>{data.racecraft_score.toFixed(0)}</div>
                <div className="text-xs text-white/40 uppercase">Racecraft</div>
              </div>
            </div>
          </div>

          {/* Stats grid */}
          <div className="grid grid-cols-3 gap-2">
            {[
              { label: 'Win Rate', value: `${(data.win_rate * 100).toFixed(1)}%` },
              { label: 'Podium Rate', value: `${(data.podium_rate * 100).toFixed(1)}%` },
              { label: 'DNF Rate', value: `${(data.dnf_rate * 100).toFixed(1)}%` },
              { label: 'Avg Grid', value: data.avg_grid_position.toFixed(1) },
              { label: 'Avg Finish', value: data.avg_finish_position.toFixed(1) },
              { label: 'Pos Gained', value: `+${data.avg_positions_gained.toFixed(1)}` },
            ].map(({ label, value }) => (
              <div key={label} className="card py-2 text-center">
                <div className="text-lg font-display font-bold text-white">{value}</div>
                <div className="text-[10px] text-white/40 uppercase">{label}</div>
              </div>
            ))}
          </div>

          {/* Radar chart */}
          <div className="card">
            <h4 className="section-title mb-3"><Target className="w-4 h-4" style={{ color }} /> Performance Radar</h4>
            <Plot
              data={[{
                type: 'scatterpolar',
                r: METRIC_CONFIG.map(m => data[m.key] || 0),
                theta: METRIC_CONFIG.map(m => m.label),
                fill: 'toself',
                fillcolor: `${color}22`,
                line: { color },
                name: data.driver_code,
              }]}
              layout={{
                polar: {
                  bgcolor: 'transparent',
                  radialaxis: { range: [0, 100], gridcolor: 'rgba(255,255,255,0.08)', tickfont: { color: 'rgba(255,255,255,0.3)', size: 9 } },
                  angularaxis: { gridcolor: 'rgba(255,255,255,0.08)', tickfont: { color: 'rgba(255,255,255,0.6)', size: 11 } },
                },
                paper_bgcolor: 'transparent',
                font: { color: 'rgba(255,255,255,0.7)', family: 'Inter' },
                margin: { l: 48, r: 48, t: 16, b: 16 },
                showlegend: false,
              }}
              config={{ displayModeBar: false, responsive: true }}
              style={{ width: '100%', height: 280 }}
            />
          </div>

          {/* Recent form */}
          <div className="card">
            <h4 className="section-title mb-3"><TrendingUp className="w-4 h-4 text-emerald-400" /> Recent Form</h4>
            <div className="space-y-2">
              {data.recent_form.map((r: any, i: number) => (
                <div key={i} className="flex items-center justify-between py-2 border-b border-f1-border last:border-0">
                  <div>
                    <p className="text-sm font-medium text-white">{r.grand_prix_name}</p>
                    <p className="text-xs text-white/40">{r.season} R{r.round_number}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-white/40">Grid: P{r.grid_position}</span>
                    <span className={`font-bold text-sm ${r.finish_position <= 3 ? 'text-f1-gold' : 'text-white'}`}>
                      P{r.finish_position}
                    </span>
                    {r.dnf && <span className="badge badge-red text-[10px]">DNF</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      )}

      {!data && !isLoading && (
        <div className="card flex flex-col items-center py-16 text-center">
          <Users className="w-12 h-12 text-white/10 mb-3" />
          <p className="text-white/40">Enter a driver code and press Enter or Search</p>
        </div>
      )}
    </div>
  )
}

export default function DriverComparison() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-3xl font-display font-black text-white flex items-center gap-3">
          <Users className="w-8 h-8 text-f1-red" />
          Driver Comparison
        </h1>
        <p className="text-white/50 mt-1">Advanced driver analytics with consistency, overtaking efficiency, and racecraft scores</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <DriverPanel driverCode="VER" color="#E10600" />
        <DriverPanel driverCode="NOR" color="#27F4D2" />
      </div>
    </div>
  )
}
