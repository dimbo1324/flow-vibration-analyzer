import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ExportPanel } from '../features/reports/ExportPanel'

describe('ExportPanel', () => {
  it('renders export heading', () => {
    render(<ExportPanel analysisId="test-id-123" />)
    expect(screen.getByText(/Экспорт/i)).toBeInTheDocument()
  })

  it('renders HTML download button', () => {
    render(<ExportPanel analysisId="test-id-123" />)
    expect(screen.getByText(/HTML/i)).toBeInTheDocument()
  })

  it('renders PDF download button', () => {
    render(<ExportPanel analysisId="test-id-123" />)
    expect(screen.getByText(/PDF/i)).toBeInTheDocument()
  })

  it('renders CSV buttons', () => {
    render(<ExportPanel analysisId="test-id-123" />)
    const csvButtons = screen.getAllByText(/CSV/i)
    expect(csvButtons.length).toBeGreaterThanOrEqual(1)
  })

  it('does not render absolute server paths', () => {
    const { container } = render(<ExportPanel analysisId="safe-id" />)
    expect(container.innerHTML).not.toMatch(/\/home\/|\/Users\/|C:\\/)
  })
})
