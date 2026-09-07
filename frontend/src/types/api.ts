export type ViolationCode =
  | 'over_category_cap'
  | 'missing_required_receipt'
  | 'weekend_policy_violation'
  | 'possible_duplicate'
  | 'late_submission'
  | 'uncapped_category'
  | 'exceeds_auto_approval_threshold'

export interface ViolationReasonApi {
  code: ViolationCode
  detail: string
}

export type ClaimStatus =
  | 'auto_approved'
  | 'pending_review'
  | 'approved'
  | 'rejected'
  | 'needs_information'
  | 'withdrawn'

export interface ReviewDecisionApi {
  reviewer_id: string
  decision: 'approved' | 'rejected' | 'needs_information'
  reason?: string
  decided_at: string
}

export interface ExpenseClaimApiResponse {
  id: string
  submitter_id: string
  category: string
  amount: number
  description?: string
  expense_date: string
  submission_date: string
  receipt_attached: boolean
  receipt_id?: string
  employee_name?: string
  status: ClaimStatus | string
  violations: ViolationReasonApi[]
  review_decision?: ReviewDecisionApi
}

export interface ClaimSubmissionRequest {
  category: string
  amount: number
  description?: string
  expense_date: string
  receipt_attached: boolean
  receipt_id?: string
  employee_name: string
}

export interface ApiValidationError {
  error_code: string
  message: string
}

export type ReceiptKind = 'file' | 'link'

export interface ReceiptReference {
  receipt_id: string
  kind: ReceiptKind
  filename_or_url: string
}

export interface ReceiptAttachmentDraft {
  kind: ReceiptKind
  file?: File
  url?: string
  uploadStatus: 'idle' | 'uploading' | 'uploaded' | 'error'
  receiptId?: string
  previewLabel: string
  errorMessage?: string
}
