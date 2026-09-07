import { useRef, useState } from 'react'
import type { ReceiptAttachmentDraft, ReceiptReference } from '../types/api'

export const ALLOWED_FILE_TYPES = ['image/png', 'image/jpeg', 'application/pdf']
export const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024 // 5MB

function isValidHttpUrl(value: string): boolean {
  try {
    const parsed = new URL(value)
    return parsed.protocol === 'http:' || parsed.protocol === 'https:'
  } catch {
    return false
  }
}

export interface ReceiptAttachmentProps {
  value: ReceiptAttachmentDraft | null
  onChange: (draft: ReceiptAttachmentDraft | null) => void
  uploadReceipt: (input: File | { url: string }) => Promise<ReceiptReference>
}

export function ReceiptAttachment({ value, onChange, uploadReceipt }: ReceiptAttachmentProps) {
  const [mode, setMode] = useState<'file' | 'link'>(value?.kind ?? 'file')
  const [linkInput, setLinkInput] = useState(value?.kind === 'link' ? (value.url ?? '') : '')
  const [rejectionMessage, setRejectionMessage] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  async function handleFileSelected(file: File) {
    setRejectionMessage(null)
    if (!ALLOWED_FILE_TYPES.includes(file.type)) {
      setRejectionMessage('Unsupported file type. Please attach a PNG, JPEG, or PDF file.')
      return
    }
    if (file.size > MAX_FILE_SIZE_BYTES) {
      setRejectionMessage('File is too large. Maximum size is 5MB.')
      return
    }

    const uploadingDraft: ReceiptAttachmentDraft = {
      kind: 'file',
      file,
      uploadStatus: 'uploading',
      previewLabel: file.name,
    }
    onChange(uploadingDraft)

    try {
      const reference = await uploadReceipt(file)
      onChange({
        kind: 'file',
        file,
        uploadStatus: 'uploaded',
        receiptId: reference.receipt_id,
        previewLabel: file.name,
      })
    } catch {
      onChange({
        kind: 'file',
        file,
        uploadStatus: 'error',
        previewLabel: file.name,
        errorMessage: 'Upload failed. Please try again.',
      })
    }
  }

  async function handleLinkSubmit() {
    setRejectionMessage(null)
    if (!isValidHttpUrl(linkInput)) {
      setRejectionMessage('Please paste a well-formed URL (starting with http:// or https://).')
      return
    }

    const uploadingDraft: ReceiptAttachmentDraft = {
      kind: 'link',
      url: linkInput,
      uploadStatus: 'uploading',
      previewLabel: linkInput,
    }
    onChange(uploadingDraft)

    try {
      const reference = await uploadReceipt({ url: linkInput })
      onChange({
        kind: 'link',
        url: linkInput,
        uploadStatus: 'uploaded',
        receiptId: reference.receipt_id,
        previewLabel: linkInput,
      })
    } catch {
      onChange({
        kind: 'link',
        url: linkInput,
        uploadStatus: 'error',
        previewLabel: linkInput,
        errorMessage: 'Could not attach this link. Please try again.',
      })
    }
  }

  function handleRemove() {
    setRejectionMessage(null)
    setLinkInput('')
    if (fileInputRef.current) fileInputRef.current.value = ''
    onChange(null)
  }

  return (
    <div className="space-y-2">
      <div className="flex gap-2 text-sm">
        <button
          type="button"
          className={`rounded px-3 py-1 ${mode === 'file' ? 'bg-slate-800 text-white' : 'bg-slate-100'}`}
          onClick={() => setMode('file')}
        >
          Upload file
        </button>
        <button
          type="button"
          className={`rounded px-3 py-1 ${mode === 'link' ? 'bg-slate-800 text-white' : 'bg-slate-100'}`}
          onClick={() => setMode('link')}
        >
          Paste link
        </button>
      </div>

      {mode === 'file' && !value && (
        <input
          ref={fileInputRef}
          type="file"
          aria-label="Receipt file"
          accept={ALLOWED_FILE_TYPES.join(',')}
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) void handleFileSelected(file)
          }}
        />
      )}

      {mode === 'link' && !value && (
        <div className="flex gap-2">
          <input
            type="text"
            aria-label="Receipt link"
            placeholder="https://example.com/receipt.pdf"
            className="flex-1 rounded border px-2 py-1 text-sm"
            value={linkInput}
            onChange={(e) => setLinkInput(e.target.value)}
          />
          <button
            type="button"
            className="rounded bg-slate-800 px-3 py-1 text-sm text-white"
            onClick={() => void handleLinkSubmit()}
          >
            Attach
          </button>
        </div>
      )}

      {rejectionMessage && <p className="text-sm text-red-600">{rejectionMessage}</p>}

      {value && (
        <div className="flex items-center justify-between rounded border bg-slate-50 px-3 py-2 text-sm">
          <span>
            {value.uploadStatus === 'uploading' && 'Uploading… '}
            {value.previewLabel}
            {value.uploadStatus === 'error' && value.errorMessage && (
              <span className="ml-2 text-red-600">{value.errorMessage}</span>
            )}
          </span>
          <button type="button" className="text-slate-500 underline" onClick={handleRemove}>
            Remove
          </button>
        </div>
      )}
    </div>
  )
}
