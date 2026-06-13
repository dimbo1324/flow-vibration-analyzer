import { z } from 'zod'

export const UploadedFileSchema = z.object({
  file_id: z.string(),
  original_name: z.string(),
  size_bytes: z.number(),
  extension: z.string(),
  uploaded_at: z.string(),
})

export const FilePreviewSchema = z.object({
  columns: z.array(z.string()),
  rows: z.array(z.record(z.unknown())),
  total_preview_rows: z.number(),
})

export type UploadedFile = z.infer<typeof UploadedFileSchema>
export type FilePreview = z.infer<typeof FilePreviewSchema>

export const ALLOWED_EXTENSIONS = ['.csv', '.txt', '.xlsx', '.parquet']
export const MAX_UPLOAD_MB = 100

export const SIGNAL_ROLES = [
  { value: 'acceleration_x', label: 'Ускорение X' },
  { value: 'acceleration_y', label: 'Ускорение Y' },
  { value: 'acceleration_z', label: 'Ускорение Z' },
  { value: 'pressure', label: 'Давление' },
  { value: 'velocity', label: 'Скорость' },
]
