import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { GitFork, Play, AlertTriangle, CheckCircle2, Clock } from 'lucide-react'
import toast from 'react-hot-toast'
import { simulateStrategy } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

const COMPOUNDS = ['SOFT', 'MEDIUM', 'HARD', 'INTERMEDIATE', 'WET']
const COMPOUND_COLORS: Record<string, string> = {
  SOFT: '#FF3333', MEDIUM: '#FFDD44', HARD: '#DDDDDD',
  INTERMEDIATE: '#44CC44', WET: '#4488FF',
}
const COMPOUND_ABBR: Record<string, string> = {
  SOFT: 'S', MEDIUM: 'M', HARD: 'H', INTERMEDIATE: 'I', WET: 'W',
}

function TyreBadge({ compound }: { compound: string }) {
  return (
    <span
      className="inline-flex w-7 h-7 rounded-full items-center justify-center text-xs font-black shadow-md border border-white/10"
      style={{ background: COMPOUND_COLORS[compound] || '#666', color: compound === 'MEDIUM' || compound === 'HARD' ? '#111' : '#fff' }}
      title={compound}
    >
      {COMPOUND_ABBR[compound] || '?'}
    </span>
  )
}

function DegBar({ pct }: { pct: number }) {
  const color = pct > 80 ? '#E10600' : pct > 60 ? '#F59E0B' : '#10B981'
  return (
    <div className="relative h-3 bg-f1-carbon rounded-full overflow-hidden w-full">
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${pct}%` }}
        transition={{ duration: 0.8, ease: 'easeOut' }}
        className="h-full rounded-full"
        style={{ background: color }}
      />
      <span className="absolute right-1 top-1/2 -translate-y-1/2 text-[9px] font-mono text-white/60">
        {pct.toFixed(0)}%
      </span>
    </div>
  )
}

export default function StrategySimulator() {
  const [form, setForm] = useState({
    current_lap: 20,
    total_laps: 58,
    tyre_compound: 'MEDIUM',
    tyre_age_laps: 15,
    current_position: 5,
    weather_condition: 'dry',
    safety_car_probability: 0.15,
    pit_lane_loss_seconds: 20,
    degradation_rate: 0.08,
    circuit_type: 'permanent',
  })

  const mutation = useMutation({
    mutationFn: () => simulateStrategy(form),
    onError: (e: any) => toast.error(e.message || 'Simulation failed'),
  })

  const result = mutation.data
  const recommended = result?.recommended_strategy

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-display font-black text-white flex items-center gap-3">
          <GitFork className="w-8 h-8 text-f1-red" />
          Strategy Simulator
        </h1>
        <p className="text-white/50 mt-1">Rule-based pit stop optimizer with tyre degradation modelling</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Inputs */}
        <div className="card space-y-5">
          <h2 className="section-title"><Play className="w-4 h-4 text-f1-red" /> Race State</h2>

          <div className="grid grid-cols-2 gap-4">
            {[
              { key: 'current_lap', label: 'Current Lap', type: 'number', min: 1, max: 78 },
              { key: 'total_laps', label: 'Total Laps', type: 'number', min: 20, max: 78 },
              { key: 'tyre_age_laps', label: 'Tyre Age (laps)', type: 'number', min: 0, max: 50 },
              { key: 'current_position', label: 'Current Position', type: 'number', min: 1, max: 20 },
              { key: 'pit_lane_loss_seconds', label: 'Pit Loss (s)', type: 'number', min: 15, max: 35 },
              { key: 'degradation_rate', label: 'Deg Rate (s/lap)', type: 'number', step: '0.01', min: 0.01, max: 1 },
            ].map(({ key, label, ...inputProps }) => (
              <div key={key}>
                <label className="text-[10px] text-white/40 uppercase tracking-wider mb-1 block">{label}</label>
                <input
                  className="input-field"
                  {...inputProps}
                  value={(form as any)[key]}
                  onChange={e => setForm(f => ({ ...f, [key]: +e.target.value }))}
                />
              </div>
            ))}
          </div>

          {/* Tyre compound selector */}
          <div>
            <label className="text-[10px] text-white/40 uppercase tracking-wider mb-2 block">Current Tyre</label>
            <div className="flex gap-2">
              {COMPOUNDS.map(c => (
                <button
                  key={c}
                  onClick={() => setForm(f => ({ ...f, tyre_compound: c }))}
                  className={`flex flex-col items-center gap-1 p-2 rounded-xl border transition-all ${form.tyre_compound === c ? 'border-white/30 bg-white/10' : 'border-f1-border hover:border-white/15'}`}
                >
                  <TyreBadge compound={c} />
                  <span className="text-[9px] text-white/40">{c.slice(0, 3)}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Weather */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-[10px] text-white/40 uppercase tracking-wider mb-1 block">Weather</label>
              <select className="select-field" value={form.weather_condition} onChange={e => setForm(f => ({ ...f, weather_condition: e.target.value }))}>
                <option value="dry">☀️ Dry</option>
                <option value="mixed">🌦️ Mixed</option>
                <option value="wet">🌧️ Wet</option>
              </select>
            </div>
            <div>
              <label className="text-[10px] text-white/40 uppercase tracking-wider mb-1 block">Safety Car Prob.</label>
              <div className="flex items-center gap-2">
                <input
                  type="range" min={0} max={1} step={0.05}
                  className="flex-1 accent-f1-red"
                  value={form.safety_car_probability}
                  onChange={e => setForm(f => ({ ...f, safety_car_probability: +e.target.value }))}
                />
                <span className="text-sm font-mono text-white/70 w-10 text-right">
                  {(form.safety_car_probability * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>

          <button onClick={() => mutation.mutate()} disabled={mutation.isPending} className="btn-primary w-full justify-center py-3">
            {mutation.isPending ? <><span className="animate-spin">⚡</span> Simulating...</> : <><Play className="w-4 h-4" /> Run Simulation</>}
          </button>
        </div>

        {/* Results */}
        <div className="space-y-4">
          <h2 className="section-title"><CheckCircle2 className="w-4 h-4 text-emerald-400" /> Strategy Recommendation</h2>

          {mutation.isPending && <LoadingSpinner />}

          {result && (
            <AnimatePresence>
              <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
                {/* Tyre degradation */}
                <div className="card">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm text-white/60">Tyre Degradation</span>
                    <TyreBadge compound={form.tyre_compound} />
                  </div>
                  <DegBar pct={result.current_tyre_degradation_pct} />
                  <div className="flex justify-between mt-2 text-xs text-white/40">
                    <span>Pit window opens in {result.laps_to_pit_window_open} laps</span>
                    <span>Closes in {result.laps_to_pit_window_close} laps</span>
                  </div>
                </div>

                {/* Recommended strategy */}
                {recommended && (
                  <div className="card glow-border">
                    <div className="flex items-center gap-2 mb-4">
                      <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                      <span className="font-bold text-white">Recommended</span>
                      <span className="badge badge-green ml-auto">{(recommended.confidence * 100).toFixed(0)}% conf.</span>
                    </div>
                    <div className="flex items-center gap-4 mb-4">
                      <TyreBadge compound={recommended.compound_in} />
                      <div className="h-px flex-1 bg-gradient-to-r from-white/20 to-f1-red" />
                      <div className="text-center">
                        <div className="text-2xl font-display font-black text-white">Lap {recommended.pit_lap}</div>
                        <div className="text-xs text-white/40">Box Box Box</div>
                      </div>
                      <div className="h-px flex-1 bg-gradient-to-l from-white/20 to-f1-red" />
                      <TyreBadge compound={recommended.compound_out} />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="bg-f1-carbon rounded-xl p-3 text-center">
                        <div className="text-xs text-white/40 mb-1">Position Impact</div>
                        <div className={`text-xl font-display font-bold ${recommended.position_gain_loss >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                          {recommended.position_gain_loss > 0 ? '+' : ''}{recommended.position_gain_loss.toFixed(1)} pos
                        </div>
                      </div>
                      <div className="bg-f1-carbon rounded-xl p-3 text-center">
                        <div className="text-xs text-white/40 mb-1">Strategy</div>
                        <div className="text-sm font-bold text-white">{recommended.strategy_name}</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Notes */}
                {result.notes && (
                  <div className="card border-amber-500/20 bg-amber-500/5">
                    <div className="flex gap-2">
                      <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                      <p className="text-sm text-amber-300/80">{result.notes}</p>
                    </div>
                  </div>
                )}

                {/* All strategies */}
                <div className="card">
                  <h3 className="section-title mb-3"><Clock className="w-4 h-4 text-blue-400" /> All Strategy Options</h3>
                  <div className="space-y-2">
                    {result.all_strategies?.map((s: any, i: number) => (
                      <div key={i} className={`flex items-center gap-3 py-2.5 px-3 rounded-xl border transition-all ${i === 0 ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-f1-border hover:border-white/10'}`}>
                        <span className="text-xs font-mono text-white/40 w-4">{i + 1}</span>
                        <div className="flex items-center gap-1.5">
                          <TyreBadge compound={s.compound_in} />
                          <span className="text-white/30 text-xs">→</span>
                          <TyreBadge compound={s.compound_out} />
                        </div>
                        <div className="flex-1">
                          <p className="text-xs font-medium text-white">{s.strategy_name}</p>
                          <p className="text-[10px] text-white/40">Lap {s.pit_lap}</p>
                        </div>
                        <div className="text-right">
                          <p className={`text-xs font-bold ${s.position_gain_loss >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            {s.position_gain_loss > 0 ? '+' : ''}{s.position_gain_loss.toFixed(1)} pos
                          </p>
                          <p className="text-[10px] text-white/30">{(s.confidence * 100).toFixed(0)}%</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            </AnimatePresence>
          )}

          {!result && !mutation.isPending && (
            <div className="card flex flex-col items-center py-16 text-center">
              <GitFork className="w-12 h-12 text-white/10 mb-3" />
              <p className="text-white/40">Configure race state and click<br />Run Simulation</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
