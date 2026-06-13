import { useState } from 'react'
import { Download, FileText, Sheet, FileBarChart } from 'lucide-react'

interface ExportPanelProps {
  analysisId: string
}

type ExportKey = 'html' | 'pdf' | 'spectrum' | 'signal' | 'physics'

const EXPORTS: { key: ExportKey; label: string; url: (id: string) => string; icon: React.ElementType }[] = [
  { key: 'html',     label: 'Скачать HTML',        url: id => `/api/analysis/${id}/reports/html`,     icon: FileText },
  { key: 'pdf',      label: 'Скачать PDF',          url: id => `/api/analysis/${id}/reports/pdf`,      icon: FileBarChart },
  { key: 'spectrum', label: 'Спектр CSV',           url: id => `/api/analysis/${id}/exports/spectrum`, icon: Sheet },
  { key: 'signal',   label: 'Сигнал CSV',           url: id => `/api/analysis/${id}/exports/signal`,   icon: Sheet },
  { key: 'physics',  label: 'Физика CSV',           url: id => `/api/analysis/${id}/exports/physics`,  icon: Sheet },
]

export function ExportPanel({ analysisId }: ExportPanelProps) {
  const [loading, setLoading] = useState<ExportKey | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function handleDownload(key: ExportKey, url: string) {
    setLoading(key)
    setError(null)
    try {
      const resp = await fetch(url)
      if (!resp.ok) {
        const body = await resp.json().catch(() => null)
        throw new Error(body?.error?.message ?? `Ошибка экспорта (${resp.status})`)
      }
      const blob = await resp.blob()
      const cd = resp.headers.get('content-disposition') ?? ''
      const match = cd.match(/filename="([^"]+)"/)
      const filename = match?.[1] ?? `iva_${key}_${analysisId.slice(0, 8)}`
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = filename
      a.click()
      URL.revokeObjectURL(a.href)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка экспорта.')
    } finally {
      setLoading(null)
    }
  }

  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
      <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
        <Download className="h-4 w-4" />
        Экспорт результатов
      </h3>

      <div className="flex flex-wrap gap-2">
        {EXPORTS.map(({ key, label, url, icon: Icon }) => (
          <button
            key={key}
            onClick={() => handleDownload(key, url(analysisId))}
            disabled={loading !== null}
            className="flex items-center gap-1.5 rounded border border-gray-700 bg-gray-800 px-3 py-1.5
                       text-xs text-gray-200 hover:bg-gray-700 hover:border-gray-600
                       disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Icon className="h-3.5 w-3.5" />
            {loading === key ? 'Загрузка...' : label}
          </button>
        ))}
      </div>

      {error && (
        <p className="mt-2 text-xs text-red-400">{error}</p>
      )}
    </div>
  )
}
