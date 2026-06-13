import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { FileDropzone } from '../features/file-upload/FileDropzone'

describe('FileDropzone', () => {
  it('renders drag-drop zone', () => {
    render(<FileDropzone onFile={() => {}} />)
    expect(screen.getByText(/Перетащите файл/i)).toBeInTheDocument()
  })

  it('shows supported extensions', () => {
    render(<FileDropzone onFile={() => {}} />)
    expect(screen.getByText(/csv/i)).toBeInTheDocument()
  })

  it('shows client-side error for unsupported extension', () => {
    const onFile = vi.fn()
    render(<FileDropzone onFile={onFile} />)

    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File(['data'], 'bad.exe', { type: 'application/octet-stream' })
    Object.defineProperty(input, 'files', { value: [file], configurable: true })
    fireEvent.change(input)

    expect(screen.getByText(/не поддерживается/i)).toBeInTheDocument()
    expect(onFile).not.toHaveBeenCalled()
  })

  it('calls onFile for valid extension', () => {
    const onFile = vi.fn()
    render(<FileDropzone onFile={onFile} />)

    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File(['time_s,signal\n0,1'], 'data.csv', { type: 'text/csv' })
    Object.defineProperty(input, 'files', { value: [file], configurable: true })
    fireEvent.change(input)

    expect(onFile).toHaveBeenCalledWith(file)
  })
})
