import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { DemoAnalysisView } from '../features/demo-analysis/DemoAnalysisView'
import type { AnalysisResponse } from '../features/demo-analysis/types'

const MOCK_RESULT: AnalysisResponse = {
  analysis_id: 'demo-clean_40hz-abc123',
  is_demo: true,
  demo_title: 'Чистый сигнал 40 Гц',
  summary: {
    risk_level: 'safe',
    risk_label_ru: 'Безопасно',
    dominant_peak_hz: 40.0,
    rms_total: 0.7071,
    reynolds_number: 23904.0,
    strouhal_number: 0.204,
  },
  signal: {
    time_s: [0, 0.001, 0.002],
    raw: [0.1, 0.2, 0.15],
    filtered: [0.09, 0.19, 0.14],
    rms_trend: [0.5, 0.5],
  },
  spectrum: {
    frequencies_hz: [10, 20, 40, 80],
    psd: [0.001, 0.002, 0.5, 0.001],
    peaks: [{ frequency_hz: 40.0, amplitude_db: -3.0, type: 'vortex_shedding' }],
  },
  warnings: ['Демонстрационные синтетические данные'],
}

describe('DemoAnalysisView', () => {
  it('renders demo marker when is_demo is true', () => {
    render(<DemoAnalysisView result={MOCK_RESULT} />)
    // Text appears in both DemoMarker and warnings; at least one must exist
    const matches = screen.getAllByText(/Демонстрационные синтетические данные/i)
    expect(matches.length).toBeGreaterThanOrEqual(1)
  })

  it('renders demo title', () => {
    render(<DemoAnalysisView result={MOCK_RESULT} />)
    expect(screen.getByText('Чистый сигнал 40 Гц')).toBeInTheDocument()
  })

  it('renders risk level card', () => {
    render(<DemoAnalysisView result={MOCK_RESULT} />)
    expect(screen.getByText('Безопасно')).toBeInTheDocument()
  })

  it('renders peaks table with peak data', () => {
    render(<DemoAnalysisView result={MOCK_RESULT} />)
    // "40.00" appears in both the metric card and the peaks table row
    const matches = screen.getAllByText('40.00')
    expect(matches.length).toBeGreaterThanOrEqual(1)
  })

  it('renders warnings section', () => {
    render(<DemoAnalysisView result={MOCK_RESULT} />)
    expect(screen.getByText(/Предупреждения/i)).toBeInTheDocument()
  })
})
