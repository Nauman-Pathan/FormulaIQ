import '@testing-library/jest-dom'
import React from 'react'
import { vi } from 'vitest'

// Mock Framer Motion to skip animations in tests
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => React.createElement('div', props, children),
    span: ({ children, ...props }: any) => React.createElement('span', props, children),
  },
  AnimatePresence: ({ children }: any) => React.createElement(React.Fragment, null, children),
}))

// Mock Plotly which doesn't run in JSDOM environment
vi.mock('react-plotly.js', () => ({
  default: () => React.createElement('div', { 'data-testid': 'mock-plotly' }, 'Plotly Chart'),
}))

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // Deprecated
    removeListener: vi.fn(), // Deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})
