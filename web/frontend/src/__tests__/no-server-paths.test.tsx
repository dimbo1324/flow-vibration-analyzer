/**
 * Проверяет, что серверные абсолютные пути не отображаются в UI.
 *
 * Сервер никогда не должен передавать клиенту абсолютные пути (C:\..., /home/...),
 * а фронтенд не должен их отображать — это требование безопасности.
 */
import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { DemoAnalysisView } from '../features/demo-analysis/DemoAnalysisView'
import type { AnalysisResponse } from '../features/demo-analysis/types'

const MOCK_RESULT: AnalysisResponse = {
  analysis_id: 'test-id-1234',
  is_demo: true,
  demo_title: 'Тест',
  summary: {
    risk_level: 'safe',
    risk_label_ru: 'Безопасно',
    dominant_peak_hz: 40.0,
    rms_total: 0.5,
    reynolds_number: null,
    strouhal_number: null,
  },
  signal: {
    time_s: [0, 0.001],
    raw: [0.1, 0.2],
    filtered: [0.09, 0.19],
    rms_trend: [0.5],
  },
  spectrum: {
    frequencies_hz: [10, 40],
    psd: [0.001, 0.5],
    peaks: [],
  },
  warnings: [],
}

describe('No server paths in UI', () => {
  it('does not render Windows absolute paths', () => {
    const { container } = render(<DemoAnalysisView result={MOCK_RESULT} />)
    // Windows-путь вида C:\ или D:\ не должен появляться в DOM.
    expect(container.textContent).not.toMatch(/[A-Z]:\\/i)
  })

  it('does not render Unix absolute paths with home/tmp', () => {
    const { container } = render(<DemoAnalysisView result={MOCK_RESULT} />)
    // /home/ или /tmp/ не должны фигурировать в UI.
    expect(container.textContent).not.toMatch(/\/(home|tmp|app)\//i)
  })
})
