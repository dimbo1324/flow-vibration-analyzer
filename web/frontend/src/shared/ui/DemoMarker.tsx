import { FlaskConical } from 'lucide-react'

export function DemoMarker() {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-blue-700 bg-blue-950 px-4 py-3 text-blue-300">
      <FlaskConical className="h-4 w-4 shrink-0" />
      <p className="text-sm font-medium">
        Демонстрационные синтетические данные — не используйте как реальные измерения.
      </p>
    </div>
  )
}
