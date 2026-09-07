import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ClaimHistoryList } from '../../src/components/ClaimHistoryList'
import fixtures from '../../src/mocks/fixtures/mock-responses.json'
import type { ExpenseClaimApiResponse } from '../../src/types/api'

const claims = fixtures.mocks
  .filter((m) => m.http_status < 400)
  .map((m) => m.body as ExpenseClaimApiResponse)

describe('ClaimHistoryList', () => {
  it('renders as a table with amount, category, date, status badge, and violation tags for each claim', () => {
    render(<ClaimHistoryList claims={claims} />)

    expect(screen.getByRole('table')).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: /employee/i })).toBeInTheDocument()

    for (const claim of claims) {
      expect(screen.getAllByText(`$${claim.amount.toFixed(2)}`).length).toBeGreaterThan(0)
      expect(screen.getAllByText(claim.category).length).toBeGreaterThan(0)
      expect(screen.getAllByText(claim.expense_date).length).toBeGreaterThan(0)
    }

    for (const violation of claims.flatMap((c) => c.violations)) {
      expect(screen.getAllByText(violation.detail).length).toBeGreaterThan(0)
    }

    expect(screen.getAllByRole('status').length).toBe(claims.length)
    expect(screen.getAllByRole('row')).toHaveLength(claims.length + 1) // +1 header row
  })

  it('shows an empty-state message when there are no claims', () => {
    render(<ClaimHistoryList claims={[]} />)
    expect(screen.getByText(/haven't submitted any claims/i)).toBeInTheDocument()
  })
})
