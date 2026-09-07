import { ClaimHistoryList } from '../components/ClaimHistoryList'
import { useClaimHistory } from '../lib/apiClient'

export function ClaimHistoryPage() {
  const { data, isLoading, isError, error } = useClaimHistory()

  return (
    <div className="mx-auto max-w-xl space-y-4 p-4">
      <h1 className="text-xl font-semibold">Your claim history</h1>
      {isLoading && <p className="text-sm text-slate-500">Loading your claims…</p>}
      {isError && (
        <p role="alert" className="text-sm text-red-600">
          {(error as { message?: string })?.message ?? 'Could not load claim history.'}
        </p>
      )}
      {data && <ClaimHistoryList claims={data} />}
    </div>
  )
}
