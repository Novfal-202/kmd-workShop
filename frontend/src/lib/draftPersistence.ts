const DRAFT_STORAGE_KEY = 'expense-portal:new-claim-draft'

export interface PersistedDraft {
  employeeName: string
  amount: string
  category: string
  expenseDate: string
  description?: string
}

export function saveDraft(draft: PersistedDraft): void {
  try {
    sessionStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(draft))
  } catch {
    // sessionStorage may be unavailable (private browsing, quota); losing draft
    // persistence is non-fatal, the form itself still holds the values.
  }
}

export function rehydrateDraft(): PersistedDraft | null {
  try {
    const raw = sessionStorage.getItem(DRAFT_STORAGE_KEY)
    if (!raw) return null
    return JSON.parse(raw) as PersistedDraft
  } catch {
    return null
  }
}

export function clearDraft(): void {
  try {
    sessionStorage.removeItem(DRAFT_STORAGE_KEY)
  } catch {
    // no-op
  }
}
