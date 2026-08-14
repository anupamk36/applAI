import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, type AnswerBankEntry, type Fact } from '../lib/api'
import { CountryChips } from '../components/CountryChips'

function AnswerBankSection() {
  const queryClient = useQueryClient()
  const answersQuery = useQuery({
    queryKey: ['answer-bank'],
    queryFn: async () => (await api.get<AnswerBankEntry[]>('/answer-bank')).data,
  })

  const [experienceYears, setExperienceYears] = useState('')
  const [authorizedCountries, setAuthorizedCountries] = useState<string[]>([])
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (!answersQuery.data) return
    const years = answersQuery.data.find((a) => a.semantic_key === 'total_experience_years')
    const countries = answersQuery.data.find((a) => a.semantic_key === 'work_authorized_countries')
    setExperienceYears(years?.value ?? '')
    setAuthorizedCountries(countries?.value ? countries.value.split(',').filter(Boolean) : [])
  }, [answersQuery.data])

  const saveMutation = useMutation({
    mutationFn: async () => {
      await api.put('/answer-bank/total_experience_years', { value: experienceYears })
      await api.put('/answer-bank/work_authorized_countries', {
        value: authorizedCountries.join(','),
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['answer-bank'] })
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    },
  })

  return (
    <section className="mb-8">
      <h2 className="mb-2 text-lg font-medium text-gray-900">Answer bank</h2>
      <p className="mb-3 text-sm text-gray-500">
        Used to filter matches (experience band, work authorization) — not a resume field, kept
        separate from your fact base.
      </p>
      <div className="mb-4">
        <label
          htmlFor="experience-years"
          className="mb-1 block text-sm font-medium text-gray-700"
        >
          Total years of experience
        </label>
        <input
          id="experience-years"
          type="number"
          min={0}
          step={0.5}
          value={experienceYears}
          onChange={(e) => setExperienceYears(e.target.value)}
          className="w-32 rounded border border-gray-300 px-3 py-2"
        />
      </div>
      <div className="mb-4">
        <span className="mb-1 block text-sm font-medium text-gray-700">
          Countries you can work in without sponsorship
        </span>
        <CountryChips selected={authorizedCountries} onChange={setAuthorizedCountries} />
      </div>
      <button
        onClick={() => saveMutation.mutate()}
        disabled={saveMutation.isPending}
        className="rounded bg-gray-900 px-4 py-2 text-white hover:bg-gray-700 disabled:opacity-50"
      >
        {saveMutation.isPending ? 'Saving…' : 'Save answer bank'}
      </button>
      {saved && <span className="ml-3 text-sm text-green-600">Saved</span>}
    </section>
  )
}

export function ResumePage() {
  const fileInput = useRef<HTMLInputElement>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const factsQuery = useQuery({
    queryKey: ['facts'],
    queryFn: async () => (await api.get<Fact[]>('/facts')).data,
  })

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData()
      form.append('file', file)
      return (await api.post('/resumes', form)).data
    },
    onSuccess: () => {
      setUploadError(null)
      queryClient.invalidateQueries({ queryKey: ['facts'] })
    },
    onError: () => setUploadError('Upload failed — only PDF/DOCX supported'),
  })

  const confirmMutation = useMutation({
    mutationFn: (factId: string) => api.post(`/facts/${factId}/confirm`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['facts'] }),
  })

  const rejectMutation = useMutation({
    mutationFn: (factId: string) => api.delete(`/facts/${factId}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['facts'] }),
  })

  const facts = factsQuery.data ?? []
  const pending = facts.filter((f) => !f.confirmed_at)
  const confirmed = facts.filter((f) => f.confirmed_at)

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="mb-6 text-2xl font-semibold text-gray-900">Resume &amp; Facts</h1>

      <div className="mb-8 rounded border border-dashed border-gray-300 p-6 text-center">
        <input
          ref={fileInput}
          type="file"
          accept=".pdf,.docx"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) uploadMutation.mutate(file)
          }}
        />
        <button
          onClick={() => fileInput.current?.click()}
          disabled={uploadMutation.isPending}
          className="rounded bg-gray-900 px-4 py-2 text-white hover:bg-gray-700 disabled:opacity-50"
        >
          {uploadMutation.isPending ? 'Uploading…' : 'Upload resume (PDF/DOCX)'}
        </button>
        {uploadError && <p className="mt-2 text-sm text-red-600">{uploadError}</p>}
      </div>

      <AnswerBankSection />

      <section className="mb-8">
        <h2 className="mb-2 text-lg font-medium text-gray-900">
          Awaiting confirmation ({pending.length})
        </h2>
        <p className="mb-3 text-sm text-gray-500">
          Nothing enters your fact base until you confirm it.
        </p>
        <ul className="flex flex-col gap-2">
          {pending.map((fact) => (
            <li
              key={fact.id}
              className="flex items-start justify-between gap-4 rounded border border-gray-200 p-3"
            >
              <div>
                <span className="mb-1 inline-block rounded bg-gray-100 px-2 py-0.5 text-xs uppercase text-gray-600">
                  {fact.kind}
                </span>
                <p className="whitespace-pre-wrap text-sm text-gray-800">
                  {fact.payload.name ?? fact.payload.raw_text}
                </p>
              </div>
              <div className="flex shrink-0 gap-2">
                <button
                  onClick={() => confirmMutation.mutate(fact.id)}
                  className="rounded bg-green-600 px-2 py-1 text-xs text-white hover:bg-green-500"
                >
                  Confirm
                </button>
                <button
                  onClick={() => rejectMutation.mutate(fact.id)}
                  className="rounded bg-red-50 px-2 py-1 text-xs text-red-600 hover:bg-red-100"
                >
                  Reject
                </button>
              </div>
            </li>
          ))}
          {pending.length === 0 && (
            <li className="text-sm text-gray-400">No candidate facts waiting on you.</li>
          )}
        </ul>
      </section>

      <section>
        <h2 className="mb-2 text-lg font-medium text-gray-900">
          Confirmed fact base ({confirmed.length})
        </h2>
        <ul className="flex flex-col gap-2">
          {confirmed.map((fact) => (
            <li key={fact.id} className="rounded border border-gray-100 bg-gray-50 p-3">
              <span className="mb-1 inline-block rounded bg-gray-200 px-2 py-0.5 text-xs uppercase text-gray-600">
                {fact.kind}
              </span>
              <p className="whitespace-pre-wrap text-sm text-gray-700">
                {fact.payload.name ?? fact.payload.raw_text}
              </p>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
