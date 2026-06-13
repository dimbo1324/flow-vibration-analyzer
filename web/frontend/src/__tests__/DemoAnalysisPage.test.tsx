import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { DemoAnalysisPage } from '../pages/DemoAnalysisPage'

function wrap(ui: React.ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('DemoAnalysisPage', () => {
  it('renders page heading', () => {
    wrap(<DemoAnalysisPage />)
    expect(screen.getByText(/Демо-анализ/i)).toBeInTheDocument()
  })

  it('does not render ExportPanel before analysis runs', () => {
    wrap(<DemoAnalysisPage />)
    // Панель экспорта появляется только после получения результата анализа.
    expect(screen.queryByText(/Экспорт результатов/i)).not.toBeInTheDocument()
  })

  it('shows loading spinner while fetching scenarios', () => {
    wrap(<DemoAnalysisPage />)
    // Когда запрос сценариев ещё выполняется, показывается спиннер.
    expect(screen.getByText(/Загрузка сценариев/i)).toBeInTheDocument()
  })
})
