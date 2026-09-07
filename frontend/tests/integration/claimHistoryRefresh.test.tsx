import { describe, expect, it } from 'vitest'
import { screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { server } from '../../src/mocks/server'
import { ClaimHistoryPage } from '../../src/pages/ClaimHistoryPage'
import { renderWithProviders } from '../utils/renderWithProviders'

const baseClaim = {
  id: 'claim-1',
  submitter_id: 'emp-1024',
  category: 'travel',
  amount: 610,
  expense_date: '2026-09-01',
  submission_date: '2026-09-06T09:05:00Z',
  receipt_attached: true,
  violations: [] as { code: string; detail: string }[],
}

describe('Claim history reflects reviewer decisions on reload (US4)', () => {
  it('shows the updated status after a simulated backend-side reviewer decision and a reload', async () => {
    server.use(
      http.get('/claims', () =>
        HttpResponse.json([{ ...baseClaim, status: 'pending_review' }], { status: 200 }),
      ),
    )

    const first = renderWithProviders(<ClaimHistoryPage />)
    expect(await screen.findByRole('status')).toHaveTextContent('Requires Manager')
    first.unmount()

    server.use(
      http.get('/claims', () =>
        HttpResponse.json([{ ...baseClaim, status: 'approved' }], { status: 200 }),
      ),
    )

    renderWithProviders(<ClaimHistoryPage />)
    expect(await screen.findByRole('status')).toHaveTextContent('Auto-Approved')
  })
})
