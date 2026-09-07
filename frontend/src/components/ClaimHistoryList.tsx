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
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] border-collapse text-left text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
            <th scope="col" className="py-2 pr-4 font-medium">
              Employee
            </th>
            <th scope="col" className="py-2 pr-4 font-medium">
              Amount
            </th>
            <th scope="col" className="py-2 pr-4 font-medium">
              Category
            </th>
            <th scope="col" className="py-2 pr-4 font-medium">
              Date
            </th>
            <th scope="col" className="py-2 pr-4 font-medium">
              Status
            </th>
            <th scope="col" className="py-2 font-medium">
              Violations
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {claims.map((claim) => {
            const badge = mapClaimToStatusBadge(claim)
            return (
              <tr key={claim.id} className="align-top">
                <td className="py-5 pr-4 font-medium">{claim.employee_name || '—'}</td>
                <td className="py-5 pr-4">${claim.amount.toFixed(2)}</td>
                <td className="py-5 pr-4">{claim.category}</td>
                <td className="py-5 pr-4 text-slate-500">{claim.expense_date}</td>
                <td className="py-5 pr-4">
                  <StatusBadge badge={badge} />
                </td>
                <td className="py-5">
                  {claim.violations.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {claim.violations.map((violation) => (
                        <ViolationTag key={violation.code} violation={violation} />
                      ))}
                    </div>
                  ) : (
                    <span className="text-slate-400">—</span>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
