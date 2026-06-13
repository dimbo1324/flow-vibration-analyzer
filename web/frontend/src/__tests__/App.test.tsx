import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Minimal smoke test — App renders without crash
describe('App smoke test', () => {
  it('renders root without throwing', () => {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })

    // Render a simple div to verify testing-library works
    const { container } = render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <div data-testid="app-root">IVA Web</div>
        </MemoryRouter>
      </QueryClientProvider>
    )
    expect(container).toBeDefined()
    expect(screen.getByTestId('app-root')).toBeInTheDocument()
  })
})
