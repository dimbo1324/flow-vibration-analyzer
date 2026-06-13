import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Activity, ChevronRight, CheckCircle, XCircle } from 'lucide-react'
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
    <div className="flex min-h-screen flex-col items-center justify-center px-4 py-16">
      {/* Logo / title */}
      <div className="flex items-center gap-3 mb-4">
        <Activity className="h-10 w-10 text-blue-500" />
        <div>
          <h1 className="text-3xl font-bold text-white">Industrial Vibration Analyzer</h1>
          <p className="text-gray-400 text-sm mt-0.5">
            Анализатор вибраций потока — веб-интерфейс
          </p>
        </div>
      </div>

      <p className="max-w-md text-center text-gray-400 mb-10 text-sm leading-relaxed">
        Спектральный анализ сигналов вибрации, расчёт гидродинамических характеристик и
        оценка риска резонанса для теплообменного оборудования.
      </p>

      {/* Health status */}
      <div className="mb-8 flex items-center gap-2 text-sm">
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

      {/* CTA */}
      <button
        onClick={() => navigate('/demo')}
        className="flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-3 font-semibold text-white
                   hover:bg-blue-500 active:bg-blue-700 transition-colors focus:outline-none
                   focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-950"
      >
        Запустить демо-анализ
        <ChevronRight className="h-5 w-5" />
      </button>
    </div>
  )
}
