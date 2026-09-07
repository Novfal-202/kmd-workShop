import { describe, expect, it } from 'vitest'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { server } from '../../src/mocks/server'
import { NewClaimPage } from '../../src/pages/NewClaimPage'
import { renderWithProviders } from '../utils/renderWithProviders'

describe('New claim submission — unrecognized status fallback (FR-017)', () => {
  it('renders the Pending Review fallback badge including the raw status text', async () => {
    server.use(
      http.post('/claims', () =>
        HttpResponse.json(
          {
            id: 'claim-1',
            submitter_id: 'emp-1024',
            category: 'meals',
            amount: 20,
            expense_date: '2026-01-01',
            submission_date: '2026-01-01T00:00:00Z',
            receipt_attached: false,
            status: 'escalated',
            violations: [{ code: 'over_category_cap', detail: 'Escalated to a special review track' }],
          },
          { status: 201 },
        ),
      ),
    )

    const user = userEvent.setup()
    renderWithProviders(<NewClaimPage />)

    await user.type(screen.getByLabelText('Your name'), 'Jane Employee')
  await user.type(screen.getByLabelText('Amount'), '20')
    await user.selectOptions(screen.getByLabelText('Category'), 'meals')
    await user.type(screen.getByLabelText('Expense date'), '2026-01-01')
    await user.click(screen.getByRole('button', { name: /submit claim/i }))

    expect(await screen.findByRole('status')).toHaveTextContent('Pending Review')
    expect(screen.getByText('Escalated to a special review track')).toBeInTheDocument()
  })
})
