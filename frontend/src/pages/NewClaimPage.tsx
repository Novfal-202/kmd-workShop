import { useState } from 'react'
import { ClaimForm } from '../components/ClaimForm'
import { StatusBadge } from '../components/StatusBadge'
import { ViolationTag } from '../components/ViolationTag'
import { mapClaimToStatusBadge } from '../lib/statusMapping'
import { uploadReceipt, useSubmitClaim } from '../lib/apiClient'
import { clearDraft, rehydrateDraft, saveDraft } from '../lib/draftPersistence'
import type { ClaimFormDraft } from '../lib/validationSchema'
import type { ApiError } from '../lib/apiClient'

export function NewClaimPage() {
  const submitClaimMutation = useSubmitClaim()
  const [lastDraft, setLastDraft] = useState<ClaimFormDraft | null>(null)
  const [needsReauth, setNeedsReauth] = useState(false)

  const persistedDraft = rehydrateDraft()

  async function handleSubmit(draft: ClaimFormDraft) {
    setLastDraft(draft)
    try {
      await submitClaimMutation.mutateAsync({
        category: draft.category,
        amount: Number(draft.amount),
        description: draft.description,
        expense_date: draft.expenseDate,
        receipt_attached: !!draft.receiptId,
        receipt_id: draft.receiptId,
      })
      clearDraft()
    } catch (err) {
      const apiError = err as ApiError
      if (apiError.message.includes('session has expired')) {
        setNeedsReauth(true)
      }
    }
  }

  function handleRetry() {
    if (lastDraft) void handleSubmit(lastDraft)
  }

  const phase = submitClaimMutation.isPending
    ? 'submitting'
    : submitClaimMutation.isSuccess
      ? 'succeeded'
      : submitClaimMutation.isError
        ? 'failed'
        : 'idle'

  return (
    <div className="mx-auto max-w-xl space-y-6 p-4">
      <h1 className="text-xl font-semibold">Submit a new expense claim</h1>

      {needsReauth && (
        <div role="alert" className="rounded border border-amber-300 bg-amber-50 p-3 text-sm">
          Your session has expired. Please sign in again — your entered claim details are still
          here and will not be lost.
        </div>
      )}

      {phase === 'failed' && (
        <div role="alert" className="flex items-center justify-between rounded border border-red-300 bg-red-50 p-3 text-sm">
          <span>{(submitClaimMutation.error as ApiError | null)?.message ?? 'Submission failed.'}</span>
          <button type="button" onClick={handleRetry} className="ml-3 rounded bg-red-600 px-3 py-1 text-white">
            Retry
          </button>
        </div>
      )}

      {phase === 'succeeded' && submitClaimMutation.data && (
        <div className="space-y-2 rounded border p-3">
          <StatusBadge badge={mapClaimToStatusBadge(submitClaimMutation.data)} />
          {submitClaimMutation.data.violations.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {submitClaimMutation.data.violations.map((violation) => (
                <ViolationTag key={violation.code} violation={violation} />
              ))}
            </div>
          )}
        </div>
      )}

      <ClaimForm
        defaultValues={
          lastDraft ?? (persistedDraft ? { ...persistedDraft } : undefined)
        }
        submitting={phase === 'submitting'}
        uploadReceipt={uploadReceipt}
        onFieldsChange={(values) => {
          saveDraft({
            amount: values.amount ?? '',
            category: values.category ?? '',
            expenseDate: values.expenseDate ?? '',
            description: values.description,
          })
        }}
        onSubmit={handleSubmit}
      />
    </div>
  )
}
