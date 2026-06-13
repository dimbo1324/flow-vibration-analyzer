import { AnalysisResponse } from './types'
import { MetricCard } from '../../shared/ui/MetricCard'
import { DemoMarker } from '../../shared/ui/DemoMarker'
import { SignalChart, PsdChart } from '../../entities/analysis/charts'

function riskVariant(level: string | null): 'default' | 'safe' | 'watch' | 'critical' {
  if (level === 'safe') return 'safe'
  if (level === 'watch') return 'watch'
  if (level === 'critical') return 'critical'
  return 'default'
}

function fmt(value: number | null | undefined, decimals = 3): string {
  if (value == null) return '—'
  return value.toFixed(decimals)
}

interface DemoAnalysisViewProps {
  result: AnalysisResponse
}

export function DemoAnalysisView({ result }: DemoAnalysisViewProps) {
  const { summary, signal, spectrum, warnings, is_demo, demo_title } = result

  return (
    <div className="flex flex-col gap-6">
      {/* Demo banner */}
      {is_demo && <DemoMarker />}

      {/* Title */}
      {demo_title && (
        <h2 className="text-lg font-semibold text-white">{demo_title}</h2>
      )}

      {/* Metric cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <MetricCard
          label="Уровень риска"
          value={summary.risk_label_ru}
          variant={riskVariant(summary.risk_level)}
        />
        <MetricCard
          label="Доминирующий пик"
          value={fmt(summary.dominant_peak_hz, 2)}
          unit="Гц"
        />
        <MetricCard
          label="RMS сигнала"
          value={fmt(summary.rms_total, 5)}
        />
        <MetricCard
          label="Число Рейнольдса"
          value={summary.reynolds_number != null ? Math.round(summary.reynolds_number).toLocaleString('ru') : '—'}
        />
        <MetricCard
          label="Число Струхаля"
          value={fmt(summary.strouhal_number, 4)}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
          <SignalChart timeS={signal.time_s} filtered={signal.filtered} />
        </div>
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
          <PsdChart frequenciesHz={spectrum.frequencies_hz} psd={spectrum.psd} />
        </div>
      </div>

      {/* Peaks table */}
      {spectrum.peaks.length > 0 && (
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-3">Спектральные пики</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="py-2 pr-6 text-gray-400 font-medium">Частота, Гц</th>
                  <th className="py-2 pr-6 text-gray-400 font-medium">Амплитуда, дБ</th>
                  <th className="py-2 text-gray-400 font-medium">Тип</th>
                </tr>
              </thead>
              <tbody>
                {spectrum.peaks.map((peak, i) => (
                  <tr key={i} className="border-b border-gray-800">
                    <td className="py-2 pr-6 font-mono text-white">{peak.frequency_hz.toFixed(2)}</td>
                    <td className="py-2 pr-6 font-mono text-white">{peak.amplitude_db.toFixed(1)}</td>
                    <td className="py-2 text-gray-300">{peak.type}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="rounded-lg border border-amber-700 bg-amber-950 p-4">
          <h3 className="text-sm font-semibold text-amber-300 mb-2">Предупреждения</h3>
          <ul className="space-y-1">
            {warnings.map((w, i) => (
              <li key={i} className="text-sm text-amber-400">• {w}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
