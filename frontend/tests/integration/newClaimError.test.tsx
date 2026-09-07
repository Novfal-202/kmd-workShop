import { describe, expect, it } from 'vitest'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { server } from '../../src/mocks/server'
import { NewClaimPage } from '../../src/pages/NewClaimPage'
import { renderWithProviders } from '../utils/renderWithProviders'

describe('New claim submission — network/server failure handling', () => {
  it('shows a distinct error, preserves field values, and retries successfully', async () => {
    let attempt = 0
    server.use(
      http.post('/claims', () => {
        attempt += 1
        if (attempt === 1) {
          return HttpResponse.json({ error_code: 'server_error', message: 'Server unavailable' }, { status: 503 })
        }
        return HttpResponse.json(
          {
            id: 'claim-1',
            submitter_id: 'emp-1024',
            category: 'meals',
            amount: 20,
            expense_date: '2026-01-01',
            submission_date: '2026-01-01T00:00:00Z',
            receipt_attached: false,
            status: 'auto_approved',
            violations: [],
          },
          { status: 201 },
        )
      }),
    )

    const user = userEvent.setup()
    renderWithProviders(<NewClaimPage />)

    await user.type(screen.getByLabelText('Your name'), 'Jane Employee')
  await user.type(screen.getByLabelText('Amount'), '20')
    await user.selectOptions(screen.getByLabelText('Category'), 'meals')
    await user.type(screen.getByLabelText('Expense date'), '2026-01-01')
    await user.click(screen.getByRole('button', { name: /submit claim/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent(/server unavailable/i)
    // Field values remain intact
    expect(screen.getByLabelText('Amount')).toHaveValue('20')
    expect(screen.getByLabelText('Category')).toHaveValue('meals')
    expect(screen.getByLabelText('Expense date')).toHaveValue('2026-01-01')

    await user.click(screen.getByRole('button', { name: /retry/i }))

    expect(await screen.findByRole('status')).toHaveTextContent('Auto-Approved')
    expect(attempt).toBe(2)
  })

  it('shows a network-error message distinct from any status badge', async () => {
    server.use(http.post('/claims', () => HttpResponse.error()))

    const user = userEvent.setup()
    renderWithProviders(<NewClaimPage />)

    await user.type(screen.getByLabelText('Your name'), 'Jane Employee')
  await user.type(screen.getByLabelText('Amount'), '20')
    await user.selectOptions(screen.getByLabelText('Category'), 'meals')
    await user.type(screen.getByLabelText('Expense date'), '2026-01-01')
    await user.click(screen.getByRole('button', { name: /submit claim/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent(/network error/i)
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })
})
