import { clsx } from 'clsx'

interface MetricCardProps {
  label: string
  value: string | number | null | undefined
  unit?: string
  variant?: 'default' | 'safe' | 'watch' | 'critical'
}

const variantClasses: Record<string, string> = {
  default: 'border-gray-700 bg-gray-900',
  safe: 'border-green-700 bg-green-950',
  watch: 'border-amber-600 bg-amber-950',
  critical: 'border-red-700 bg-red-950',
}

export function MetricCard({ label, value, unit, variant = 'default' }: MetricCardProps) {
  const displayValue = value != null ? String(value) : '—'
  return (
    <div className={clsx('rounded-lg border p-4', variantClasses[variant])}>
      <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">{label}</p>
      <p className="text-2xl font-mono font-semibold text-white">
        {displayValue}
        {unit && <span className="text-sm text-gray-400 ml-1">{unit}</span>}
      </p>
    </div>
  )
}
