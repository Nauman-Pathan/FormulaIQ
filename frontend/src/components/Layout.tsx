import { NavLink, Outlet } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  LayoutDashboard, Brain, Activity, Users,
  GitFork, BarChart3, Zap, BrainCircuit
} from 'lucide-react'

const NAV_ITEMS = [
  { to: '/',          icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/predict',   icon: Brain,           label: 'Race Predictor' },
  { to: '/telemetry', icon: Activity,        label: 'Telemetry' },
  { to: '/drivers',   icon: Users,           label: 'Drivers' },
  { to: '/strategy',  icon: GitFork,         label: 'Strategy' },
  { to: '/rl-strategy', icon: BrainCircuit,  label: 'AI Strategist' },
  { to: '/history',   icon: BarChart3,       label: 'Historical' },
]

export default function Layout() {
  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 shrink-0 bg-f1-carbon border-r border-f1-border flex flex-col sticky top-0 h-screen z-40">
        {/* Logo */}
        <div className="p-5 border-b border-f1-border">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-f1-red rounded-xl flex items-center justify-center shadow-f1 animate-glow">
              <Zap className="w-5 h-5 text-white" fill="white" />
            </div>
            <div>
              <span className="font-display font-black text-xl text-white tracking-tight">FormulaIQ</span>
              <p className="text-[10px] text-white/40 uppercase tracking-widest">F1 Analytics</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) => isActive ? 'nav-link-active' : 'nav-link'}
            >
              <Icon className="w-4.5 h-4.5 shrink-0" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-f1-border">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs text-white/40">API Connected</span>
          </div>
          <p className="text-[10px] text-white/25 mt-1">Powered by FastF1 + XGBoost</p>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        {/* Top bar */}
        <header className="sticky top-0 z-30 glass border-b border-f1-border px-8 py-4 flex items-center justify-between">
          <div className="h-5 w-px bg-f1-border" />
          <div className="flex items-center gap-3">
            <span className="badge badge-red">LIVE</span>
            <span className="text-xs text-white/40 font-mono">2026 Season</span>
          </div>
        </header>

        {/* Page content */}
        <motion.div
          key={window.location.pathname}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, ease: 'easeOut' }}
          className="p-8"
        >
          <Outlet />
        </motion.div>
      </main>
    </div>
  )
}
