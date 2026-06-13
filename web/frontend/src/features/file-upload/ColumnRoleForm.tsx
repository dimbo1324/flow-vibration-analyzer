import { useState } from 'react'
import { SIGNAL_ROLES } from './model'
import type { FilePreview } from './model'
import type { RoleAssignment, FlowParameters } from './api'

interface ColumnRoleFormProps {
  preview: FilePreview | null | undefined
  onSubmit: (role: RoleAssignment, flow: FlowParameters) => void
  disabled?: boolean
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs text-gray-400 uppercase tracking-wider">{label}</label>
      {children}
    </div>
  )
}

const inputCls =
  'rounded bg-gray-800 border border-gray-700 text-white text-sm px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500'

export function ColumnRoleForm({ preview, onSubmit, disabled }: ColumnRoleFormProps) {
  const columns = preview?.columns ?? []
  const colOptions = columns.length > 0 ? columns : ['time_s', 'signal']

  const [timeCol, setTimeCol] = useState(colOptions[0] ?? 'time_s')
  const [signalCol, setSignalCol] = useState(colOptions[1] ?? 'signal')
  const [role, setRole] = useState('acceleration_y')
  const [rate, setRate] = useState('1000')
  const [convFactor, setConvFactor] = useState('')
  // Flow parameters
  const [diameter, setDiameter] = useState('0.012')
  const [velocity, setVelocity] = useState('2.0')
  const [density, setDensity] = useState('998.0')
  const [viscosity, setViscosity] = useState('0.001002')
  const [natFreq, setNatFreq] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const roleAssignment: RoleAssignment = {
      time_column: timeCol,
      primary_signal_column: signalCol,
      signal_role: role,
      sampling_rate_hz: parseFloat(rate) || 1000,
      ...(convFactor ? { sensor_conversion_factor: parseFloat(convFactor) } : {}),
    }
    const flow: FlowParameters = {
      ...(diameter ? { cylinder_diameter_m: parseFloat(diameter) } : {}),
      ...(velocity ? { mean_flow_velocity_ms: parseFloat(velocity) } : {}),
      ...(density ? { fluid_density_kgm3: parseFloat(density) } : {}),
      ...(viscosity ? { dynamic_viscosity_pas: parseFloat(viscosity) } : {}),
      ...(natFreq ? { natural_frequency_hz: parseFloat(natFreq) } : {}),
    }
    onSubmit(roleAssignment, flow)
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
      {/* Signal configuration */}
      <div>
        <h3 className="text-sm font-semibold text-gray-200 mb-3">Конфигурация сигнала</h3>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <Field label="Столбец времени">
            {columns.length > 0 ? (
              <select value={timeCol} onChange={e => setTimeCol(e.target.value)} disabled={disabled} className={inputCls}>
                {columns.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            ) : (
              <input value={timeCol} onChange={e => setTimeCol(e.target.value)} disabled={disabled} className={inputCls} placeholder="time_s" />
            )}
          </Field>

          <Field label="Столбец сигнала">
            {columns.length > 0 ? (
              <select value={signalCol} onChange={e => setSignalCol(e.target.value)} disabled={disabled} className={inputCls}>
                {columns.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            ) : (
              <input value={signalCol} onChange={e => setSignalCol(e.target.value)} disabled={disabled} className={inputCls} placeholder="signal" />
            )}
          </Field>

          <Field label="Роль сигнала">
            <select value={role} onChange={e => setRole(e.target.value)} disabled={disabled} className={inputCls}>
              {SIGNAL_ROLES.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
            </select>
          </Field>

          <Field label="Частота дискретизации, Гц">
            <input type="number" value={rate} onChange={e => setRate(e.target.value)} disabled={disabled} className={inputCls} min="1" step="any" />
          </Field>

          <Field label="Коэф. преобразования">
            <input type="number" value={convFactor} onChange={e => setConvFactor(e.target.value)} disabled={disabled} className={inputCls} placeholder="1.0 (опц.)" step="any" />
          </Field>
        </div>
      </div>

      {/* Flow parameters */}
      <div>
        <h3 className="text-sm font-semibold text-gray-200 mb-3">Параметры потока</h3>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <Field label="Диаметр цилиндра, м">
            <input type="number" value={diameter} onChange={e => setDiameter(e.target.value)} disabled={disabled} className={inputCls} step="any" />
          </Field>
          <Field label="Скорость потока, м/с">
            <input type="number" value={velocity} onChange={e => setVelocity(e.target.value)} disabled={disabled} className={inputCls} step="any" />
          </Field>
          <Field label="Плотность жидкости, кг/м³">
            <input type="number" value={density} onChange={e => setDensity(e.target.value)} disabled={disabled} className={inputCls} step="any" />
          </Field>
          <Field label="Динамическая вязкость, Па·с">
            <input type="number" value={viscosity} onChange={e => setViscosity(e.target.value)} disabled={disabled} className={inputCls} step="any" />
          </Field>
          <Field label="Собственная частота, Гц">
            <input type="number" value={natFreq} onChange={e => setNatFreq(e.target.value)} disabled={disabled} className={inputCls} placeholder="опц." step="any" />
          </Field>
        </div>
      </div>

      <button
        type="submit"
        disabled={disabled}
        className="self-start rounded-lg bg-blue-600 px-5 py-2 text-sm font-semibold text-white
                   hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors
                   focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        Запустить анализ
      </button>
    </form>
  )
}
