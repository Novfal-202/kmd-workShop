import { describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '../../src/mocks/server'
import { fetchClaimHistory, submitClaim } from '../../src/lib/apiClient'

const claimWithStringAmount = {
  id: 'claim-1',
  submitter_id: 'emp-1024',
  category: 'meals',
  amount: '15.5', // the real backend serializes Decimal as a JSON string, not a number
  expense_date: '2026-01-01',
  submission_date: '2026-01-01T00:00:00Z',
  receipt_attached: false,
  status: 'pending_review',
  violations: [],
}

describe('apiClient — normalizes the backend amount field', () => {
  it('coerces a string amount to a number on claim submission', async () => {
    server.use(http.post('/claims', () => HttpResponse.json(claimWithStringAmount, { status: 201 })))

    const claim = await submitClaim({
      employee_name: 'Jane Employee',
      category: 'meals',
      amount: 15.5,
      expense_date: '2026-01-01',
      receipt_attached: false,
    })

    expect(claim.amount).toBe(15.5)
    expect(typeof claim.amount).toBe('number')
  })

  it('coerces string amounts to numbers when fetching claim history', async () => {
    server.use(http.get('/claims', () => HttpResponse.json([claimWithStringAmount], { status: 200 })))

    const claims = await fetchClaimHistory()

    expect(claims[0].amount).toBe(15.5)
    expect(typeof claims[0].amount).toBe('number')
  })
})
