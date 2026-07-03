import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const message = err.response?.data?.detail || err.message || 'API Error'
    console.error('[FormulaIQ API Error]', message)
    return Promise.reject(new Error(message))
  }
)

// ── Races ────────────────────────────────────────────────────────────────────
export const getRaces = (season?: number) =>
  api.get('/races', { params: season ? { season } : {} }).then((r) => r.data)

export const getRaceResults = (raceId: number) =>
  api.get(`/races/${raceId}/results`).then((r) => r.data)

export const getHistoricalResults = (params: {
  driver_code?: string
  season?: number
  grand_prix?: string
  limit?: number
}) => api.get('/historical-results', { params }).then((r) => r.data)

// ── Drivers ───────────────────────────────────────────────────────────────────
export const getDrivers = (season?: number) =>
  api.get('/drivers', { params: season ? { season } : {} }).then((r) => r.data)

export const getDriverAnalysis = (driverCode: string, season?: number) =>
  api.get(`/driver-analysis/${driverCode}`, { params: season ? { season } : {} }).then((r) => r.data)

// ── Circuits ──────────────────────────────────────────────────────────────────
export const getCircuits = () => api.get('/circuits').then((r) => r.data)

// ── Telemetry ─────────────────────────────────────────────────────────────────
export const getTelemetry = (
  year: number,
  grandPrix: string,
  driver1: string,
  driver2: string,
  lap?: number
) =>
  api
    .get(`/telemetry/${year}/${encodeURIComponent(grandPrix)}/${driver1}/${driver2}`, {
      params: lap ? { lap } : {},
    })
    .then((r) => r.data)

// ── Prediction ────────────────────────────────────────────────────────────────
export const predictRace = (payload: any) =>
  api.post('/predict-race', payload).then((r) => r.data)

export const getPredictionMetadata = () =>
  api.get('/predict-race/metadata').then((r) => r.data)

// ── Strategy ──────────────────────────────────────────────────────────────────
export const simulateStrategy = (payload: any) =>
  api.post('/simulate-strategy', payload).then((r) => r.data)

// ── RL Strategy ───────────────────────────────────────────────────────────────
export const trainRLStrategy = () =>
  api.post('/rl-strategy/train').then((r) => r.data)

export const getRLStrategyStatus = () =>
  api.get('/rl-strategy/status').then((r) => r.data)

export const simulateRLStrategy = (payload: any) =>
  api.post('/rl-strategy/simulate', payload).then((r) => r.data)

export const recommendRLStrategy = (payload: any) =>
  api.post('/rl-strategy/recommend', payload).then((r) => r.data)

export default api

