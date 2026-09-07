import { http, HttpResponse } from 'msw'
import fixtures from './fixtures/mock-responses.json'
import type { ExpenseClaimApiResponse } from '../types/api'

export const mockClaims: ExpenseClaimApiResponse[] = fixtures.mocks
  .filter((mock): mock is (typeof fixtures.mocks)[number] & { http_status: 200 | 201 } =>
    mock.http_status < 400,
  )
  .map((mock) => mock.body as ExpenseClaimApiResponse)

let receiptCounter = 0

export const handlers = [
  http.post('/claims', async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>
    const response: ExpenseClaimApiResponse = {
      id: `mock-claim-${Date.now()}`,
      submitter_id: 'emp-1024',
      category: String(body.category ?? ''),
      amount: Number(body.amount ?? 0),
      description: typeof body.description === 'string' ? body.description : undefined,
      expense_date: String(body.expense_date ?? ''),
      submission_date: new Date().toISOString(),
      receipt_attached: Boolean(body.receipt_attached),
      receipt_id: typeof body.receipt_id === 'string' ? body.receipt_id : undefined,
      status: 'auto_approved',
      violations: [],
    }
    return HttpResponse.json(response, { status: 201 })
  }),

  http.get('/claims', () => {
    return HttpResponse.json(mockClaims, { status: 200 })
  }),

  http.post('/receipts', async () => {
    receiptCounter += 1
    return HttpResponse.json(
      {
        receipt_id: `mock-receipt-${receiptCounter}`,
        kind: 'file',
        filename_or_url: `receipt-${receiptCounter}`,
      },
      { status: 201 },
    )
  }),

  http.delete('/receipts/:receiptId', () => {
    return new HttpResponse(null, { status: 204 })
  }),
]
