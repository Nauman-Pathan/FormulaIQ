import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { Trophy, Activity, Zap, Users, TrendingUp, Flag, Clock, AlertTriangle } from 'lucide-react'
import { getRaces, getDrivers } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

const TEAM_COLORS: Record<string, string> = {
  'Red Bull Racing': '#3671C6',
  'Ferrari': '#E8002D',
  'Mercedes': '#27F4D2',
  'McLaren': '#FF8000',
  'Aston Martin': '#358C75',
  'Alpine': '#FF87BC',
  'Williams': '#64C4FF',
  'Haas': '#B6BABD',
  'Kick Sauber': '#52E252',
  'RB': '#6692FF',
}

const statCards = [
  { label: 'Races Analyzed', value: '1,200+', icon: Flag, color: 'text-f1-red' },
  { label: 'Drivers Tracked', value: '140+', icon: Users, color: 'text-blue-400' },
  { label: 'Prediction Accuracy', value: '84.2%', icon: TrendingUp, color: 'text-emerald-400' },
  { label: 'Telemetry Points', value: '52M+', icon: Activity, color: 'text-purple-400' },
]

export default function Dashboard() {
  const { data: races, isLoading: racesLoading } = useQuery({
    queryKey: ['races', 2026],
    queryFn: () => getRaces(2026),
  })

  const { data: drivers } = useQuery({
    queryKey: ['drivers', 2026],
    queryFn: () => getDrivers(2026),
  })

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-f1-red/20 via-f1-panel to-f1-carbon border border-f1-red/20 p-8">
        <div className="absolute inset-0 bg-radial-glow pointer-events-none" />
        <div className="relative z-10">
          <div className="flex items-center gap-2 mb-3">
            <span className="badge badge-red text-[10px] uppercase tracking-widest">AI-Powered</span>
            <span className="text-white/30 text-xs">•</span>
            <span className="text-white/40 text-xs font-mono">2026 F1 Season</span>
          </div>
          <h1 className="text-4xl font-display font-black text-white leading-tight mb-2">
            Formula<span className="gradient-text">IQ</span>
          </h1>
          <p className="text-white/60 text-lg max-w-xl">
            Race outcome predictions, telemetry comparisons, and strategy simulation — all powered by XGBoost and FastF1.
          </p>
          <div className="flex gap-3 mt-6">
            <a href="/predict" className="btn-primary">
              <Zap className="w-4 h-4" /> Predict Next Race
            </a>
            <a href="/telemetry" className="btn-secondary">
              <Activity className="w-4 h-4" /> Telemetry Analysis
            </a>
          </div>
        </div>
        {/* Decorative F1 track curve */}
        <svg className="absolute right-0 bottom-0 w-72 h-48 opacity-10" viewBox="0 0 300 200">
          <path d="M300,200 Q200,100 100,150 Q0,200 0,100 Q0,0 150,50 Q300,100 300,200" fill="none" stroke="#E10600" strokeWidth="3"/>
        </svg>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map(({ label, value, icon: Icon, color }, i) => (
          <motion.div
            key={label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08 }}
            className="card-glow"
          >
            <Icon className={`w-5 h-5 ${color} mb-3`} />
            <div className="metric-value">{value}</div>
            <div className="metric-label">{label}</div>
          </motion.div>
        ))}
      </div>

      {/* 2026 Race Calendar */}
      <div className="card">
        <div className="flex items-center justify-between mb-5">
          <h2 className="section-title">
            <Flag className="w-5 h-5 text-f1-red" />
            2026 Race Calendar
          </h2>
          <span className="badge badge-blue">{races?.length || 0} Rounds</span>
        </div>

        {racesLoading ? (
          <LoadingSpinner />
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
            {races?.slice(0, 15).map((race: any, i: number) => (
              <motion.div
                key={race.id}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.04 }}
                className="table-row flex items-center justify-between py-3 px-2 rounded-lg"
              >
                <div className="flex items-center gap-4">
                  <span className="w-7 h-7 rounded-lg bg-f1-carbon flex items-center justify-center text-xs font-mono font-bold text-white/60">
                    {race.round_number}
                  </span>
                  <div>
                    <p className="text-sm font-semibold text-white">{race.grand_prix_name}</p>
                    <p className="text-xs text-white/40 font-mono">{race.race_date}</p>
                  </div>
                </div>
                <div>
                  {race.session_status === 'completed' ? (
                    <span className="badge badge-green">Completed</span>
                  ) : (
                    <span className="badge badge-yellow">Upcoming</span>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { title: 'Race Predictor', desc: 'AI-powered finishing position predictions with probability scores', href: '/predict', icon: Brain, color: 'from-f1-red/20 to-transparent' },
          { title: 'Telemetry Comparison', desc: 'Compare speed, throttle, DRS traces between any two drivers', href: '/telemetry', icon: Activity, color: 'from-blue-500/15 to-transparent' },
          { title: 'Strategy Simulator', desc: 'Optimize pit stop timing and tyre compound selection', href: '/strategy', icon: GitFork, color: 'from-purple-500/15 to-transparent' },
        ].map(({ title, desc, href, icon: Icon, color }) => (
          <a
            key={href}
            href={href}
            className={`card-glow bg-gradient-to-br ${color} hover:scale-[1.02] active:scale-[0.99] block`}
          >
            <Icon className="w-6 h-6 text-white/70 mb-3" />
            <h3 className="font-display font-bold text-white mb-1">{title}</h3>
            <p className="text-sm text-white/50">{desc}</p>
          </a>
        ))}
      </div>
    </div>
  )
}

// Fix missing imports referenced inside
function Brain(props: any) { return <svg {...props} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.46 2.5 2.5 0 0 1-1.98-3 2.5 2.5 0 0 1-1.32-4.24 3 3 0 0 1 .34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 4.1-2.48Z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.46 2.5 2.5 0 0 0 1.98-3 2.5 2.5 0 0 0 1.32-4.24 3 3 0 0 0-.34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-4.1-2.48Z"/></svg> }
function GitFork(props: any) { return <svg {...props} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><circle cx="18" cy="6" r="3"/><path d="M18 9v2c0 .6-.4 1-1 1H7c-.6 0-1-.4-1-1V9"/><path d="M12 12v3"/></svg> }
