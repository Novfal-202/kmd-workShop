import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type {
  ApiValidationError,
  ClaimSubmissionRequest,
  ExpenseClaimApiResponse,
  ReceiptReference,
} from '../types/api'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export interface ApiError {
  message: string
  retryable: boolean
}

function isApiValidationError(value: unknown): value is ApiValidationError {
  return typeof value === 'object' && value !== null && 'message' in value
}

/**
 * The live backend serializes `amount` (a Pydantic v2 Decimal) as a JSON string
 * (e.g. "15.5"), not a number, even though the contract documents it as `number`.
 * Normalize at the boundary so the rest of the app can rely on `amount: number`.
 */
function normalizeClaim(claim: ExpenseClaimApiResponse): ExpenseClaimApiResponse {
  return { ...claim, amount: Number(claim.amount) }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      headers: init?.body instanceof FormData ? undefined : { 'Content-Type': 'application/json' },
      ...init,
    })
  } catch {
    const error: ApiError = { message: 'Network error — please check your connection and retry.', retryable: true }
    throw error
  }

  if (response.status === 401) {
    const error: ApiError = { message: 'Your session has expired. Please sign in again.', retryable: false }
    throw error
  }

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`
    try {
      const body: unknown = await response.json()
      if (isApiValidationError(body)) message = body.message
    } catch {
      // response body was not JSON; keep the generic message
    }
    const retryable = response.status >= 500
    const error: ApiError = { message, retryable }
    throw error
  }

  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export async function submitClaim(
  payload: ClaimSubmissionRequest,
): Promise<ExpenseClaimApiResponse> {
  const claim = await request<ExpenseClaimApiResponse>('/claims', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
  return normalizeClaim(claim)
}

export async function fetchClaimHistory(): Promise<ExpenseClaimApiResponse[]> {
  const claims = await request<ExpenseClaimApiResponse[]>('/claims', { method: 'GET' })
  return claims.map(normalizeClaim)
}

export async function uploadReceipt(input: File | { url: string }): Promise<ReceiptReference> {
  if (input instanceof File) {
    const formData = new FormData()
    formData.append('file', input)
    return request<ReceiptReference>('/receipts', { method: 'POST', body: formData })
  }
  return request<ReceiptReference>('/receipts', {
    method: 'POST',
    body: JSON.stringify({ url: input.url }),
  })
}

export async function deleteReceipt(receiptId: string): Promise<void> {
  return request<void>(`/receipts/${receiptId}`, { method: 'DELETE' })
}

export function useSubmitClaim() {
  return useMutation<ExpenseClaimApiResponse, ApiError, ClaimSubmissionRequest>({
    mutationFn: submitClaim,
  })
}

export const CLAIM_HISTORY_QUERY_KEY = ['claims', 'history'] as const

export function useClaimHistory() {
  return useQuery<ExpenseClaimApiResponse[], ApiError>({
    queryKey: CLAIM_HISTORY_QUERY_KEY,
    queryFn: fetchClaimHistory,
    refetchOnMount: true,
    refetchOnWindowFocus: true,
  })
}

export function useInvalidateClaimHistory() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: CLAIM_HISTORY_QUERY_KEY })
}
