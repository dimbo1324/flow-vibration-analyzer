import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { DashboardPage } from '../pages/DashboardPage'

function wrap(ui: React.ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('DashboardPage', () => {
  it('renders application title', () => {
    wrap(<DashboardPage />)
    expect(screen.getByText(/Industrial Vibration Analyzer/i)).toBeInTheDocument()
  })

  it('renders demo analysis CTA card', () => {
    wrap(<DashboardPage />)
    expect(screen.getByText(/Демо-анализ/i)).toBeInTheDocument()
  })

  it('renders file upload CTA card', () => {
    wrap(<DashboardPage />)
    expect(screen.getByText(/Загрузка файла/i)).toBeInTheDocument()
  })

  it('renders description text', () => {
    wrap(<DashboardPage />)
    expect(screen.getByText(/Спектральный анализ/i)).toBeInTheDocument()
  })
})
