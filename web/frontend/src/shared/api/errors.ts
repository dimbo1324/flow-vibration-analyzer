export class ApiError extends Error {
  constructor(
    public readonly code: string,
    public readonly message: string,
    public readonly details: string | null = null,
    public readonly status: number = 500
  ) {
    super(message)
    this.name = 'ApiError'
  }
}
