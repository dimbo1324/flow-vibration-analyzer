import { useRef, useState } from 'react'
import { Save, FolderOpen } from 'lucide-react'
import type { AnalysisResponse } from '../demo-analysis/types'

interface SessionPanelProps {
  analysisId: string
  onSessionLoaded?: (result: AnalysisResponse | null, meta: Record<string, unknown>) => void
}

export function SessionPanel({ analysisId, onSessionLoaded }: SessionPanelProps) {
  const fileRef = useRef<HTMLInputElement>(null)
  const [saving, setSaving] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  async function handleSave() {
    setSaving(true)
    setError(null)
    setSuccess(null)
    try {
      const resp = await fetch(`/api/sessions/export/${analysisId}`, { method: 'POST' })
      if (!resp.ok) {
        const body = await resp.json().catch(() => null)
        throw new Error(body?.error?.message ?? 'Ошибка сохранения сессии.')
      }
      const blob = await resp.blob()
      const cd = resp.headers.get('content-disposition') ?? ''
      const match = cd.match(/filename="([^"]+)"/)
      const filename = match?.[1] ?? `iva_session_${analysisId.slice(0, 8)}.vibproj`
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = filename
      a.click()
      URL.revokeObjectURL(a.href)
      setSuccess('Сессия сохранена.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка сохранения.')
    } finally {
      setSaving(false)
    }
  }

  async function handleLoad(file: File) {
    setLoading(true)
    setError(null)
    setSuccess(null)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const resp = await fetch('/api/sessions/import', { method: 'POST', body: formData })
      const body = await resp.json()
      if (!resp.ok) {
        throw new Error(body?.error?.message ?? 'Ошибка загрузки сессии.')
      }
      setSuccess('Сессия загружена.')
      onSessionLoaded?.(body.has_result ? body.result : null, body)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка загрузки сессии.')
    } finally {
      setLoading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
      <h3 className="text-sm font-semibold text-gray-300 mb-3">Сессии</h3>

      <div className="flex flex-wrap gap-2">
        <button
          onClick={handleSave}
          disabled={saving || loading}
          className="flex items-center gap-1.5 rounded border border-gray-700 bg-gray-800 px-3 py-1.5
                     text-xs text-gray-200 hover:bg-gray-700 hover:border-gray-600
                     disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Save className="h-3.5 w-3.5" />
          {saving ? 'Сохранение...' : 'Сохранить .vibproj'}
        </button>

        <button
          onClick={() => fileRef.current?.click()}
          disabled={saving || loading}
          className="flex items-center gap-1.5 rounded border border-gray-700 bg-gray-800 px-3 py-1.5
                     text-xs text-gray-200 hover:bg-gray-700 hover:border-gray-600
                     disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <FolderOpen className="h-3.5 w-3.5" />
          {loading ? 'Загрузка...' : 'Открыть .vibproj'}
        </button>
      </div>

      <input
        ref={fileRef}
        type="file"
        accept=".vibproj"
        className="hidden"
        onChange={e => {
          const f = e.target.files?.[0]
          if (f) handleLoad(f)
        }}
      />

      {success && <p className="mt-2 text-xs text-green-400">{success}</p>}
      {error && <p className="mt-2 text-xs text-red-400">{error}</p>}
    </div>
  )
}
