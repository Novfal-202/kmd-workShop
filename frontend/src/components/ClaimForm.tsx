import { useEffect, useState } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import {
  claimFormSchema,
  EXPENSE_CATEGORIES,
  RECEIPT_REQUIRED_THRESHOLD,
  type ClaimFormDraft,
} from '../lib/validationSchema'
import type { ReceiptAttachmentDraft, ReceiptReference } from '../types/api'
import { ReceiptAttachment } from './ReceiptAttachment'

export interface ClaimFormProps {
  defaultValues?: Partial<ClaimFormDraft>
  onSubmit: (draft: ClaimFormDraft) => Promise<void>
  submitting: boolean
  uploadReceipt: (input: File | { url: string }) => Promise<ReceiptReference>
  onFieldsChange?: (values: Partial<ClaimFormDraft>) => void
}

export function ClaimForm({
  defaultValues,
  onSubmit,
  submitting,
  uploadReceipt,
  onFieldsChange,
}: ClaimFormProps) {
  const {
    register,
    handleSubmit,
    control,
    watch,
    setValue,
    formState: { errors, isValid },
  } = useForm<ClaimFormDraft>({
    resolver: zodResolver(claimFormSchema),
    mode: 'onChange',
    defaultValues: {
      employeeName: '',
      amount: '',
      category: '',
      expenseDate: '',
      description: '',
      receiptId: undefined,
      ...defaultValues,
    },
  })

  const watchedValues = watch()
  const [receiptUploading, setReceiptUploading] = useState(false)

  useEffect(() => {
    onFieldsChange?.(watchedValues)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    watchedValues.employeeName,
    watchedValues.amount,
    watchedValues.category,
    watchedValues.expenseDate,
    watchedValues.description,
  ])

  const amountNumber = Number(watchedValues.amount)
  const receiptRequired =
    !Number.isNaN(amountNumber) && amountNumber >= RECEIPT_REQUIRED_THRESHOLD

  return (
    <form
      onSubmit={handleSubmit(async (values) => {
        await onSubmit(values)
      })}
    >
      <div className="space-y-4">
      <div>
        <label htmlFor="employeeName" className="block text-sm font-medium">
          Your name
        </label>
        <input
          id="employeeName"
          type="text"
          className="mt-1 w-full rounded border px-3 py-2"
          aria-invalid={!!errors.employeeName}
          aria-describedby={errors.employeeName ? 'employeeName-error' : undefined}
          {...register('employeeName')}
        />
        {errors.employeeName && (
          <p id="employeeName-error" role="alert" className="mt-1 text-sm text-red-600">
            {errors.employeeName.message}
          </p>
        )}
      </div>

      <div>
        <label htmlFor="amount" className="block text-sm font-medium">
          Amount
        </label>
        <input
          id="amount"
          type="text"
          inputMode="decimal"
          className="mt-1 w-full rounded border px-3 py-2"
          aria-invalid={!!errors.amount}
          aria-describedby={errors.amount ? 'amount-error' : undefined}
          {...register('amount')}
        />
        {errors.amount && (
          <p id="amount-error" role="alert" className="mt-1 text-sm text-red-600">
            {errors.amount.message}
          </p>
        )}
      </div>

      <div>
        <label htmlFor="category" className="block text-sm font-medium">
          Category
        </label>
        <select
          id="category"
          className="mt-1 w-full rounded border px-3 py-2"
          aria-invalid={!!errors.category}
          aria-describedby={errors.category ? 'category-error' : undefined}
          {...register('category')}
        >
          <option value="">Select a category</option>
          {EXPENSE_CATEGORIES.map((category) => (
            <option key={category} value={category}>
              {category}
            </option>
          ))}
        </select>
        {errors.category && (
          <p id="category-error" role="alert" className="mt-1 text-sm text-red-600">
            {errors.category.message}
          </p>
        )}
      </div>

      <div>
        <label htmlFor="expenseDate" className="block text-sm font-medium">
          Expense date
        </label>
        <input
          id="expenseDate"
          type="date"
          className="mt-1 w-full rounded border px-3 py-2"
          aria-invalid={!!errors.expenseDate}
          aria-describedby={errors.expenseDate ? 'expenseDate-error' : undefined}
          {...register('expenseDate')}
        />
        {errors.expenseDate && (
          <p id="expenseDate-error" role="alert" className="mt-1 text-sm text-red-600">
            {errors.expenseDate.message}
          </p>
        )}
      </div>

      <div>
        <label htmlFor="description" className="block text-sm font-medium">
          Description (optional)
        </label>
        <textarea
          id="description"
          className="mt-1 w-full rounded border px-3 py-2"
          {...register('description')}
        />
      </div>

      <div>
        <span className="block text-sm font-medium">Receipt</span>
        <Controller
          control={control}
          name="receiptId"
          render={({ field }) => {
            const currentDraft: ReceiptAttachmentDraft | null = field.value
              ? {
                  kind: 'file',
                  uploadStatus: 'uploaded',
                  receiptId: field.value,
                  previewLabel: field.value,
                }
              : null
            return (
              <ReceiptAttachment
                value={currentDraft}
                uploadReceipt={uploadReceipt}
                onChange={(draft) => {
                  setValue('receiptId', draft?.receiptId, { shouldValidate: true })
                  setReceiptUploading(draft?.uploadStatus === 'uploading')
                }}
              />
            )
          }}
        />
        {receiptRequired && !watchedValues.receiptId && (
          <p role="alert" className="mt-1 text-sm text-amber-600">
            {errors.receiptId?.message ??
              `Receipt required for amounts at or above $${RECEIPT_REQUIRED_THRESHOLD.toFixed(2)}`}
          </p>
        )}
      </div>
      </div>

      <div
        data-testid="submit-bar"
        className="-mx-6 -mb-6 mt-6 flex justify-end border-t border-slate-200 bg-slate-50 px-6 py-4 sm:-mx-8 sm:-mb-8 sm:px-8"
      >
        <button
          type="submit"
          disabled={!isValid || submitting || receiptUploading}
          className="rounded bg-slate-800 px-4 py-2 text-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? 'Submitting…' : receiptUploading ? 'Uploading receipt…' : 'Submit claim'}
        </button>
      </div>
    </form>
  )
}
