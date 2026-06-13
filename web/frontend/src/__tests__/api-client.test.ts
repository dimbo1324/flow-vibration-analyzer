import { describe, it, expect } from 'vitest'
import { ApiError } from '../shared/api/errors'

describe('ApiError', () => {
  it('creates error with correct properties', () => {
    const err = new ApiError('UNKNOWN_SCENARIO', 'Сценарий не найден', null, 404)
    expect(err.code).toBe('UNKNOWN_SCENARIO')
    expect(err.message).toBe('Сценарий не найден')
    expect(err.status).toBe(404)
    expect(err.name).toBe('ApiError')
  })

  it('is instanceof Error', () => {
    const err = new ApiError('TEST', 'test')
    expect(err instanceof Error).toBe(true)
  })
})
