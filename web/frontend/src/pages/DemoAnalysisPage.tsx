import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Play } from 'lucide-react'
import { useDemoScenarios, useRunDemoAnalysis } from '../features/demo-analysis/api'
import { DemoScenarioSelector } from '../features/demo-analysis/DemoScenarioSelector'
import { DemoAnalysisView } from '../features/demo-analysis/DemoAnalysisView'
import { LoadingSpinner } from '../shared/ui/LoadingSpinner'
import { ErrorBanner } from '../shared/ui/ErrorBanner'
import { ApiError } from '../shared/api/errors'

export function DemoAnalysisPage() {
  const navigate = useNavigate()
  const { data: scenariosData, isLoading: scenariosLoading, isError: scenariosError } = useDemoScenarios()
  const mutation = useRunDemoAnalysis()

  const [selectedKey, setSelectedKey] = useState<string>('clean_40hz')

  // Use the first scenario key when data arrives
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
    <div className="min-h-screen bg-gray-950 px-4 py-8">
      <div className="mx-auto max-w-5xl">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-1.5 text-sm text-gray-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            На главную
          </button>
          <span className="text-gray-700">/</span>
          <h1 className="text-xl font-semibold text-white">Демо-анализ</h1>
        </div>

        {/* Controls */}
        {scenariosLoading && <LoadingSpinner message="Загрузка сценариев..." />}
        {scenariosError && (
          <ErrorBanner message="Не удалось загрузить сценарии. Убедитесь, что бэкенд запущен." />
        )}

        {scenariosData && (
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end mb-8">
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
              className="flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 font-semibold
                         text-white hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed
                         transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500
                         focus:ring-offset-2 focus:ring-offset-gray-950"
            >
              <Play className="h-4 w-4" />
              Запустить анализ
            </button>
          </div>
        )}

        {/* Result / loading / error */}
        {mutation.isPending && <LoadingSpinner message="Выполняется анализ вибраций..." />}
        {mutation.isError && <ErrorBanner message={errorMessage} />}
        {mutation.data && <DemoAnalysisView result={mutation.data} />}
      </div>
    </div>
  )
}
