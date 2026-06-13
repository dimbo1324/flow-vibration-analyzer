import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { UploadAnalysisPage } from '../pages/UploadAnalysisPage'

function wrap(ui: React.ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('UploadAnalysisPage', () => {
  it('renders heading', () => {
    wrap(<UploadAnalysisPage />)
    expect(screen.getByText(/Загрузка файла/i)).toBeInTheDocument()
  })

  it('shows allowed extensions hint', () => {
    wrap(<UploadAnalysisPage />)
    expect(screen.getByText(/csv/i)).toBeInTheDocument()
  })

  it('shows max size hint', () => {
    wrap(<UploadAnalysisPage />)
    expect(screen.getByText(/100/)).toBeInTheDocument()
  })
})
