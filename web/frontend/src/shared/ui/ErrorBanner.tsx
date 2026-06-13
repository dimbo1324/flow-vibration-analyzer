import { AlertTriangle } from 'lucide-react'

interface ErrorBannerProps {
  message: string
  details?: string | null
}

export function ErrorBanner({ message, details }: ErrorBannerProps) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-red-700 bg-red-950 p-4 text-red-300">
      <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" />
      <div>
        <p className="font-medium">{message}</p>
        {details && <p className="mt-1 text-sm text-red-400">{details}</p>}
      </div>
    </div>
  )
}
