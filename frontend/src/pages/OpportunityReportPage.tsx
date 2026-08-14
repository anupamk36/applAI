import { useQuery } from '@tanstack/react-query'
import { api, type MatchedJob, type OpportunityReport } from '../lib/api'

function humanize(key: string): string {
  return key.replace(/_/g, ' ')
}

function MatchRow({ job }: { job: MatchedJob }) {
  return (
    <li className="flex items-center justify-between gap-4 rounded border border-gray-200 p-3">
      <div>
        <p className="text-sm font-medium text-gray-900">{job.title}</p>
        <p className="text-xs text-gray-500">{job.company_name}</p>
        {job.limiting_factors.length > 0 && (
          <p className="mt-1 text-xs text-gray-400">
            Limiting factors: {job.limiting_factors.map(humanize).join(', ')}
          </p>
        )}
      </div>
      <div className="flex shrink-0 items-center gap-3">
        <span className="rounded bg-gray-100 px-2 py-1 text-xs font-medium text-gray-700">
          {Math.round(job.score * 100)}%
        </span>
        <button
          type="button"
          disabled
          title="Auto-apply isn't built yet (Phase 1.6) — this button is a placeholder."
          className="cursor-not-allowed rounded border border-gray-300 px-2 py-1 text-xs text-gray-400"
        >
          Apply anyway
        </button>
      </div>
    </li>
  )
}

export function OpportunityReportPage() {
  const reportQuery = useQuery({
    queryKey: ['opportunity-report'],
    queryFn: async () => (await api.get<OpportunityReport>('/matches/opportunity-report')).data,
  })

  const report = reportQuery.data

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="mb-1 text-2xl font-semibold text-gray-900">Opportunity Report</h1>
      <p className="mb-6 text-sm text-gray-500">
        Why you saw what you saw — gating made visible, not an invisible constraint.
      </p>

      {!report && <p className="text-sm text-gray-400">Loading…</p>}

      {report && (
        <>
          <section className="mb-8 rounded border border-gray-200 p-4">
            <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
              <div>
                <dt className="text-gray-500">Scanned</dt>
                <dd className="text-lg font-semibold text-gray-900">{report.scanned}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Passed filters</dt>
                <dd className="text-lg font-semibold text-gray-900">{report.passed_hard_filters}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Met quality bar</dt>
                <dd className="text-lg font-semibold text-gray-900">{report.met_quality_bar}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Below threshold</dt>
                <dd className="text-lg font-semibold text-gray-900">{report.below_threshold}</dd>
              </div>
            </dl>
            <p className="mt-3 text-xs text-gray-400">
              Threshold: {Math.round(report.threshold * 100)}%
            </p>
          </section>

          <section className="mb-8">
            <h2 className="mb-2 text-lg font-medium text-gray-900">Excluded by hard filter</h2>
            <ul className="flex flex-col gap-1 text-sm text-gray-600">
              {Object.entries(report.excluded_by_reason)
                .filter(([, count]) => count > 0)
                .sort(([, a], [, b]) => b - a)
                .map(([reason, count]) => (
                  <li key={reason} className="flex justify-between">
                    <span>{humanize(reason)}</span>
                    <span className="text-gray-400">{count}</span>
                  </li>
                ))}
              {Object.values(report.excluded_by_reason).every((c) => c === 0) && (
                <li className="text-gray-400">Nothing excluded yet.</li>
              )}
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="mb-2 text-lg font-medium text-gray-900">
              Met your quality bar ({report.matched.length})
            </h2>
            <ul className="flex flex-col gap-2">
              {report.matched.map((job) => (
                <MatchRow key={job.job_id} job={job} />
              ))}
              {report.matched.length === 0 && (
                <li className="text-sm text-gray-400">
                  Nothing above threshold yet — see near-misses below.
                </li>
              )}
            </ul>
          </section>

          <section>
            <h2 className="mb-2 text-lg font-medium text-gray-900">
              Below threshold ({report.below_threshold})
            </h2>
            <ul className="flex flex-col gap-2">
              {report.near_misses.map((job) => (
                <MatchRow key={job.job_id} job={job} />
              ))}
              {report.near_misses.length === 0 && (
                <li className="text-sm text-gray-400">No near-misses.</li>
              )}
            </ul>
          </section>
        </>
      )}
    </div>
  )
}
