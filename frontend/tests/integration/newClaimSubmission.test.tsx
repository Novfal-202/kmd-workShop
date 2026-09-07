import { describe, expect, it } from 'vitest'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { server } from '../../src/mocks/server'
import { NewClaimPage } from '../../src/pages/NewClaimPage'
import { renderWithProviders } from '../utils/renderWithProviders'
import fixtures from '../../src/mocks/fixtures/mock-responses.json'

const mockById = Object.fromEntries(fixtures.mocks.map((m) => [m.id, m]))

async function fillAndSubmitValidClaim() {
  const user = userEvent.setup()
  renderWithProviders(<NewClaimPage />)

  await user.type(screen.getByLabelText('Amount'), '20')
  await user.selectOptions(screen.getByLabelText('Category'), 'meals')
  await user.type(screen.getByLabelText('Expense date'), '2026-01-01')

  const submitButton = await screen.findByRole('button', { name: /submit claim/i })
  await user.click(submitButton)
}

describe('New claim submission renders the correct status badge', () => {
  it.each([
    ['auto-approved-1', 'Auto-Approved'],
    ['requires-manager-1', 'Requires Manager'],
    ['audit-flagged-1', 'Audit Flagged'],
    ['rejected-1', 'Rejected'],
  ])('renders "%s" badge for mock "%s"', async (mockId, expectedLabel) => {
    const mock = mockById[mockId]
    server.use(
      http.post('/claims', () => HttpResponse.json(mock.body, { status: mock.http_status })),
    )

    await fillAndSubmitValidClaim()

    expect(await screen.findByRole('status')).toHaveTextContent(expectedLabel)

    for (const violation of (mock.body as { violations?: { detail: string }[] }).violations ?? []) {
      expect(screen.getByText(violation.detail)).toBeInTheDocument()
    }
  })
})
