import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import Dashboard from './Dashboard'
import * as api from '../services/api'

// Mock the API service functions
vi.mock('../services/api', () => ({
  getRaces: vi.fn(),
  getDrivers: vi.fn(),
}))

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

describe('Dashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading spinner initially', () => {
    // Make api calls pending/resolving late
    vi.mocked(api.getRaces).mockReturnValue(new Promise(() => {}))
    vi.mocked(api.getDrivers).mockReturnValue(new Promise(() => {}))

    const queryClient = createTestQueryClient()
    render(
      <QueryClientProvider client={queryClient}>
        <Dashboard />
      </QueryClientProvider>
    )

    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('renders hero title and stats cards after data loads', async () => {
    const mockRaces = [
      { id: 1, round_number: 1, grand_prix_name: 'Bahrain Grand Prix', race_date: '2026-03-05', session_status: 'completed' },
      { id: 2, round_number: 2, grand_prix_name: 'Saudi Arabian Grand Prix', race_date: '2026-03-19', session_status: 'upcoming' },
    ]
    const mockDrivers = [{ id: 1, driver_code: 'VER', full_name: 'Max Verstappen' }]

    vi.mocked(api.getRaces).mockResolvedValue(mockRaces)
    vi.mocked(api.getDrivers).mockResolvedValue(mockDrivers)

    const queryClient = createTestQueryClient()
    render(
      <QueryClientProvider client={queryClient}>
        <Dashboard />
      </QueryClientProvider>
    )

    // Wait for the calendar data to render
    expect(await screen.findByText('Bahrain Grand Prix')).toBeInTheDocument()

    // Verify Title and Hero elements
    expect(screen.getByText('Formula')).toBeInTheDocument()
    expect(screen.getByText('IQ')).toBeInTheDocument()
    expect(screen.getByText('2026 F1 Season')).toBeInTheDocument()

    // Verify Quick stats metrics
    expect(screen.getByText('Races Analyzed')).toBeInTheDocument()
    expect(screen.getByText('1,200+')).toBeInTheDocument()
    expect(screen.getByText('Prediction Accuracy')).toBeInTheDocument()
    expect(screen.getByText('84.2%')).toBeInTheDocument()

    // Verify calendar contents
    expect(screen.getByText('Saudi Arabian Grand Prix')).toBeInTheDocument()
    expect(screen.getByText('2 Rounds')).toBeInTheDocument()
  })
})
