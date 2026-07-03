import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { Brain, Plus, Trash2, Zap, Trophy, AlertTriangle } from 'lucide-react'
import toast from 'react-hot-toast'
import { predictRace } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

const COMPOUNDS = ['SOFT', 'MEDIUM', 'HARD', 'INTERMEDIATE', 'WET']
const WEATHER_OPTIONS = [{ value: 0, label: '☀️ Dry' }, { value: 1, label: '🌦️ Mixed' }, { value: 2, label: '🌧️ Wet' }]

const defaultDriver = () => ({
  driver_code: '',
  driver_name: '',
  constructor: '',
  grid_position: 1,
  best_qualifying_time_seconds: 88.0,
  consistency_score: 75,
  avg_lap_time: 90.0,
  prev3_avg_finish: 5,
  cumulative_points: 50,
  num_pit_stops: 2,
  avg_pit_duration: 23,
  weather_code: 0,
  rainfall: 0,
  air_temp_avg: 25,
  track_temp_avg: 42,
  humidity_avg: 50,
  grid_delta: 0,
  laps_completed: 58,
})

const MEDAL_COLORS = ['text-f1-gold', 'text-f1-silver', 'text-f1-bronze']

export default function RacePredictor() {
  const [drivers, setDrivers] = useState([
    { ...defaultDriver(), driver_code: 'VER', driver_name: 'Max Verstappen', constructor: 'Red Bull Racing', grid_position: 1, prev3_avg_finish: 1.5, cumulative_points: 200 },
    { ...defaultDriver(), driver_code: 'NOR', driver_name: 'Lando Norris', constructor: 'McLaren', grid_position: 2, prev3_avg_finish: 2.8, cumulative_points: 150 },
    { ...defaultDriver(), driver_code: 'LEC', driver_name: 'Charles Leclerc', constructor: 'Ferrari', grid_position: 3, prev3_avg_finish: 4.0, cumulative_points: 120 },
  ])
  const [year, setYear] = useState(2026)
  const [grandPrix, setGrandPrix] = useState('British Grand Prix')

  const mutation = useMutation({
    mutationFn: predictRace,
    onSuccess: () => toast.success('Prediction complete!'),
    onError: (e: any) => toast.error(e.message || 'Prediction failed'),
  })

  const addDriver = () => {
    if (drivers.length >= 20) return
    setDrivers([...drivers, { ...defaultDriver(), grid_position: drivers.length + 1 }])
  }

  const removeDriver = (i: number) => setDrivers(drivers.filter((_, idx) => idx !== i))

  const updateDriver = (i: number, key: string, value: any) => {
    setDrivers(drivers.map((d, idx) => (idx === i ? { ...d, [key]: value } : d)))
  }

  const handlePredict = () => {
    if (drivers.length < 2) { toast.error('Add at least 2 drivers'); return }
    if (drivers.some(d => !d.driver_code)) { toast.error('All drivers need a code'); return }
    mutation.mutate({
      year,
      grand_prix: grandPrix,
      model_version: 'v1',
      drivers,
    })
  }

  const results = mutation.data?.predictions || []

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-display font-black text-white flex items-center gap-3">
          <Brain className="w-8 h-8 text-f1-red" />
          Race Predictor
        </h1>
        <p className="text-white/50 mt-1">XGBoost-powered finishing position predictions with probability scores</p>
      </div>

      {/* Race Info */}
      <div className="card grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="text-xs font-medium text-white/50 uppercase tracking-wider mb-1.5 block">Season</label>
          <select className="select-field" value={year} onChange={e => setYear(+e.target.value)}>
            {[2022, 2023, 2024, 2025, 2026].map(y => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs font-medium text-white/50 uppercase tracking-wider mb-1.5 block">Grand Prix</label>
          <input className="input-field" value={grandPrix} onChange={e => setGrandPrix(e.target.value)} placeholder="e.g. British Grand Prix" />
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Driver Inputs */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="section-title"><Zap className="w-4 h-4 text-f1-red" /> Driver Grid</h2>
            <button onClick={addDriver} className="btn-secondary text-sm py-1.5 px-3">
              <Plus className="w-3.5 h-3.5" /> Add Driver
            </button>
          </div>

          <div className="space-y-3 max-h-[600px] overflow-y-auto pr-1">
            <AnimatePresence>
              {drivers.map((driver, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -16 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 16 }}
                  className="card border-l-2 border-l-f1-red/40"
                >
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-mono font-bold text-white/80 text-sm">P{i + 1}</span>
                    <button onClick={() => removeDriver(i)} className="text-white/30 hover:text-red-400 transition-colors">
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <label className="text-[10px] text-white/40 uppercase">Code</label>
                      <input className="input-field mt-0.5 text-sm py-1.5" placeholder="VER" maxLength={4}
                        value={driver.driver_code} onChange={e => updateDriver(i, 'driver_code', e.target.value.toUpperCase())} />
                    </div>
                    <div>
                      <label className="text-[10px] text-white/40 uppercase">Grid Pos</label>
                      <input type="number" min={1} max={20} className="input-field mt-0.5 text-sm py-1.5"
                        value={driver.grid_position} onChange={e => updateDriver(i, 'grid_position', +e.target.value)} />
                    </div>
                    <div className="col-span-2">
                      <label className="text-[10px] text-white/40 uppercase">Driver Name</label>
                      <input className="input-field mt-0.5 text-sm py-1.5" placeholder="Max Verstappen"
                        value={driver.driver_name} onChange={e => updateDriver(i, 'driver_name', e.target.value)} />
                    </div>
                    <div>
                      <label className="text-[10px] text-white/40 uppercase">Q Time (s)</label>
                      <input type="number" step="0.001" className="input-field mt-0.5 text-sm py-1.5"
                        value={driver.best_qualifying_time_seconds} onChange={e => updateDriver(i, 'best_qualifying_time_seconds', +e.target.value)} />
                    </div>
                    <div>
                      <label className="text-[10px] text-white/40 uppercase">Prev 3 Avg Finish</label>
                      <input type="number" min={1} max={20} step="0.1" className="input-field mt-0.5 text-sm py-1.5"
                        value={driver.prev3_avg_finish} onChange={e => updateDriver(i, 'prev3_avg_finish', +e.target.value)} />
                    </div>
                    <div>
                      <label className="text-[10px] text-white/40 uppercase">Points</label>
                      <input type="number" min={0} className="input-field mt-0.5 text-sm py-1.5"
                        value={driver.cumulative_points} onChange={e => updateDriver(i, 'cumulative_points', +e.target.value)} />
                    </div>
                    <div>
                      <label className="text-[10px] text-white/40 uppercase">Weather</label>
                      <select className="select-field mt-0.5 text-sm py-1.5"
                        value={driver.weather_code} onChange={e => updateDriver(i, 'weather_code', +e.target.value)}>
                        {WEATHER_OPTIONS.map(w => <option key={w.value} value={w.value}>{w.label}</option>)}
                      </select>
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>

          <button onClick={handlePredict} disabled={mutation.isPending} className="btn-primary w-full justify-center py-3">
            {mutation.isPending ? <><span className="animate-spin mr-2">⚡</span>Predicting...</> : <><Zap className="w-4 h-4" /> Run Prediction</>}
          </button>
        </div>

        {/* Results */}
        <div className="space-y-4">
          <h2 className="section-title"><Trophy className="w-4 h-4 text-f1-gold" /> Prediction Results</h2>

          {mutation.isPending && <LoadingSpinner message="Running XGBoost model..." />}

          {mutation.isError && (
            <div className="card border-red-500/20 bg-red-500/5 flex items-center gap-3 text-red-400">
              <AlertTriangle className="w-5 h-5 shrink-0" />
              <p className="text-sm">{(mutation.error as any)?.message}</p>
            </div>
          )}

          {results.length > 0 && (
            <AnimatePresence>
              <div className="space-y-2">
                {results.map((r: any, i: number) => (
                  <motion.div
                    key={r.driver_code}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="card-glow flex items-center gap-4"
                  >
                    <span className={`text-2xl font-display font-black w-10 text-center ${MEDAL_COLORS[i] || 'text-white/60'}`}>
                      P{i + 1}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white">{r.driver_name || r.driver_code}</span>
                        <span className="badge badge-blue text-[10px]">{r.driver_code}</span>
                      </div>
                      <div className="flex gap-3 mt-1.5">
                        <div className="text-center">
                          <div className="text-xs text-white/40">Win</div>
                          <div className="text-sm font-mono font-bold text-f1-red">{(r.win_probability * 100).toFixed(1)}%</div>
                        </div>
                        <div className="text-center">
                          <div className="text-xs text-white/40">Podium</div>
                          <div className="text-sm font-mono font-bold text-f1-gold">{(r.podium_probability * 100).toFixed(1)}%</div>
                        </div>
                        <div className="text-center">
                          <div className="text-xs text-white/40">Top 10</div>
                          <div className="text-sm font-mono font-bold text-blue-400">{(r.top10_probability * 100).toFixed(1)}%</div>
                        </div>
                        <div className="text-center">
                          <div className="text-xs text-white/40">DNF</div>
                          <div className="text-sm font-mono font-bold text-red-500">{(r.dnf_probability * 100).toFixed(1)}%</div>
                        </div>
                      </div>
                    </div>
                    {/* Probability bar */}
                    <div className="w-20">
                      <div className="h-1.5 bg-f1-carbon rounded-full overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-f1-red to-orange-400 rounded-full transition-all duration-500"
                          style={{ width: `${r.win_probability * 100 * 3}%`, maxWidth: '100%' }} />
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </AnimatePresence>
          )}

          {!mutation.isPending && results.length === 0 && !mutation.isError && (
            <div className="card flex flex-col items-center justify-center py-16 text-center">
              <Brain className="w-12 h-12 text-white/10 mb-4" />
              <p className="text-white/40">Fill in driver data and click<br />"Run Prediction" to get results</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
