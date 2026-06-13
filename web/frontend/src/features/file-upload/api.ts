import { useMutation, useQuery } from '@tanstack/react-query'
import { apiFetch } from '../../shared/api/client'
import { ApiError } from '../../shared/api/errors'
import { UploadedFileSchema, FilePreviewSchema, type UploadedFile, type FilePreview } from './model'
import { AnalysisResponseSchema, type AnalysisResponse } from '../demo-analysis/types'

// ── Upload file ──────────────────────────────────────────────────────────────

async function uploadFile(file: File): Promise<UploadedFile> {
  const formData = new FormData()
  formData.append('file', file)

  const resp = await fetch('/api/files/upload', {
    method: 'POST',
    body: formData,
  })

  const body = await resp.json()
  if (!resp.ok) {
    throw new ApiError(body?.error?.code ?? 'UPLOAD_ERROR', body?.error?.message ?? 'Ошибка загрузки файла.', null, resp.status)
  }
  return UploadedFileSchema.parse(body)
}

export function useUploadFile() {
  return useMutation<UploadedFile, Error, File>({
    mutationFn: uploadFile,
  })
}

// ── Preview columns ──────────────────────────────────────────────────────────

export function useFilePreview(fileId: string | null) {
  return useQuery<FilePreview, Error>({
    queryKey: ['file-preview', fileId],
    queryFn: () => apiFetch<FilePreview>(`/files/${fileId}/preview?rows=5`).then(d => FilePreviewSchema.parse(d)),
    enabled: fileId != null,
    retry: false,
  })
}

// ── Run analysis on uploaded file ───────────────────────────────────────────

interface RoleAssignment {
  time_column: string
  primary_signal_column: string
  signal_role: string
  sampling_rate_hz: number
  sensor_conversion_factor?: number
}

interface FlowParameters {
  cylinder_diameter_m?: number
  mean_flow_velocity_ms?: number
  fluid_density_kgm3?: number
  dynamic_viscosity_pas?: number
  natural_frequency_hz?: number
}

interface UploadAnalysisPayload {
  file_id: string
  role_assignment: RoleAssignment
  settings: {
    flow_parameters?: FlowParameters
  }
}

async function runUploadAnalysis(payload: UploadAnalysisPayload): Promise<AnalysisResponse> {
  const resp = await fetch('/api/analysis/upload', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const body = await resp.json()
  if (!resp.ok) {
    throw new ApiError(body?.error?.code ?? 'ANALYSIS_ERROR', body?.error?.message ?? 'Ошибка запуска анализа.', null, resp.status)
  }
  return AnalysisResponseSchema.parse(body)
}

export function useRunUploadAnalysis() {
  return useMutation<AnalysisResponse, Error, UploadAnalysisPayload>({
    mutationFn: runUploadAnalysis,
  })
}

export type { UploadAnalysisPayload, RoleAssignment, FlowParameters }
