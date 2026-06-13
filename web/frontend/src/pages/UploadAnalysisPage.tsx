import { useState } from 'react'
import { FileDropzone } from '../features/file-upload/FileDropzone'
import { ColumnRoleForm } from '../features/file-upload/ColumnRoleForm'
import { ExportPanel } from '../features/reports/ExportPanel'
import { SessionPanel } from '../features/sessions/SessionPanel'
import { DemoAnalysisView } from '../features/demo-analysis/DemoAnalysisView'
import { LoadingSpinner } from '../shared/ui/LoadingSpinner'
import { ErrorBanner } from '../shared/ui/ErrorBanner'
import { useUploadFile, useRunUploadAnalysis, useFilePreview } from '../features/file-upload/api'
import type { UploadedFile } from '../features/file-upload/model'
import type { AnalysisResponse } from '../features/demo-analysis/types'
import type { RoleAssignment, FlowParameters } from '../features/file-upload/api'
import { CheckCircle, File } from 'lucide-react'

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} Б`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} КБ`
  return `${(bytes / (1024 * 1024)).toFixed(1)} МБ`
}

export function UploadAnalysisPage() {
  const uploadMutation = useUploadFile()
  const analysisMutation = useRunUploadAnalysis()

  const [uploadedFile, setUploadedFile] = useState<UploadedFile | null>(null)
  const [result, setResult] = useState<AnalysisResponse | null>(null)

  const { data: preview } = useFilePreview(uploadedFile?.file_id ?? null)

  function handleFile(file: File) {
    setResult(null)
    uploadMutation.mutate(file, {
      onSuccess: meta => setUploadedFile(meta),
    })
  }

  function handleAnalysisSubmit(role: RoleAssignment, flow: FlowParameters) {
    if (!uploadedFile) return
    analysisMutation.mutate(
      {
        file_id: uploadedFile.file_id,
        role_assignment: role,
        settings: { flow_parameters: Object.keys(flow).length > 0 ? flow : undefined },
      },
      { onSuccess: r => setResult(r) },
    )
  }

  const isUploading = uploadMutation.isPending
  const isAnalysing = analysisMutation.isPending

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold text-white">Загрузка файла и анализ</h1>

      {/* Drop zone */}
      <FileDropzone onFile={handleFile} disabled={isUploading || isAnalysing} />

      {isUploading && <LoadingSpinner message="Загрузка файла..." />}
      {uploadMutation.isError && (
        <ErrorBanner message={uploadMutation.error?.message ?? 'Ошибка загрузки файла.'} />
      )}

      {/* File metadata */}
      {uploadedFile && (
        <div className="flex items-center gap-3 rounded-lg border border-green-800 bg-green-950/40 px-4 py-3">
          <CheckCircle className="h-5 w-5 text-green-400 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-green-300">{uploadedFile.original_name}</p>
            <p className="text-xs text-green-500">
              {formatBytes(uploadedFile.size_bytes)} · {uploadedFile.extension.toUpperCase()}
            </p>
          </div>
          <File className="h-4 w-4 text-green-500 ml-auto" />
        </div>
      )}

      {/* Column role form */}
      {uploadedFile && (
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
          <ColumnRoleForm
            preview={preview}
            onSubmit={handleAnalysisSubmit}
            disabled={isAnalysing}
          />
        </div>
      )}

      {isAnalysing && <LoadingSpinner message="Выполняется анализ..." />}
      {analysisMutation.isError && (
        <ErrorBanner message={analysisMutation.error?.message ?? 'Ошибка анализа.'} />
      )}

      {/* Analysis result */}
      {result && (
        <>
          <DemoAnalysisView result={result} />
          <ExportPanel analysisId={result.analysis_id} />
          <SessionPanel analysisId={result.analysis_id} />
        </>
      )}
    </div>
  )
}
