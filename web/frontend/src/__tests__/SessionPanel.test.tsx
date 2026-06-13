import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { SessionPanel } from '../features/sessions/SessionPanel'

describe('SessionPanel', () => {
  it('renders save button', () => {
    render(<SessionPanel analysisId="test-id" />)
    expect(screen.getByText(/Сохранить/i)).toBeInTheDocument()
  })

  it('renders load button', () => {
    render(<SessionPanel analysisId="test-id" />)
    expect(screen.getByText(/Открыть/i)).toBeInTheDocument()
  })

  it('renders .vibproj label', () => {
    render(<SessionPanel analysisId="test-id" />)
    const matches = screen.getAllByText(/vibproj/i)
    expect(matches.length).toBeGreaterThanOrEqual(1)
  })
})
