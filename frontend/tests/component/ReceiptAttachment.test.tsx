import { describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ReceiptAttachment } from '../../src/components/ReceiptAttachment'

function setup() {
  const uploadReceipt = vi.fn().mockResolvedValue({
    receipt_id: 'r1',
    kind: 'file',
    filename_or_url: 'receipt.pdf',
  })
  const onChange = vi.fn()
  const { rerender } = render(
    <ReceiptAttachment value={null} onChange={onChange} uploadReceipt={uploadReceipt} />,
  )
  return { uploadReceipt, onChange, rerender }
}

describe('ReceiptAttachment', () => {
  it('shows a filename confirmation after uploading a supported file', async () => {
    const user = userEvent.setup()
    const { onChange, rerender, uploadReceipt } = setup()

    const file = new File(['dummy'], 'receipt.png', { type: 'image/png' })
    await user.upload(screen.getByLabelText('Receipt file'), file)

    await waitFor(() => expect(uploadReceipt).toHaveBeenCalledWith(file))
    await waitFor(() => {
      const lastCall = onChange.mock.calls.at(-1)?.[0]
      expect(lastCall?.uploadStatus).toBe('uploaded')
    })

    rerender(
      <ReceiptAttachment
        value={{ kind: 'file', uploadStatus: 'uploaded', receiptId: 'r1', previewLabel: 'receipt.png' }}
        onChange={onChange}
        uploadReceipt={uploadReceipt}
      />,
    )
    expect(screen.getByText('receipt.png')).toBeInTheDocument()
  })

  it('validates a well-formed URL and shows a link confirmation', async () => {
    const user = userEvent.setup()
    const { onChange, rerender, uploadReceipt } = setup()

    await user.click(screen.getByRole('button', { name: /paste link/i }))
    await user.type(screen.getByLabelText('Receipt link'), 'https://example.com/receipt.pdf')
    await user.click(screen.getByRole('button', { name: /attach/i }))

    await waitFor(() =>
      expect(uploadReceipt).toHaveBeenCalledWith({ url: 'https://example.com/receipt.pdf' }),
    )

    rerender(
      <ReceiptAttachment
        value={{
          kind: 'link',
          url: 'https://example.com/receipt.pdf',
          uploadStatus: 'uploaded',
          receiptId: 'r1',
          previewLabel: 'https://example.com/receipt.pdf',
        }}
        onChange={onChange}
        uploadReceipt={uploadReceipt}
      />,
    )
    expect(screen.getByText('https://example.com/receipt.pdf')).toBeInTheDocument()
  })

  it('rejects a malformed URL without calling uploadReceipt', async () => {
    const user = userEvent.setup()
    const { uploadReceipt } = setup()

    await user.click(screen.getByRole('button', { name: /paste link/i }))
    await user.type(screen.getByLabelText('Receipt link'), 'not-a-url')
    await user.click(screen.getByRole('button', { name: /attach/i }))

    expect(await screen.findByText(/well-formed url/i)).toBeInTheDocument()
    expect(uploadReceipt).not.toHaveBeenCalled()
  })

  it('rejects an oversized file without calling uploadReceipt', async () => {
    const user = userEvent.setup()
    const { uploadReceipt } = setup()

    const bigFile = new File([new Uint8Array(6 * 1024 * 1024)], 'big.png', { type: 'image/png' })
    await user.upload(screen.getByLabelText('Receipt file'), bigFile)

    expect(await screen.findByText(/too large/i)).toBeInTheDocument()
    expect(uploadReceipt).not.toHaveBeenCalled()
  })

  it('rejects an unsupported file type without calling uploadReceipt', async () => {
    const user = userEvent.setup({ applyAccept: false })
    const { uploadReceipt } = setup()

    const file = new File(['dummy'], 'receipt.exe', { type: 'application/x-msdownload' })
    await user.upload(screen.getByLabelText('Receipt file'), file)

    expect(await screen.findByText(/unsupported file type/i)).toBeInTheDocument()
    expect(uploadReceipt).not.toHaveBeenCalled()
  })
})
