import { mapClaimToStatusBadge } from '../lib/statusMapping'
import type { ExpenseClaimApiResponse } from '../types/api'
import { StatusBadge } from './StatusBadge'
import { ViolationTag } from './ViolationTag'

export interface ClaimHistoryListProps {
  claims: ExpenseClaimApiResponse[]
}

export function ClaimHistoryList({ claims }: ClaimHistoryListProps) {
  if (claims.length === 0) {
    return <p className="text-sm text-slate-500">You haven't submitted any claims yet.</p>
  }

  return (
    <ul className="divide-y divide-slate-200">
      {claims.map((claim) => {
        const badge = mapClaimToStatusBadge(claim)
        return (
          <li key={claim.id} className="flex flex-col gap-2 py-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="font-medium">
                ${claim.amount.toFixed(2)} — {claim.category}
              </p>
              <p className="text-sm text-slate-500">{claim.expense_date}</p>
              {claim.violations.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {claim.violations.map((violation) => (
                    <ViolationTag key={violation.code} violation={violation} />
                  ))}
                </div>
              )}
            </div>
            <StatusBadge badge={badge} />
          </li>
        )
      })}
    </ul>
  )
}
