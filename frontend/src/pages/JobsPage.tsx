import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api, type JobList } from '../lib/api'

const PAGE_SIZE = 25

export function JobsPage() {
  const [page, setPage] = useState(0)
  const [titleInput, setTitleInput] = useState('')
  const [companyInput, setCompanyInput] = useState('')
  const [locationInput, setLocationInput] = useState('')
  const [filters, setFilters] = useState({ title: '', company: '', location: '' })

  const offset = page * PAGE_SIZE

  const jobsQuery = useQuery({
    queryKey: ['jobs', page, filters],
    queryFn: async () =>
      (
        await api.get<JobList>('/jobs', {
          params: {
            limit: PAGE_SIZE,
            offset,
            title: filters.title || undefined,
            company: filters.company || undefined,
            location: filters.location || undefined,
          },
        })
      ).data,
  })

  function applyFilters() {
    setPage(0)
    setFilters({ title: titleInput, company: companyInput, location: locationInput })
  }

  function clearFilters() {
    setTitleInput('')
    setCompanyInput('')
    setLocationInput('')
    setPage(0)
    setFilters({ title: '', company: '', location: '' })
  }

  const jobs = jobsQuery.data?.items ?? []
  const total = jobsQuery.data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))
  const hasActiveFilters = filters.title || filters.company || filters.location

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <h1 className="mb-1 text-2xl font-semibold text-gray-900">Jobs</h1>
      <p className="mb-6 text-sm text-gray-500">
        {total} normalised postings from Greenhouse + Lever. No matching or scoring yet.
      </p>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          applyFilters()
        }}
        className="mb-4 flex flex-wrap items-end gap-3"
      >
        <div>
          <label htmlFor="filter-title" className="mb-1 block text-xs font-medium text-gray-600">
            Role
          </label>
          <input
            id="filter-title"
            value={titleInput}
            onChange={(e) => setTitleInput(e.target.value)}
            placeholder="e.g. Software Engineer"
            className="w-48 rounded border border-gray-300 px-2 py-1.5 text-sm"
          />
        </div>
        <div>
          <label htmlFor="filter-company" className="mb-1 block text-xs font-medium text-gray-600">
            Company
          </label>
          <input
            id="filter-company"
            value={companyInput}
            onChange={(e) => setCompanyInput(e.target.value)}
            placeholder="e.g. Stripe"
            className="w-40 rounded border border-gray-300 px-2 py-1.5 text-sm"
          />
        </div>
        <div>
          <label htmlFor="filter-location" className="mb-1 block text-xs font-medium text-gray-600">
            Location
          </label>
          <input
            id="filter-location"
            value={locationInput}
            onChange={(e) => setLocationInput(e.target.value)}
            placeholder="e.g. Remote, Bengaluru"
            className="w-44 rounded border border-gray-300 px-2 py-1.5 text-sm"
          />
        </div>
        <button
          type="submit"
          className="rounded bg-gray-900 px-3 py-1.5 text-sm text-white hover:bg-gray-700"
        >
          Search
        </button>
        {hasActiveFilters && (
          <button
            type="button"
            onClick={clearFilters}
            className="text-sm text-gray-500 underline"
          >
            Clear
          </button>
        )}
      </form>

      <div className="overflow-x-auto rounded border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
            <tr>
              <th className="px-3 py-2">Company</th>
              <th className="px-3 py-2">Title</th>
              <th className="px-3 py-2">ATS</th>
              <th className="px-3 py-2">Location</th>
              <th className="px-3 py-2">Remote</th>
              <th className="px-3 py-2">Last seen</th>
              <th className="px-3 py-2">Apply</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {jobs.map((job) => (
              <tr key={job.id}>
                <td className="px-3 py-2 text-gray-700">{job.company_name}</td>
                <td className="px-3 py-2 font-medium text-gray-900">{job.title}</td>
                <td className="px-3 py-2 text-gray-600">{job.ats}</td>
                <td className="px-3 py-2 text-gray-600">{job.locations.join(', ')}</td>
                <td className="px-3 py-2 text-gray-600">{job.remote_policy ?? '—'}</td>
                <td className="px-3 py-2 text-gray-500">
                  {new Date(job.last_seen_at).toLocaleDateString()}
                </td>
                <td className="px-3 py-2">
                  <a
                    href={job.apply_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-blue-600 underline"
                  >
                    View
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {jobs.length === 0 && (
          <p className="p-4 text-sm text-gray-400">
            {hasActiveFilters ? 'No jobs match these filters.' : 'No jobs yet — run worker-ingest to populate this table.'}
          </p>
        )}
      </div>

      {total > 0 && (
        <div className="mt-4 flex items-center justify-between text-sm text-gray-600">
          <span>
            Page {page + 1} of {totalPages} ({total} total)
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="rounded border border-gray-300 px-3 py-1 disabled:opacity-40"
            >
              Previous
            </button>
            <button
              type="button"
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="rounded border border-gray-300 px-3 py-1 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
