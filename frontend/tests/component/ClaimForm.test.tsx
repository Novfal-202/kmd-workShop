import { describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ClaimForm } from '../../src/components/ClaimForm'

function renderForm() {
  const onSubmit = vi.fn().mockResolvedValue(undefined)
  const uploadReceipt = vi.fn().mockResolvedValue({
    receipt_id: 'r1',
    kind: 'file',
    filename_or_url: 'receipt.pdf',
  })
  render(<ClaimForm submitting={false} onSubmit={onSubmit} uploadReceipt={uploadReceipt} />)
  return { onSubmit, uploadReceipt }
}

describe('ClaimForm', () => {
  it('disables submit and shows an inline error for a negative amount', async () => {
    const user = userEvent.setup()
    renderForm()

    await user.type(screen.getByLabelText('Amount'), '-5')
    await user.tab()

    expect(await screen.findByText(/greater than zero/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /submit claim/i })).toBeDisabled()
  })

  it('shows an inline error for a future expense date', async () => {
    const user = userEvent.setup()
    renderForm()

    await user.type(screen.getByLabelText('Expense date'), '2099-01-01')
    await user.tab()

    expect(await screen.findByText(/cannot be in the future/i)).toBeInTheDocument()
  })

  it('shows an inline error when category is left empty and other fields are valid', async () => {
    const user = userEvent.setup()
    renderForm()

    await user.type(screen.getByLabelText('Amount'), '20')
    await user.type(screen.getByLabelText('Expense date'), '2026-01-01')
    await user.tab()

    expect(screen.getByRole('button', { name: /submit claim/i })).toBeDisabled()
  })

  it('shows an inline error when the employee name is left empty', async () => {
    const user = userEvent.setup()
    renderForm()

    await user.type(screen.getByLabelText('Amount'), '20')
    await user.selectOptions(screen.getByLabelText('Category'), 'meals')
    await user.type(screen.getByLabelText('Expense date'), '2026-01-01')
    await user.type(screen.getByLabelText('Your name'), 'a')
    await user.clear(screen.getByLabelText('Your name'))

    expect(await screen.findByText(/your name is required/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /submit claim/i })).toBeDisabled()
  })

  it('renders the submit control inside its attached footer-bar container', () => {
    renderForm()

    const submitBar = screen.getByTestId('submit-bar')
    expect(submitBar).toContainElement(screen.getByRole('button', { name: /submit claim/i }))
  })

  it('clears all errors and enables submit once every field is valid', async () => {
    const user = userEvent.setup()
    renderForm()

    await user.type(screen.getByLabelText('Your name'), 'Jane Employee')
    await user.type(screen.getByLabelText('Amount'), '20')
    await user.selectOptions(screen.getByLabelText('Category'), 'meals')
    await user.type(screen.getByLabelText('Expense date'), '2026-01-01')

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /submit claim/i })).toBeEnabled()
    })
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})
