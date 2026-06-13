import { useState } from 'react'
import { Play } from 'lucide-react'
import { useDemoScenarios, useRunDemoAnalysis } from '../features/demo-analysis/api'
import { DemoScenarioSelector } from '../features/demo-analysis/DemoScenarioSelector'
import { DemoAnalysisView } from '../features/demo-analysis/DemoAnalysisView'
import { ExportPanel } from '../features/reports/ExportPanel'
import { SessionPanel } from '../features/sessions/SessionPanel'
import { LoadingSpinner } from '../shared/ui/LoadingSpinner'
import { ErrorBanner } from '../shared/ui/ErrorBanner'
import { ApiError } from '../shared/api/errors'

export function DemoAnalysisPage() {
  const { data: scenariosData, isLoading: scenariosLoading, isError: scenariosError } = useDemoScenarios()
  const mutation = useRunDemoAnalysis()

  const [selectedKey, setSelectedKey] = useState<string>('clean_40hz')

  const effectiveKey = scenariosData?.items.length
    ? (scenariosData.items.some(s => s.key === selectedKey) ? selectedKey : scenariosData.items[0].key)
    : selectedKey

  function handleRun() {
    mutation.mutate(effectiveKey)
  }

  const mutationError = mutation.error
  const errorMessage = mutationError instanceof ApiError
    ? mutationError.message
    : mutationError instanceof Error
    ? mutationError.message
    : 'Произошла ошибка при выполнении анализа.'

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold text-white">Демо-анализ</h1>

      {scenariosLoading && <LoadingSpinner message="Загрузка сценариев..." />}
      {scenariosError && (
        <ErrorBanner message="Не удалось загрузить сценарии. Убедитесь, что бэкенд запущен." />
      )}

      {scenariosData && (
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="flex-1">
            <DemoScenarioSelector
              scenarios={scenariosData.items}
              selected={effectiveKey}
              onChange={setSelectedKey}
              disabled={mutation.isPending}
            />
          </div>
          <button
            onClick={handleRun}
            disabled={mutation.isPending}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold
                       text-white hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed
                       transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <Play className="h-4 w-4" />
            Запустить анализ
          </button>
        </div>
      )}

      {mutation.isPending && <LoadingSpinner message="Выполняется анализ вибраций..." />}
      {mutation.isError && <ErrorBanner message={errorMessage} />}

      {mutation.data && (
        <>
          <DemoAnalysisView result={mutation.data} />
          <ExportPanel analysisId={mutation.data.analysis_id} />
          <SessionPanel analysisId={mutation.data.analysis_id} />
        </>
      )}
    </div>
  )
}
