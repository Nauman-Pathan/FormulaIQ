import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import Plot from 'react-plotly.js'
import { Activity, Search, ChevronRight, Gauge, Zap } from 'lucide-react'
import toast from 'react-hot-toast'
import { getTelemetry } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

const PLOT_LAYOUT_BASE = {
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  font: { color: 'rgba(255,255,255,0.7)', family: 'Inter, sans-serif', size: 11 },
  margin: { l: 48, r: 16, t: 32, b: 40 },
  xaxis: { gridcolor: 'rgba(255,255,255,0.05)', zerolinecolor: 'rgba(255,255,255,0.1)' },
  yaxis: { gridcolor: 'rgba(255,255,255,0.05)', zerolinecolor: 'rgba(255,255,255,0.1)' },
  legend: { bgcolor: 'transparent', font: { color: 'rgba(255,255,255,0.6)' } },
  hovermode: 'x unified' as const,
}

const DRIVER_COLORS = ['#E10600', '#27F4D2']

export default function TelemetryAnalyzer() {
  const [year, setYear] = useState(2024)
  const [grandPrix, setGrandPrix] = useState('Abu Dhabi Grand Prix')
  const [driver1, setDriver1] = useState('HAM')
  const [driver2, setDriver2] = useState('RUS')
  const [lap, setLap] = useState<string>('')

  const mutation = useMutation({
    mutationFn: () => getTelemetry(year, grandPrix, driver1, driver2, lap ? +lap : undefined),
    onError: (e: any) => toast.error(e.message || 'Failed to load telemetry'),
  })

  const data = mutation.data
  const d1 = data?.driver1
  const d2 = data?.driver2

  const makeTrace = (
    label: string,
    yData: number[],
    color: string,
    xData?: number[],
    visible: boolean = true
  ) => ({
    x: xData || d1?.distance || [],
    y: yData,
    type: 'scatter' as const,
    mode: 'lines' as const,
    name: label,
    line: { color, width: 1.5 },
    visible: visible ? true : ('legendonly' as const),
  })

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-display font-black text-white flex items-center gap-3">
          <Activity className="w-8 h-8 text-f1-red" />
          Telemetry Analyzer
        </h1>
        <p className="text-white/50 mt-1">Compare speed, throttle, brake, gear and DRS traces between two drivers</p>
      </div>

      {/* Controls */}
      <div className="card grid grid-cols-2 md:grid-cols-5 gap-4">
        <div>
          <label className="text-[10px] text-white/40 uppercase tracking-wider mb-1 block">Season</label>
          <select className="select-field" value={year} onChange={e => setYear(+e.target.value)}>
            {[2022, 2023, 2024, 2025, 2026].map(y => <option key={y}>{y}</option>)}
          </select>
        </div>
        <div className="col-span-2 md:col-span-2">
          <label className="text-[10px] text-white/40 uppercase tracking-wider mb-1 block">Grand Prix</label>
          <input className="input-field" value={grandPrix} onChange={e => setGrandPrix(e.target.value)} placeholder="e.g. British Grand Prix" />
        </div>
        <div>
          <label className="text-[10px] text-white/40 uppercase tracking-wider mb-1 block">Driver 1 (Red)</label>
          <input className="input-field" value={driver1} onChange={e => setDriver1(e.target.value.toUpperCase())} placeholder="VER" maxLength={4} />
        </div>
        <div>
          <label className="text-[10px] text-white/40 uppercase tracking-wider mb-1 block">Driver 2 (Teal)</label>
          <input className="input-field" value={driver2} onChange={e => setDriver2(e.target.value.toUpperCase())} placeholder="NOR" maxLength={4} />
        </div>
        <div>
          <label className="text-[10px] text-white/40 uppercase tracking-wider mb-1 block">Lap (blank = fastest)</label>
          <input type="number" min={1} max={78} className="input-field" value={lap} onChange={e => setLap(e.target.value)} placeholder="Fastest" />
        </div>
        <div className="flex items-end">
          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className="btn-primary w-full justify-center"
          >
            {mutation.isPending ? <><span className="animate-spin">⚡</span>Loading</> : <><Search className="w-4 h-4" />Compare</>}
          </button>
        </div>
      </div>

      {mutation.isPending && <LoadingSpinner message="Fetching telemetry data from FastF1..." size="lg" />}

      {data && !mutation.isPending && (
        <>
          {/* Lap info chips */}
          <div className="flex flex-wrap gap-3">
            {[d1, d2].map((d, i) => d && (
              <div key={i} className="card-glow flex items-center gap-3 py-2 px-4">
                <div className="w-3 h-3 rounded-full" style={{ background: DRIVER_COLORS[i] }} />
                <span className="font-bold text-white text-sm">{d.driver_code}</span>
                <span className="badge badge-yellow font-mono">{d.compound}</span>
                <span className="font-mono text-white/60 text-sm">{d.lap_time_seconds?.toFixed(3)}s</span>
              </div>
            ))}
            {/* Sector comparison */}
            {data.sector_comparison && Object.entries(data.sector_comparison).map(([sector, info]: any) => (
              <div key={sector} className="card flex items-center gap-2 py-2 px-4">
                <span className="text-xs text-white/40">{sector.replace('Time', '')}</span>
                <span className={`text-xs font-bold ${info.fastest === driver1 ? 'text-f1-red' : 'text-[#27F4D2]'}`}>
                  {info.fastest} (+{Math.abs(info.delta).toFixed(3)}s)
                </span>
              </div>
            ))}
          </div>

          {/* Speed trace */}
          <div className="card">
            <h3 className="section-title mb-4"><Gauge className="w-4 h-4 text-f1-red" /> Speed (km/h)</h3>
            <Plot
              data={[
                makeTrace(d1.driver_code, d1.speed_kmh, DRIVER_COLORS[0], d1.distance),
                makeTrace(d2.driver_code, d2.speed_kmh, DRIVER_COLORS[1], d2.distance),
              ]}
              layout={{ ...PLOT_LAYOUT_BASE, yaxis: { ...PLOT_LAYOUT_BASE.yaxis, title: 'Speed (km/h)' }, xaxis: { ...PLOT_LAYOUT_BASE.xaxis, title: 'Distance (m)' } }}
              config={{ displayModeBar: false, responsive: true }}
              style={{ width: '100%', height: 260 }}
            />
          </div>

          {/* Throttle + Brake */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="card">
              <h3 className="section-title mb-4"><Zap className="w-4 h-4 text-emerald-400" /> Throttle (%)</h3>
              <Plot
                data={[
                  makeTrace(d1.driver_code, d1.throttle_pct, DRIVER_COLORS[0], d1.distance),
                  makeTrace(d2.driver_code, d2.throttle_pct, DRIVER_COLORS[1], d2.distance),
                ]}
                layout={{ ...PLOT_LAYOUT_BASE, yaxis: { ...PLOT_LAYOUT_BASE.yaxis, range: [0, 105] } }}
                config={{ displayModeBar: false, responsive: true }}
                style={{ width: '100%', height: 220 }}
              />
            </div>
            <div className="card">
              <h3 className="section-title mb-4"><span className="text-red-400">⬛</span> Gear</h3>
              <Plot
                data={[
                  makeTrace(d1.driver_code, d1.gear, DRIVER_COLORS[0], d1.distance),
                  makeTrace(d2.driver_code, d2.gear, DRIVER_COLORS[1], d2.distance),
                ]}
                layout={{ ...PLOT_LAYOUT_BASE, yaxis: { ...PLOT_LAYOUT_BASE.yaxis, dtick: 1, range: [0, 9] } }}
                config={{ displayModeBar: false, responsive: true }}
                style={{ width: '100%', height: 220 }}
              />
            </div>
          </div>

          {/* DRS */}
          <div className="card">
            <h3 className="section-title mb-4">DRS Usage</h3>
            <Plot
              data={[
                makeTrace(d1.driver_code, d1.drs, DRIVER_COLORS[0], d1.distance),
                makeTrace(d2.driver_code, d2.drs, DRIVER_COLORS[1], d2.distance),
              ]}
              layout={{ ...PLOT_LAYOUT_BASE, yaxis: { ...PLOT_LAYOUT_BASE.yaxis, range: [-1, 16] } }}
              config={{ displayModeBar: false, responsive: true }}
              style={{ width: '100%', height: 160 }}
            />
          </div>

          {/* Lap Delta */}
          {data.lap_delta?.length > 0 && (
            <div className="card">
              <h3 className="section-title mb-4">
                <ChevronRight className="w-4 h-4 text-purple-400" />
                Lap Delta Time (+ = {d2?.driver_code} ahead)
              </h3>
              <Plot
                data={[{
                  x: Array.from({ length: data.lap_delta.length }, (_, i) => i),
                  y: data.lap_delta,
                  type: 'scatter',
                  mode: 'lines',
                  fill: 'tozeroy',
                  line: { color: '#8B5CF6', width: 2 },
                  fillcolor: 'rgba(139,92,246,0.1)',
                  name: 'Delta',
                }]}
                layout={{ ...PLOT_LAYOUT_BASE, yaxis: { ...PLOT_LAYOUT_BASE.yaxis, title: 'Delta (s)' } }}
                config={{ displayModeBar: false, responsive: true }}
                style={{ width: '100%', height: 200 }}
              />
            </div>
          )}

          {/* Track Map */}
          {d1.x_pos?.length > 0 && (
            <div className="card">
              <h3 className="section-title mb-4">Track Map — Speed Overlay</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[d1, d2].map((d, i) => (
                  <Plot
                    key={i}
                    data={[{
                      x: d.x_pos,
                      y: d.y_pos,
                      type: 'scatter',
                      mode: 'markers',
                      marker: {
                        color: d.speed_kmh,
                        colorscale: 'RdYlGn',
                        size: 3,
                        showscale: i === 0,
                        colorbar: { title: 'Speed', thickness: 10, len: 0.8, tickfont: { color: 'rgba(255,255,255,0.5)' } },
                      },
                      name: d.driver_code,
                    }]}
                    layout={{
                      ...PLOT_LAYOUT_BASE,
                      title: { text: d.driver_code, font: { color: DRIVER_COLORS[i], size: 13 } },
                      xaxis: { ...PLOT_LAYOUT_BASE.xaxis, showticklabels: false },
                      yaxis: { ...PLOT_LAYOUT_BASE.yaxis, showticklabels: false, scaleanchor: 'x' },
                      margin: { l: 16, r: 16, t: 40, b: 16 },
                    }}
                    config={{ displayModeBar: false, responsive: true }}
                    style={{ width: '100%', height: 300 }}
                  />
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {!data && !mutation.isPending && (
        <div className="card flex flex-col items-center justify-center py-20 text-center">
          <Activity className="w-16 h-16 text-white/10 mb-4" />
          <p className="text-white/40 text-lg font-medium">Select year, GP and two drivers</p>
          <p className="text-white/25 text-sm mt-1">Click Compare to load telemetry from FastF1</p>
        </div>
      )}
    </div>
  )
}
