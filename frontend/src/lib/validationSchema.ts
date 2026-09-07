import { z } from 'zod'

export const RECEIPT_REQUIRED_THRESHOLD = 75

export const EXPENSE_CATEGORIES = [
  'meals',
  'travel',
  'lodging',
  'supplies',
  'entertainment',
] as const

function isValidDateString(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false
  const date = new Date(`${value}T00:00:00`)
  return !Number.isNaN(date.getTime())
}

function isNotFutureDate(value: string): boolean {
  if (!isValidDateString(value)) return false
  const date = new Date(`${value}T00:00:00`)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return date.getTime() <= today.getTime()
}

export const claimFormSchema = z
  .object({
    amount: z
      .string()
      .min(1, 'Amount is required')
      .refine((v) => !Number.isNaN(Number(v)), 'Amount must be a number')
      .refine((v) => Number(v) > 0, 'Amount must be greater than zero'),
    category: z.string().min(1, 'Category is required'),
    expenseDate: z
      .string()
      .min(1, 'Expense date is required')
      .refine(isValidDateString, 'Expense date must be a valid date')
      .refine(isNotFutureDate, 'Expense date cannot be in the future'),
    description: z.string().optional(),
    receiptId: z.string().optional(),
  })
  .superRefine((data, ctx) => {
    const amountNumber = Number(data.amount)
    if (
      !Number.isNaN(amountNumber) &&
      amountNumber >= RECEIPT_REQUIRED_THRESHOLD &&
      !data.receiptId
    ) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['receiptId'],
        message: `Receipt required for amounts at or above $${RECEIPT_REQUIRED_THRESHOLD.toFixed(2)}`,
      })
    }
  })

export type ClaimFormDraft = z.infer<typeof claimFormSchema>
