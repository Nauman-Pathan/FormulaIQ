import { useState, useEffect } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import Plot from 'react-plotly.js'
import {
  BrainCircuit, Play, Cpu, AlertTriangle, CheckCircle2,
  TrendingUp, BarChart3, RotateCcw, Activity
} from 'lucide-react'
import toast from 'react-hot-toast'
import {
  trainRLStrategy,
  getRLStrategyStatus,
  simulateRLStrategy,
  recommendRLStrategy
} from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

// Constants
const COMPOUNDS = ['Soft', 'Medium', 'Hard']
const COMPOUND_COLORS: Record<string, string> = {
  Soft: '#FF3333', Medium: '#FFDD44', Hard: '#DDDDDD',
  None: '#666666', Finish: '#E10600'
}

function TyreBadge({ compound }: { compound: string }) {
  const color = COMPOUND_COLORS[compound] || '#666'
  return (
    <span
      className="inline-flex w-7 h-7 rounded-full items-center justify-center text-xs font-black shadow-md border border-white/10"
      style={{
        background: color,
        color: compound === 'Medium' || compound === 'Hard' ? '#111' : '#fff'
      }}
      title={compound}
    >
      {compound ? compound[0] : '?'}
    </span>
  )
}

export default function AIStrategist() {
  // ── States ──────────────────────────────────────────────────────────────────
  const [activeTab, setActiveTab] = useState<'simulate' | 'recommend'>('simulate')
  
  // Setup Form (Simulation)
  const [simForm, setSimForm] = useState({
    total_laps: 50,
    starting_position: 10,
    track_temp: 35.0,
    weather: 'dry',
    track_type: 'permanent',
    safety_car_prob: 0.05,
  })

  // Live Recommendation Form
  const [recForm, setRecForm] = useState({
    current_lap: 20,
    total_laps: 50,
    tyre_compound: 'Medium',
    tyre_age: 12,
    tyre_degradation: 35.0,
    track_temp: 33.5,
    weather_condition: 'dry',
    safety_car_prob: 0.05,
    safety_car_active: false,
    competitor_avg_tyre_age: 10.0,
    competitor_pit_status: false,
    current_position: 10,
    lap_delta_ahead: 1.5,
    lap_delta_behind: 2.1,
    fuel_load: 60.0,
    track_type: 'permanent',
  })

  // ── API Queries/Mutations ───────────────────────────────────────────────────
  // Status check
  const { data: status, refetch: refetchStatus } = useQuery({
    queryKey: ['rlStrategyStatus'],
    queryFn: getRLStrategyStatus,
    refetchInterval: 5000, // Poll every 5s
  })

  // Train agent
  const trainMutation = useMutation({
    mutationFn: trainRLStrategy,
    onSuccess: () => {
      toast.success('RL Agent training triggered in background!')
      refetchStatus()
    },
    onError: (e: any) => toast.error(e.message || 'Failed to start training'),
  })

  // Run Simulation
  const simMutation = useMutation({
    mutationFn: simulateRLStrategy,
    onError: (e: any) => toast.error(e.message || 'Simulation failed'),
  })

  // Live Recommendation
  const recMutation = useMutation({
    mutationFn: recommendRLStrategy,
    onError: (e: any) => toast.error(e.message || 'Recommendation failed'),
  })

  // ── Plotly Helper ──────────────────────────────────────────────────────────
  const simHistory = simMutation.data || []
  
  // Extract simulation metrics for graphing
  const plotLaps = simHistory.map((h: any) => h.lap)
  const plotDegradation = simHistory.map((h: any) => h.tyre_degradation)
  const plotPosition = simHistory.map((h: any) => h.position)
  const plotConfidence = simHistory.map((h: any) => h.confidence * 100)
  
  // Custom marker colors/sizes based on compound pitted
  const plotMarkers = simHistory.map((h: any) => {
    if (h.action > 0) {
      return {
        color: COMPOUND_COLORS[h.action_name.replace('Pit for ', '')] || '#FF3333',
        size: 14,
        symbol: 'hexagon'
      }
    }
    return {
      color: 'rgba(255,255,255,0.05)',
      size: 0,
      symbol: 'circle'
    }
  })

  const PLOT_LAYOUT_BASE = {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { color: 'rgba(255,255,255,0.7)', family: 'Inter, sans-serif', size: 11 },
    margin: { l: 48, r: 16, t: 32, b: 40 },
    xaxis: { gridcolor: 'rgba(255,255,255,0.05)', zerolinecolor: 'rgba(255,255,255,0.1)', title: 'Lap' },
    yaxis: { gridcolor: 'rgba(255,255,255,0.05)', zerolinecolor: 'rgba(255,255,255,0.1)' },
    legend: { bgcolor: 'transparent', font: { color: 'rgba(255,255,255,0.6)' } },
    hovermode: 'x unified' as const,
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-display font-black text-white flex items-center gap-3">
            <BrainCircuit className="w-8 h-8 text-f1-red" />
            AI Strategy Engine
          </h1>
          <p className="text-white/50 mt-1">Deep Reinforcement Learning (PPO) strategist for optimal pitstop sequences</p>
        </div>

        {/* Model Training Box */}
        <div className="card flex items-center gap-4 py-3 px-5 border-f1-border bg-f1-carbon/50">
          <div className="flex items-center gap-2">
            <Cpu className={`w-4 h-4 ${status?.is_training ? 'text-amber-400 animate-spin' : 'text-f1-red'}`} />
            <span className="text-xs font-mono text-white/80">
              {status?.is_training ? 'Training Agent...' : status?.checkpoint_exists ? 'PPO Checkpoint Loaded' : 'No Checkpoint'}
            </span>
          </div>
          <button
            onClick={() => trainMutation.mutate()}
            disabled={status?.is_training || trainMutation.isPending}
            className="btn-primary py-1 px-3 text-xs justify-center"
          >
            {status?.is_training ? 'Training...' : 'Retrain Agent'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-f1-border pb-px">
        <button
          onClick={() => setActiveTab('simulate')}
          className={`pb-3 px-4 font-display font-bold text-sm tracking-wide border-b-2 transition-all ${
            activeTab === 'simulate' ? 'border-f1-red text-white' : 'border-transparent text-white/40 hover:text-white/60'
          }`}
        >
          Race Strategy Simulator
        </button>
        <button
          onClick={() => setActiveTab('recommend')}
          className={`pb-3 px-4 font-display font-bold text-sm tracking-wide border-b-2 transition-all ${
            activeTab === 'recommend' ? 'border-f1-red text-white' : 'border-transparent text-white/40 hover:text-white/60'
          }`}
        >
          Live Strategy Advice
        </button>
      </div>

      <AnimatePresence mode="wait">
        {activeTab === 'simulate' ? (
          <motion.div
            key="simulate"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            className="grid grid-cols-1 xl:grid-cols-3 gap-6"
          >
            {/* Inputs Form */}
            <div className="card space-y-5 h-fit">
              <h2 className="section-title"><Play className="w-4 h-4 text-f1-red" /> Race Parameters</h2>
              
              <div className="space-y-4">
                {[
                  { key: 'total_laps', label: 'Total Laps', type: 'number', min: 10, max: 80 },
                  { key: 'starting_position', label: 'Starting Position', type: 'number', min: 1, max: 20 },
                  { key: 'track_temp', label: 'Track Temp (°C)', type: 'number', min: 15, max: 55 },
                ].map(({ key, label, ...inputProps }) => (
                  <div key={key}>
                    <label className="text-[10px] text-white/40 uppercase tracking-wider mb-1 block">{label}</label>
                    <input
                      className="input-field"
                      {...inputProps}
                      value={(simForm as any)[key]}
                      onChange={e => setSimForm(f => ({ ...f, [key]: +e.target.value }))}
                    />
                  </div>
                ))}

                <div>
                  <label className="text-[10px] text-white/40 uppercase tracking-wider mb-1 block">Weather Condition</label>
                  <select
                    className="select-field"
                    value={simForm.weather}
                    onChange={e => setSimForm(f => ({ ...f, weather: e.target.value }))}
                  >
                    <option value="dry">☀️ Dry</option>
                    <option value="rain">🌧️ Rain / Wet</option>
                  </select>
                </div>

                <div>
                  <label className="text-[10px] text-white/40 uppercase tracking-wider mb-1 block">Track Layout Type</label>
                  <select
                    className="select-field"
                    value={simForm.track_type}
                    onChange={e => setSimForm(f => ({ ...f, track_type: e.target.value }))}
                  >
                    <option value="permanent">🏎️ Permanent Circuit</option>
                    <option value="street">🏙️ Street Circuit</option>
                  </select>
                </div>

                <div>
                  <label className="text-[10px] text-white/40 uppercase tracking-wider mb-1 block">Safety Car Prob.</label>
                  <div className="flex items-center gap-3">
                    <input
                      type="range"
                      min={0}
                      max={0.5}
                      step={0.01}
                      className="flex-1 accent-f1-red"
                      value={simForm.safety_car_prob}
                      onChange={e => setSimForm(f => ({ ...f, safety_car_prob: +e.target.value }))}
                    />
                    <span className="text-sm font-mono text-white/70 w-12 text-right">
                      {(simForm.safety_car_prob * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>

              <button
                onClick={() => simMutation.mutate(simForm)}
                disabled={simMutation.isPending}
                className="btn-primary w-full justify-center py-3"
              >
                {simMutation.isPending ? <><span className="animate-spin mr-2">⚡</span>Simulating...</> : <><Play className="w-4 h-4 mr-2" />Run RL Simulation</>}
              </button>
            </div>

            {/* Results Charts */}
            <div className="xl:col-span-2 space-y-6">
              {simMutation.isPending && <LoadingSpinner message="Simulating full race strategy using PPO agent..." size="lg" />}

              {simHistory.length > 0 && !simMutation.isPending && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
                  {/* Simulation Stats Overview */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="card p-4 text-center">
                      <div className="text-xs text-white/40 mb-1">Starting Position</div>
                      <div className="text-2xl font-display font-black text-white">P{simForm.starting_position}</div>
                    </div>
                    <div className="card p-4 text-center">
                      <div className="text-xs text-white/40 mb-1">Predicted Finish</div>
                      <div className="text-2xl font-display font-black text-f1-red">
                        P{simHistory[simHistory.length - 1]?.position || simForm.starting_position}
                      </div>
                    </div>
                    <div className="card p-4 text-center">
                      <div className="text-xs text-white/40 mb-1">Net Gain/Loss</div>
                      <div className={`text-2xl font-display font-black ${
                        simForm.starting_position - (simHistory[simHistory.length - 1]?.position || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'
                      }`}>
                        {simForm.starting_position - (simHistory[simHistory.length - 1]?.position || 0) > 0 ? '+' : ''}
                        {simForm.starting_position - (simHistory[simHistory.length - 1]?.position || 0)} pos
                      </div>
                    </div>
                    <div className="card p-4 text-center">
                      <div className="text-xs text-white/40 mb-1">Pitstops Taken</div>
                      <div className="text-2xl font-display font-black text-white">
                        {simHistory.filter((h: any) => h.action > 0).length} Stops
                      </div>
                    </div>
                  </div>

                  {/* Pit Stints Visual Timeline */}
                  <div className="card">
                    <h3 className="section-title mb-4"><Activity className="w-4 h-4 text-f1-red" /> Optimal Stint Timeline</h3>
                    <div className="relative h-12 bg-f1-carbon/50 rounded-xl overflow-hidden flex border border-white/5">
                      {simHistory.map((h: any, idx: number) => {
                        if (idx === simHistory.length - 1) return null
                        // Determine segment width (each lap is 1/total_laps)
                        const widthPct = (1 / simForm.total_laps) * 100
                        return (
                          <div
                            key={idx}
                            style={{
                              width: `${widthPct}%`,
                              backgroundColor: COMPOUND_COLORS[h.tyre_compound] || '#666'
                            }}
                            title={`Lap ${h.lap}: Compound ${h.tyre_compound}, Degradation: ${h.tyre_degradation.toFixed(0)}%`}
                            className="h-full border-r border-black/10 hover:brightness-125 transition-all cursor-pointer relative group"
                          >
                            {/* Render stint labels on hover or start of segments */}
                            {(idx === 0 || simHistory[idx - 1]?.tyre_compound !== h.tyre_compound) && (
                              <span className="absolute left-1 top-1/2 -translate-y-1/2 text-[9px] font-black text-black select-none pointer-events-none">
                                {h.tyre_compound[0]}{h.lap}
                              </span>
                            )}
                          </div>
                        )
                      })}
                    </div>
                    <div className="flex gap-4 mt-3 text-xs justify-center">
                      {COMPOUNDS.map(c => (
                        <div key={c} className="flex items-center gap-1.5">
                          <span className="w-3 h-3 rounded-full" style={{ backgroundColor: COMPOUND_COLORS[c] }} />
                          <span className="text-white/60">{c}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Degradation Chart */}
                  <div className="card">
                    <h3 className="section-title mb-2"><BarChart3 className="w-4 h-4 text-f1-red" /> Tyre Wear Profile (%)</h3>
                    <Plot
                      data={[{
                        x: plotLaps,
                        y: plotDegradation,
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Wear %',
                        line: { color: '#E10600', width: 2 },
                        fill: 'tozeroy',
                        fillcolor: 'rgba(225,6,0,0.05)',
                      }]}
                      layout={{
                        ...PLOT_LAYOUT_BASE,
                        yaxis: { ...PLOT_LAYOUT_BASE.yaxis, range: [0, 100], title: 'Degradation (%)' },
                      }}
                      config={{ displayModeBar: false, responsive: true }}
                      style={{ width: '100%', height: 220 }}
                    />
                  </div>

                  {/* Position Tracker Chart */}
                  <div className="card">
                    <h3 className="section-title mb-2"><TrendingUp className="w-4 h-4 text-emerald-400" /> Race Position Progression</h3>
                    <Plot
                      data={[
                        {
                          x: plotLaps,
                          y: plotPosition,
                          type: 'scatter',
                          mode: 'lines+markers',
                          name: 'Position',
                          line: { color: '#10B981', width: 2 },
                          marker: {
                            color: plotMarkers.map((m: any) => m.color),
                            size: plotMarkers.map((m: any) => m.size),
                            symbol: plotMarkers.map((m: any) => m.symbol),
                          }
                        }
                      ]}
                      layout={{
                        ...PLOT_LAYOUT_BASE,
                        yaxis: {
                          ...PLOT_LAYOUT_BASE.yaxis,
                          autorange: 'reversed' as const,
                          dtick: 1,
                          title: 'Race Position (P1 - P20)'
                        },
                      }}
                      config={{ displayModeBar: false, responsive: true }}
                      style={{ width: '100%', height: 240 }}
                    />
                  </div>

                  {/* Simulation Log Table */}
                  <div className="card">
                    <h3 className="section-title mb-3">Lap-by-Lap Strategy Log</h3>
                    <div className="max-h-60 overflow-y-auto border border-white/5 rounded-xl">
                      <table className="w-full text-left text-xs text-white/70">
                        <thead className="bg-f1-carbon sticky top-0 font-mono text-[10px] text-white/40 uppercase">
                          <tr>
                            <th className="p-3">Lap</th>
                            <th className="p-3">Current Tyre</th>
                            <th className="p-3">Age</th>
                            <th className="p-3">Degradation</th>
                            <th className="p-3">Position</th>
                            <th className="p-3">Action Recommendation</th>
                            <th className="p-3">Confidence</th>
                          </tr>
                        </thead>
                        <tbody>
                          {simHistory.map((h: any, i: number) => (
                            <tr key={i} className="border-t border-white/5 hover:bg-white/5">
                              <td className="p-3 font-mono">{h.lap}</td>
                              <td className="p-3 flex items-center gap-1.5">
                                <TyreBadge compound={h.tyre_compound} />
                              </td>
                              <td className="p-3 font-mono">{h.tyre_age} laps</td>
                              <td className="p-3 font-mono">{h.tyre_degradation.toFixed(1)}%</td>
                              <td className="p-3 font-mono font-bold text-white">P{h.position}</td>
                              <td className="p-3">
                                <span className={`badge ${
                                  h.action > 0 ? 'badge-red font-bold' : 'bg-transparent text-white/50'
                                }`}>
                                  {h.action_name}
                                </span>
                              </td>
                              <td className="p-3 font-mono">{(h.confidence * 100).toFixed(0)}%</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </motion.div>
              )}

              {simHistory.length === 0 && !simMutation.isPending && (
                <div className="card flex flex-col items-center justify-center py-24 text-center">
                  <BrainCircuit className="w-16 h-16 text-white/10 mb-4" />
                  <h3 className="text-lg font-bold text-white mb-1">No Simulation Active</h3>
                  <p className="text-white/40 text-sm max-w-xs">Configure your race parameters and run the Deep RL simulation.</p>
                </div>
              )}
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="recommend"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            className="grid grid-cols-1 xl:grid-cols-3 gap-6"
          >
            {/* Live Setup Inputs */}
            <div className="card space-y-4 h-fit xl:col-span-1">
              <h2 className="section-title"><Cpu className="w-4 h-4 text-f1-red" /> Current Race Situation</h2>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] text-white/40 uppercase tracking-wider mb-1 block">Current Lap</label>
                  <input
                    type="number"
                    className="input-field"
                    value={recForm.current_lap}
                    onChange={e => setRecForm(f => ({ ...f, current_lap: +e.target.value }))}
                  />
                </div>
                <div>
                  <label className="text-[10px] text-white/40 uppercase tracking-wider mb-1 block">Total Laps</label>
                  <input
                    type="number"
                    className="input-field"
                    value={recForm.total_laps}
                    onChange={e => setRecForm(f => ({ ...f, total_laps: +e.target.value }))}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] text-white/40 uppercase tracking-wider mb-1 block">Current Position</label>
                  <input
                    type="number"
                    className="input-field"
                    value={recForm.current_position}
                    onChange={e => setRecForm(f => ({ ...f, current_position: +e.target.value }))}
                  />
                </div>
                <div>
                  <label className="text-[10px] text-white/40 uppercase tracking-wider mb-1 block">Tyre Age</label>
                  <input
                    type="number"
                    className="input-field"
                    value={recForm.tyre_age}
                    onChange={e => setRecForm(f => ({ ...f, tyre_age: +e.target.value }))}
                  />
                </div>
              </div>

              <div>
                <label className="text-[10px] text-white/40 uppercase tracking-wider mb-2 block">Tyre Compound</label>
                <div className="flex gap-2">
                  {COMPOUNDS.map(c => (
                    <button
                      key={c}
                      onClick={() => setRecForm(f => ({ ...f, tyre_compound: c }))}
                      className={`flex flex-col items-center gap-1 p-2 rounded-xl border flex-1 transition-all ${
                        recForm.tyre_compound === c ? 'border-white/30 bg-white/10' : 'border-f1-border hover:border-white/15'
                      }`}
                    >
                      <TyreBadge compound={c} />
                      <span className="text-[9px] text-white/40 mt-1">{c}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-[10px] text-white/40 uppercase tracking-wider mb-1 block">Tyre Wear / Degradation</label>
                <div className="flex items-center gap-3">
                  <input
                    type="range"
                    min={0}
                    max={100}
                    className="flex-1 accent-f1-red"
                    value={recForm.tyre_degradation}
                    onChange={e => setRecForm(f => ({ ...f, tyre_degradation: +e.target.value }))}
                  />
                  <span className="text-sm font-mono text-white/70 w-12 text-right">
                    {recForm.tyre_degradation.toFixed(0)}%
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] text-white/40 uppercase tracking-wider mb-1 block">Track Temp</label>
                  <input
                    type="number"
                    className="input-field"
                    value={recForm.track_temp}
                    onChange={e => setRecForm(f => ({ ...f, track_temp: +e.target.value }))}
                  />
                </div>
                <div>
                  <label className="text-[10px] text-white/40 uppercase tracking-wider mb-1 block">Weather</label>
                  <select
                    className="select-field"
                    value={recForm.weather_condition}
                    onChange={e => setRecForm(f => ({ ...f, weather_condition: e.target.value }))}
                  >
                    <option value="dry">☀️ Dry</option>
                    <option value="rain">🌧️ Rain</option>
                  </select>
                </div>
              </div>

              {/* Safety Car active / competitors */}
              <div className="space-y-2 border-t border-white/5 pt-3">
                <label className="flex items-center gap-2 cursor-pointer text-xs text-white/70">
                  <input
                    type="checkbox"
                    checked={recForm.safety_car_active}
                    onChange={e => setRecForm(f => ({ ...f, safety_car_active: e.target.checked }))}
                    className="rounded bg-f1-carbon border-f1-border text-f1-red focus:ring-0"
                  />
                  <span>🚨 Safety Car / VSC Active</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer text-xs text-white/70">
                  <input
                    type="checkbox"
                    checked={recForm.competitor_pit_status}
                    onChange={e => setRecForm(f => ({ ...f, competitor_pit_status: e.target.checked }))}
                    className="rounded bg-f1-carbon border-f1-border text-f1-red focus:ring-0"
                  />
                  <span>🏎️ Competitor pitting this lap</span>
                </label>
              </div>

              <button
                onClick={() => recMutation.mutate(recForm)}
                disabled={recMutation.isPending}
                className="btn-primary w-full justify-center py-3"
              >
                {recMutation.isPending ? <><span className="animate-spin mr-2">⚡</span>Querying...</> : 'Get AI Recommendation'}
              </button>
            </div>

            {/* Recommendation Outputs */}
            <div className="xl:col-span-2 space-y-6">
              {recMutation.isPending && <LoadingSpinner message="Calculating reinforcement learning recommendation..." />}

              {recMutation.data && !recMutation.isPending && (
                <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
                  {/* Recommended Action Card */}
                  <div className="card glow-border bg-gradient-to-r from-f1-carbon/80 to-f1-red/10 border-f1-red/30">
                    <div className="flex items-center gap-2 mb-4">
                      <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                      <span className="font-bold text-white uppercase tracking-wider text-sm">Recommended Action</span>
                      <span className="badge badge-red ml-auto font-mono">PPO AI</span>
                    </div>

                    <div className="flex items-center justify-between gap-6 mb-6">
                      <div>
                        <div className="text-4xl font-display font-black text-white tracking-tight">
                          {recMutation.data.recommended_action}
                        </div>
                        <p className="text-xs text-white/40 mt-1 uppercase tracking-widest">Recommended Decision</p>
                      </div>
                      
                      {recMutation.data.action_id > 0 && (
                        <div className="flex items-center gap-3 bg-f1-carbon/50 p-3 rounded-xl border border-white/5">
                          <span className="text-[10px] text-white/40 uppercase">Compound:</span>
                          <TyreBadge compound={recMutation.data.recommended_action.replace('Pit for ', '')} />
                        </div>
                      )}
                    </div>

                    {/* Confidence bar */}
                    <div className="space-y-2">
                      <div className="flex justify-between text-xs font-mono text-white/50">
                        <span>Confidence Index</span>
                        <span>{(recMutation.data.confidence_score * 100).toFixed(0)}%</span>
                      </div>
                      <div className="h-2.5 bg-f1-carbon rounded-full overflow-hidden w-full border border-white/5">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${recMutation.data.confidence_score * 100}%` }}
                          transition={{ duration: 0.8 }}
                          className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 rounded-full"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Prediction Impact cards */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="card p-5">
                      <h3 className="text-xs text-white/40 uppercase tracking-wider mb-2">Predicted Finish Impact</h3>
                      <div className={`text-2xl font-display font-black flex items-center gap-2 ${
                        recMutation.data.predicted_finish_gain_loss >= 0 ? 'text-emerald-400' : 'text-red-400'
                      }`}>
                        {recMutation.data.predicted_finish_gain_loss > 0 ? '+' : ''}
                        {recMutation.data.predicted_finish_gain_loss} positions
                      </div>
                      <p className="text-[10px] text-white/30 mt-1">Expected net finish position shift compared to baseline</p>
                    </div>

                    <div className="card p-5">
                      <h3 className="text-xs text-white/40 uppercase tracking-wider mb-2">Strategy Explanation</h3>
                      <p className="text-sm text-white/70 leading-relaxed">
                        {recMutation.data.explanation}
                      </p>
                    </div>
                  </div>

                  {/* Fallback Comparison */}
                  <div className="card border-white/5 bg-white/2">
                    <div className="flex gap-2.5">
                      <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                      <div>
                        <h4 className="text-xs font-bold text-amber-300">Rule-Based Fallback Guardrail Active</h4>
                        <p className="text-xs text-white/40 mt-1">
                          RL policy probabilities are automatically constrained by technical strategy safety window rules to ensure safety stop recommendations and prevent illogical pit sequences.
                        </p>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}

              {!recMutation.data && !recMutation.isPending && (
                <div className="card flex flex-col items-center justify-center py-28 text-center">
                  <BrainCircuit className="w-16 h-16 text-white/10 mb-4" />
                  <h3 className="text-lg font-bold text-white mb-1">Awaiting Current Race State</h3>
                  <p className="text-white/40 text-sm max-w-xs">Fill in the current race state form on the left to fetch live AI strategy advice.</p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
