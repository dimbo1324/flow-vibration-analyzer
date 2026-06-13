import { DemoScenarioItem } from './types'

interface DemoScenarioSelectorProps {
  scenarios: DemoScenarioItem[]
  selected: string
  onChange: (key: string) => void
  disabled?: boolean
}

export function DemoScenarioSelector({
  scenarios,
  selected,
  onChange,
  disabled,
}: DemoScenarioSelectorProps) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor="scenario-select" className="text-sm text-gray-400">
        Сценарий анализа
      </label>
      <select
        id="scenario-select"
        value={selected}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-white
                   focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500
                   disabled:opacity-50"
      >
        {scenarios.map((s) => (
          <option key={s.key} value={s.key}>
            {s.title_ru}
          </option>
        ))}
      </select>
      {scenarios.find((s) => s.key === selected) && (
        <p className="text-xs text-gray-500">
          {scenarios.find((s) => s.key === selected)?.description_ru}
        </p>
      )}
    </div>
  )
}
