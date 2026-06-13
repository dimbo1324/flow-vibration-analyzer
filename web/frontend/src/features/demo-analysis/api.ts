import { useMutation, useQuery } from '@tanstack/react-query'
import { apiFetch } from '../../shared/api/client'
import {
  AnalysisResponse,
  AnalysisResponseSchema,
  DemoScenariosResponseSchema,
} from './types'

export function useDemoScenarios() {
  return useQuery({
    queryKey: ['demo-scenarios'],
    queryFn: async () => {
      const raw = await apiFetch<unknown>('/demo-scenarios')
      return DemoScenariosResponseSchema.parse(raw)
    },
    retry: 2,
    retryDelay: (attempt) => Math.min(500 * 2 ** attempt, 5000),
  })
}

export function useRunDemoAnalysis() {
  return useMutation({
    mutationFn: async (scenarioKey: string): Promise<AnalysisResponse> => {
      const raw = await apiFetch<unknown>('/analysis/demo', {
        method: 'POST',
        body: JSON.stringify({ scenario_key: scenarioKey }),
      })
      return AnalysisResponseSchema.parse(raw)
    },
  })
}
