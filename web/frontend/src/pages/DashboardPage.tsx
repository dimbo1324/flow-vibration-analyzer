import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Activity, ChevronRight, CheckCircle, XCircle, Upload, BarChart2 } from 'lucide-react'
import { apiFetch } from '../shared/api/client'
import { LoadingSpinner } from '../shared/ui/LoadingSpinner'

interface HealthResponse {
  status: string
  app: string
  version: string
}

function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => apiFetch<HealthResponse>('/health'),
    retry: 1,
    refetchInterval: 30_000,
  })
}

export function DashboardPage() {
  const navigate = useNavigate()
  const { data: health, isLoading, isError } = useHealth()

  return (
    <div className="flex flex-col items-center py-12 gap-8">
      {/* Logo / title */}
      <div className="flex items-center gap-3">
        <Activity className="h-10 w-10 text-blue-500" />
        <div>
          <h1 className="text-2xl font-bold text-white">Industrial Vibration Analyzer</h1>
          <p className="text-gray-400 text-sm mt-0.5">Анализатор вибраций потока — веб-интерфейс</p>
        </div>
      </div>

      <p className="max-w-md text-center text-gray-400 text-sm leading-relaxed">
        Спектральный анализ сигналов вибрации, расчёт гидродинамических характеристик и
        оценка риска резонанса для теплообменного оборудования.
      </p>

      {/* Health status */}
      <div className="flex items-center gap-2 text-sm">
        {isLoading && <LoadingSpinner message="Проверка бэкенда..." />}
        {isError && (
          <span className="flex items-center gap-1.5 text-red-400">
            <XCircle className="h-4 w-4" />
            Бэкенд недоступен
          </span>
        )}
        {health && (
          <span className="flex items-center gap-1.5 text-green-400">
            <CheckCircle className="h-4 w-4" />
            Бэкенд работает · v{health.version}
          </span>
        )}
      </div>

      {/* CTA cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 w-full max-w-xl">
        <button
          onClick={() => navigate('/demo')}
          className="flex flex-col items-start gap-2 rounded-lg border border-blue-800 bg-blue-950/40
                     px-5 py-4 text-left hover:bg-blue-950/70 transition-colors group"
        >
          <BarChart2 className="h-6 w-6 text-blue-400 group-hover:text-blue-300" />
          <div>
            <p className="font-semibold text-white text-sm">Демо-анализ</p>
            <p className="text-xs text-gray-400 mt-0.5">Встроенные синтетические сценарии</p>
          </div>
          <ChevronRight className="h-4 w-4 text-blue-500 self-end" />
        </button>

        <button
          onClick={() => navigate('/upload')}
          className="flex flex-col items-start gap-2 rounded-lg border border-gray-700 bg-gray-900
                     px-5 py-4 text-left hover:bg-gray-800 transition-colors group"
        >
          <Upload className="h-6 w-6 text-gray-400 group-hover:text-gray-200" />
          <div>
            <p className="font-semibold text-white text-sm">Загрузка файла</p>
            <p className="text-xs text-gray-400 mt-0.5">CSV, Excel, Parquet — ваши данные</p>
          </div>
          <ChevronRight className="h-4 w-4 text-gray-500 self-end" />
        </button>
      </div>
    </div>
  )
}
