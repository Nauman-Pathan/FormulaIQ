import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import RacePredictor from './RacePredictor'
import * as api from '../services/api'

// Mock api
vi.mock('../services/api', () => ({
  predictRace: vi.fn(),
  getPredictionMetadata: vi.fn(),
}))

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

describe('RacePredictor Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders input fields for default drivers', () => {
    const queryClient = createTestQueryClient()
    render(
      <QueryClientProvider client={queryClient}>
        <RacePredictor />
      </QueryClientProvider>
    )

    expect(screen.getByText('Race Predictor')).toBeInTheDocument()
    expect(screen.getByDisplayValue('VER')).toBeInTheDocument()
    expect(screen.getByDisplayValue('NOR')).toBeInTheDocument()
    expect(screen.getByDisplayValue('LEC')).toBeInTheDocument()
    expect(screen.getByText('Run Prediction')).toBeInTheDocument()
  })

  it('calls predictRace API and displays results on click', async () => {
    const mockPredictions = {
      predictions: [
        {
          driver_code: 'VER',
          driver_name: 'Max Verstappen',
          constructor: 'Red Bull Racing',
          predicted_position: 1,
          predicted_position_int: 1,
          win_probability: 0.65,
          podium_probability: 0.88,
          top10_probability: 0.98,
          dnf_probability: 0.02,
        },
        {
          driver_code: 'NOR',
          driver_name: 'Lando Norris',
          constructor: 'McLaren',
          predicted_position: 2,
          predicted_position_int: 2,
          win_probability: 0.25,
          podium_probability: 0.70,
          top10_probability: 0.95,
          dnf_probability: 0.05,
        },
      ],
    }

    vi.mocked(api.predictRace).mockResolvedValue(mockPredictions)

    const queryClient = createTestQueryClient()
    render(
      <QueryClientProvider client={queryClient}>
        <RacePredictor />
      </QueryClientProvider>
    )

    // Trigger prediction
    const predictBtn = screen.getByText('Run Prediction')
    fireEvent.click(predictBtn)

    // Verify prediction loading states/triggers
    await waitFor(() => {
      expect(api.predictRace).toHaveBeenCalledTimes(1)
    })

    // Verify results render in card
    expect(await screen.findByText('Prediction Results')).toBeInTheDocument()
    expect(screen.getByText('Max Verstappen')).toBeInTheDocument()
    expect(screen.getByText('Lando Norris')).toBeInTheDocument()
    expect(screen.getByText('65.0%')).toBeInTheDocument() // Win %
    expect(screen.getByText('88.0%')).toBeInTheDocument() // Podium %
    expect(screen.getByText('95.0%')).toBeInTheDocument() // NOR top 10 %
  })
})
