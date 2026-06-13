import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

interface SignalChartProps {
  timeS: number[]
  filtered: number[]
}

export function SignalChart({ timeS, filtered }: SignalChartProps) {
  const data = timeS.map((t, i) => ({ t: +t.toFixed(4), v: +filtered[i].toFixed(6) }))

  return (
    <div>
      <p className="text-sm text-gray-400 mb-2">Сигнал во времени (фильтрованный)</p>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 4, right: 8, bottom: 4, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="t"
            stroke="#9ca3af"
            tick={{ fontSize: 11 }}
            label={{ value: 'Время, с', position: 'insideBottomRight', offset: -4, fill: '#9ca3af', fontSize: 11 }}
          />
          <YAxis stroke="#9ca3af" tick={{ fontSize: 11 }} width={60} />
          <Tooltip
            contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 6 }}
            labelStyle={{ color: '#9ca3af' }}
            itemStyle={{ color: '#60a5fa' }}
          />
          <Line type="monotone" dataKey="v" stroke="#3b82f6" dot={false} strokeWidth={1.5} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

interface PsdChartProps {
  frequenciesHz: number[]
  psd: number[]
}

export function PsdChart({ frequenciesHz, psd }: PsdChartProps) {
  const data = frequenciesHz.map((f, i) => ({
    f: +f.toFixed(2),
    p: psd[i] > 0 ? +(10 * Math.log10(psd[i])).toFixed(3) : -120,
  }))

  return (
    <div>
      <p className="text-sm text-gray-400 mb-2">Спектральная плотность мощности (дБ)</p>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 4, right: 8, bottom: 4, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="f"
            stroke="#9ca3af"
            tick={{ fontSize: 11 }}
            label={{ value: 'Частота, Гц', position: 'insideBottomRight', offset: -4, fill: '#9ca3af', fontSize: 11 }}
          />
          <YAxis
            stroke="#9ca3af"
            tick={{ fontSize: 11 }}
            width={60}
            label={{ value: 'дБ', angle: -90, position: 'insideLeft', fill: '#9ca3af', fontSize: 11 }}
          />
          <Tooltip
            contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 6 }}
            labelStyle={{ color: '#9ca3af' }}
            itemStyle={{ color: '#34d399' }}
          />
          <Line type="monotone" dataKey="p" stroke="#10b981" dot={false} strokeWidth={1.5} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
