import { ClaimHistoryList } from '../components/ClaimHistoryList'
import { useClaimHistory } from '../lib/apiClient'

export function ClaimHistoryPage() {
  const { data, isLoading, isError, error } = useClaimHistory()

  return (
    <div className="mx-auto max-w-3xl space-y-4 px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
      <h1 className="text-xl font-semibold">Your claim history</h1>
      {isLoading && <p className="text-sm text-slate-500">Loading your claims…</p>}
      {isError && (
        <p role="alert" className="text-sm text-red-600">
          {(error as { message?: string })?.message ?? 'Could not load claim history.'}
        </p>
      )}
      {data && (
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <ClaimHistoryList claims={data} />
        </div>
      )}
    </div>
  )
}
