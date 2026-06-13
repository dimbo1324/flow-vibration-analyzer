import { useRef, useState, DragEvent, ChangeEvent } from 'react'
import { Upload, FileText } from 'lucide-react'
import { ALLOWED_EXTENSIONS, MAX_UPLOAD_MB } from './model'

interface FileDropzoneProps {
  onFile: (file: File) => void
  disabled?: boolean
}

export function FileDropzone({ onFile, disabled }: FileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragOver, setDragOver] = useState(false)
  const [clientError, setClientError] = useState<string | null>(null)

  function validate(file: File): string | null {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return `Формат ${ext} не поддерживается. Допустимые: ${ALLOWED_EXTENSIONS.join(', ')}.`
    }
    if (file.size > MAX_UPLOAD_MB * 1024 * 1024) {
      return `Файл превышает максимальный размер ${MAX_UPLOAD_MB} МБ.`
    }
    return null
  }

  function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return
    const file = files[0]
    const err = validate(file)
    if (err) {
      setClientError(err)
      return
    }
    setClientError(null)
    onFile(file)
  }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setDragOver(false)
    if (disabled) return
    handleFiles(e.dataTransfer.files)
  }

  function onInputChange(e: ChangeEvent<HTMLInputElement>) {
    handleFiles(e.target.files)
    e.target.value = ''
  }

  return (
    <div>
      <div
        onClick={() => !disabled && inputRef.current?.click()}
        onDragOver={e => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        role="button"
        aria-label="Зона загрузки файла. Нажмите или перетащите файл для загрузки."
        aria-disabled={disabled}
        tabIndex={disabled ? -1 : 0}
        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') inputRef.current?.click() }}
        className={[
          'flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed',
          'py-10 px-6 cursor-pointer transition-colors',
          dragOver ? 'border-blue-400 bg-blue-950/30' : 'border-gray-700 bg-gray-900 hover:border-gray-500',
          disabled ? 'opacity-50 cursor-not-allowed' : '',
        ].join(' ')}
      >
        <Upload className="h-8 w-8 text-gray-500" />
        <div className="text-center">
          <p className="text-sm text-gray-300 font-medium">
            Перетащите файл или{' '}
            <span className="text-blue-400 underline">выберите вручную</span>
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Поддерживаются: {ALLOWED_EXTENSIONS.join(', ')} · Макс. {MAX_UPLOAD_MB} МБ
          </p>
        </div>
      </div>

      <input
        ref={inputRef}
        type="file"
        className="hidden"
        accept={ALLOWED_EXTENSIONS.join(',')}
        onChange={onInputChange}
        disabled={disabled}
      />

      {clientError && (
        <p className="mt-2 text-sm text-red-400 flex items-center gap-1.5">
          <FileText className="h-4 w-4 flex-shrink-0" />
          {clientError}
        </p>
      )}
    </div>
  )
}
