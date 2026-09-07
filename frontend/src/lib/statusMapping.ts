import type { ExpenseClaimApiResponse, ViolationCode } from '../types/api'

export type StatusBadgeTone = 'success' | 'warning' | 'danger' | 'neutral'

export type StatusBadgeLabel =
  | 'Auto-Approved'
  | 'Requires Manager'
  | 'Audit Flagged'
  | 'Rejected'
  | 'Pending Review'

export interface StatusBadge {
  label: StatusBadgeLabel
  tone: StatusBadgeTone
  rawStatus: string
}

const AUDIT_FLAGGED_CODES: ViolationCode[] = [
  'possible_duplicate',
  'late_submission',
  'uncapped_category',
]

/**
 * Single source of truth for backend status/violations -> UI badge.
 * No component may string-match a raw backend status itself (research.md §5).
 */
export function mapClaimToStatusBadge(claim: ExpenseClaimApiResponse): StatusBadge {
  const rawStatus = claim.status

  switch (rawStatus) {
    case 'auto_approved':
      return { label: 'Auto-Approved', tone: 'success', rawStatus }
    case 'rejected':
      return { label: 'Rejected', tone: 'danger', rawStatus }
    case 'pending_review': {
      const isAuditFlagged = claim.violations.some((v) => AUDIT_FLAGGED_CODES.includes(v.code))
      return isAuditFlagged
        ? { label: 'Audit Flagged', tone: 'danger', rawStatus }
        : { label: 'Requires Manager', tone: 'warning', rawStatus }
    }
    case 'needs_information':
      return { label: 'Requires Manager', tone: 'warning', rawStatus }
    case 'approved':
      return { label: 'Auto-Approved', tone: 'success', rawStatus }
    case 'withdrawn':
      return { label: 'Pending Review', tone: 'neutral', rawStatus }
    default:
      return { label: 'Pending Review', tone: 'neutral', rawStatus }
  }
}
