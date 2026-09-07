import { describe, expect, it } from 'vitest'
import { mapClaimToStatusBadge } from '../../src/lib/statusMapping'
import fixtures from '../../src/mocks/fixtures/mock-responses.json'
import type { ExpenseClaimApiResponse } from '../../src/types/api'

describe('mapClaimToStatusBadge', () => {
  for (const mock of fixtures.mocks) {
    if (mock.http_status >= 400) continue // error-shape mocks have no claim to map

    it(`maps "${mock.id}" to ui_status "${mock.ui_status}"`, () => {
      const badge = mapClaimToStatusBadge(mock.body as ExpenseClaimApiResponse)
      expect(badge.label).toBe(mock.ui_status)
    })
  }

  it('falls back to Pending Review for an unrecognized status (FR-017)', () => {
    const claim: ExpenseClaimApiResponse = {
      id: 'x',
      submitter_id: 'emp-1',
      category: 'meals',
      amount: 10,
      expense_date: '2026-01-01',
      submission_date: '2026-01-01T00:00:00Z',
      receipt_attached: false,
      status: 'escalated',
      violations: [],
    }
    const badge = mapClaimToStatusBadge(claim)
    expect(badge.label).toBe('Pending Review')
    expect(badge.tone).toBe('neutral')
    expect(badge.rawStatus).toBe('escalated')
  })

  it('never throws on an unrecognized status', () => {
    const claim = {
      id: 'x',
      submitter_id: 'emp-1',
      category: 'meals',
      amount: 10,
      expense_date: '2026-01-01',
      submission_date: '2026-01-01T00:00:00Z',
      receipt_attached: false,
      status: 'totally_unknown',
      violations: [],
    } as ExpenseClaimApiResponse
    expect(() => mapClaimToStatusBadge(claim)).not.toThrow()
  })
})
