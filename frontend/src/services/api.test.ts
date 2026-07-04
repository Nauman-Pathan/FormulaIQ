import { vi, describe, it, expect, beforeEach } from 'vitest'

// Define the mock outside or directly inside vi.mock using vi.hoisted
const { mockGet, mockPost } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
}))

vi.mock('axios', () => {
  return {
    default: {
      create: vi.fn(() => ({
        get: mockGet,
        post: mockPost,
        interceptors: {
          request: { use: vi.fn(), eject: vi.fn() },
          response: { use: vi.fn(), eject: vi.fn() },
        },
      })),
    },
  }
})

import {
  getRaces,
  getDrivers,
  getTelemetry,
  predictRace,
  simulateStrategy,
} from './api'

describe('API Service functions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Setup standard mock returns
    mockGet.mockResolvedValue({ data: 'mock-response' })
    mockPost.mockResolvedValue({ data: 'mock-response' })
  })

  it('getRaces calls correct endpoint and query params', async () => {
    const res = await getRaces(2024)
    expect(mockGet).toHaveBeenCalledWith('/races', {
      params: { season: 2024 },
    })
    expect(res).toBe('mock-response')
  })

  it('getDrivers calls correct endpoint and query params', async () => {
    const res = await getDrivers(2025)
    expect(mockGet).toHaveBeenCalledWith('/drivers', {
      params: { season: 2025 },
    })
    expect(res).toBe('mock-response')
  })

  it('getTelemetry calls correct URL layout', async () => {
    const res = await getTelemetry(2024, 'British Grand Prix', 'VER', 'NOR', 12)
    expect(mockGet).toHaveBeenCalledWith(
      '/telemetry/2024/British%20Grand%20Prix/VER/NOR',
      { params: { lap: 12 } }
    )
    expect(res).toBe('mock-response')
  })

  it('predictRace makes POST request with correct payload', async () => {
    const payload = { year: 2026, drivers: [] }
    const res = await predictRace(payload)
    expect(mockPost).toHaveBeenCalledWith('/predict-race', payload)
    expect(res).toBe('mock-response')
  })

  it('simulateStrategy makes POST request with correct payload', async () => {
    const payload = { current_lap: 20, tyre_compound: 'MEDIUM' }
    const res = await simulateStrategy(payload)
    expect(mockPost).toHaveBeenCalledWith('/simulate-strategy', payload)
    expect(res).toBe('mock-response')
  })
})
