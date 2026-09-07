import type { ViolationReasonApi } from '../types/api'

const ICON_BY_CODE: Record<string, string> = {
  over_category_cap: '\u{1F4B0}',
  missing_required_receipt: '\u{1F9FE}',
  weekend_policy_violation: '\u{1F4C5}',
  possible_duplicate: '\u{1F501}',
  late_submission: '⏰',
  uncapped_category: '❗',
  exceeds_auto_approval_threshold: '\u{1F4C8}',
}

export interface ViolationTagProps {
  violation: ViolationReasonApi
}

export function ViolationTag({ violation }: ViolationTagProps) {
  return (
    <span className="inline-flex items-center gap-1 rounded border border-red-200 bg-red-50 px-2 py-0.5 text-xs text-red-700">
      <span aria-hidden="true">{ICON_BY_CODE[violation.code] ?? '❗'}</span>
      {violation.detail}
    </span>
  )
}
