import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { Shell } from '../shared/ui/Shell'

describe('Shell', () => {
  it('renders nav links', () => {
    render(
      <MemoryRouter>
        <Shell>
          <div>content</div>
        </Shell>
      </MemoryRouter>,
    )
    expect(screen.getByText(/Главная/i)).toBeInTheDocument()
    expect(screen.getByText(/Демо-анализ/i)).toBeInTheDocument()
    expect(screen.getByText(/Загрузка файла/i)).toBeInTheDocument()
  })

  it('renders children', () => {
    render(
      <MemoryRouter>
        <Shell>
          <p>Дочерний элемент</p>
        </Shell>
      </MemoryRouter>,
    )
    expect(screen.getByText('Дочерний элемент')).toBeInTheDocument()
  })

  it('renders IVA brand', () => {
    render(
      <MemoryRouter>
        <Shell>
          <span />
        </Shell>
      </MemoryRouter>,
    )
    expect(screen.getByText('IVA')).toBeInTheDocument()
  })
})
