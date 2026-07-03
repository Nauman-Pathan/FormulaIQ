import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import RacePredictor from './pages/RacePredictor'
import TelemetryAnalyzer from './pages/TelemetryAnalyzer'
import DriverComparison from './pages/DriverComparison'
import StrategySimulator from './pages/StrategySimulator'
import HistoricalAnalytics from './pages/HistoricalAnalytics'
import AIStrategist from './pages/AIStrategist'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/predict" element={<RacePredictor />} />
        <Route path="/telemetry" element={<TelemetryAnalyzer />} />
        <Route path="/drivers" element={<DriverComparison />} />
        <Route path="/strategy" element={<StrategySimulator />} />
        <Route path="/rl-strategy" element={<AIStrategist />} />
        <Route path="/history" element={<HistoricalAnalytics />} />
      </Route>
    </Routes>
  )
}
