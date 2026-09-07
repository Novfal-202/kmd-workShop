import type { StatusBadge as StatusBadgeModel } from '../lib/statusMapping'

const TONE_STYLES: Record<StatusBadgeModel['tone'], string> = {
  success: 'bg-green-100 text-green-800 border-green-300',
  warning: 'bg-amber-100 text-amber-800 border-amber-300',
  danger: 'bg-red-100 text-red-800 border-red-300',
  neutral: 'bg-gray-100 text-gray-800 border-gray-300',
}

const TONE_ICON: Record<StatusBadgeModel['tone'], string> = {
  success: '✓',
  warning: '⚠',
  danger: '✕',
  neutral: '•',
}

export interface StatusBadgeProps {
  badge: StatusBadgeModel
}

export function StatusBadge({ badge }: StatusBadgeProps) {
  return (
    <span
      role="status"
      className={`inline-flex items-center gap-1 rounded-full border px-3 py-1 text-sm font-medium ${TONE_STYLES[badge.tone]}`}
    >
      <span aria-hidden="true">{TONE_ICON[badge.tone]}</span>
      {badge.label}
    </span>
  )
}
