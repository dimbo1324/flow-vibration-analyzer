import { ApiError } from './errors'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${path}`
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    ...init,
  })

  if (!response.ok) {
    let code = 'UNKNOWN_ERROR'
    let message = `HTTP ${response.status}`
    let details: string | null = null
    try {
      const body = await response.json()
      if (body?.error) {
        code = body.error.code ?? code
        message = body.error.message ?? message
        details = body.error.details ?? null
      }
    } catch {
      // ignore JSON parse errors
    }
    throw new ApiError(code, message, details, response.status)
  }

  return response.json() as Promise<T>
}
