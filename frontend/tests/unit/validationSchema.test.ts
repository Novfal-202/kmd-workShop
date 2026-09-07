import { describe, expect, it } from 'vitest'
import { claimFormSchema, RECEIPT_REQUIRED_THRESHOLD } from '../../src/lib/validationSchema'

const validBase = {
  amount: '25.00',
  category: 'meals',
  expenseDate: '2026-01-01',
  description: '',
  receiptId: undefined as string | undefined,
}

describe('claimFormSchema', () => {
  it('accepts a fully valid draft', () => {
    const result = claimFormSchema.safeParse(validBase)
    expect(result.success).toBe(true)
  })

  it('rejects a zero amount', () => {
    const result = claimFormSchema.safeParse({ ...validBase, amount: '0' })
    expect(result.success).toBe(false)
  })

  it('rejects a negative amount', () => {
    const result = claimFormSchema.safeParse({ ...validBase, amount: '-5' })
    expect(result.success).toBe(false)
  })

  it('rejects a non-numeric amount', () => {
    const result = claimFormSchema.safeParse({ ...validBase, amount: 'abc' })
    expect(result.success).toBe(false)
  })

  it('rejects a missing category', () => {
    const result = claimFormSchema.safeParse({ ...validBase, category: '' })
    expect(result.success).toBe(false)
  })

  it('rejects an invalid expense date', () => {
    const result = claimFormSchema.safeParse({ ...validBase, expenseDate: 'not-a-date' })
    expect(result.success).toBe(false)
  })

  it('rejects a future expense date', () => {
    const future = new Date()
    future.setFullYear(future.getFullYear() + 1)
    const isoFuture = future.toISOString().slice(0, 10)
    const result = claimFormSchema.safeParse({ ...validBase, expenseDate: isoFuture })
    expect(result.success).toBe(false)
  })

  it(`requires a receipt when amount is at or above the $${RECEIPT_REQUIRED_THRESHOLD} threshold`, () => {
    const result = claimFormSchema.safeParse({
      ...validBase,
      amount: String(RECEIPT_REQUIRED_THRESHOLD),
      receiptId: undefined,
    })
    expect(result.success).toBe(false)
  })

  it('passes the threshold check once a receiptId is present', () => {
    const result = claimFormSchema.safeParse({
      ...validBase,
      amount: String(RECEIPT_REQUIRED_THRESHOLD),
      receiptId: 'receipt-1',
    })
    expect(result.success).toBe(true)
  })
})
