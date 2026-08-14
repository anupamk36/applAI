import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, type JobPreferences, type Settings } from '../lib/api'
import { TagListInput } from '../components/TagListInput'
import { CountryChips } from '../components/CountryChips'

const THRESHOLD_STEPS: { value: number; label: string }[] = [
  { value: 0.6, label: 'Broad' },
  { value: 0.75, label: 'Balanced' },
  { value: 0.9, label: 'Selective' },
]

function closestStepIndex(value: number): number {
  let best = 0
  let bestDiff = Infinity
  THRESHOLD_STEPS.forEach((step, i) => {
    const diff = Math.abs(step.value - value)
    if (diff < bestDiff) {
      bestDiff = diff
      best = i
    }
  })
  return best
}

export function PreferencesPage() {
  const queryClient = useQueryClient()
  const settingsQuery = useQuery({
    queryKey: ['settings'],
    queryFn: async () => (await api.get<Settings>('/settings')).data,
  })

  const [threshold, setThreshold] = useState(0.75)
  const [dailyCap, setDailyCap] = useState(10)
  const [prefs, setPrefs] = useState<JobPreferences | null>(null)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (settingsQuery.data) {
      setThreshold(settingsQuery.data.threshold)
      setDailyCap(settingsQuery.data.daily_cap)
      setPrefs(settingsQuery.data.job_preferences)
    }
  }, [settingsQuery.data])

  const saveMutation = useMutation({
    mutationFn: async () =>
      (
        await api.patch('/settings', {
          threshold,
          daily_cap: dailyCap,
          job_preferences: prefs,
        })
      ).data,
    onSuccess: (data: Settings) => {
      queryClient.setQueryData(['settings'], data)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    },
  })

  if (!prefs) {
    return <div className="mx-auto max-w-2xl px-4 py-10 text-sm text-gray-400">Loading…</div>
  }

  const stepIndex = closestStepIndex(threshold)

  return (
    <div className="mx-auto max-w-2xl px-4 py-10">
      <h1 className="mb-6 text-2xl font-semibold text-gray-900">Preferences</h1>

      <section className="mb-8">
        <h2 className="mb-2 text-lg font-medium text-gray-900">Target countries</h2>
        <p className="mb-3 text-sm text-gray-500">
          Defaults to India. Add more to broaden where the agent looks for and applies to roles.
        </p>
        <CountryChips
          selected={prefs.target_countries}
          onChange={(target_countries) => setPrefs({ ...prefs, target_countries })}
        />
        {prefs.target_countries.length === 0 && (
          <p className="mt-2 text-sm text-red-600">Select at least one country.</p>
        )}
      </section>

      <section className="mb-8">
        <h2 className="mb-2 text-lg font-medium text-gray-900">Match threshold</h2>
        <input
          type="range"
          min={0}
          max={THRESHOLD_STEPS.length - 1}
          step={1}
          value={stepIndex}
          onChange={(e) => setThreshold(THRESHOLD_STEPS[Number(e.target.value)].value)}
          className="w-full"
        />
        <div className="flex justify-between text-xs text-gray-500">
          {THRESHOLD_STEPS.map((s) => (
            <span key={s.label}>{s.label}</span>
          ))}
        </div>
      </section>

      <section className="mb-8">
        <h2 className="mb-2 text-lg font-medium text-gray-900">Daily application cap</h2>
        <input
          type="number"
          min={1}
          max={25}
          value={dailyCap}
          onChange={(e) => setDailyCap(Math.min(25, Math.max(1, Number(e.target.value))))}
          className="w-24 rounded border border-gray-300 px-3 py-2"
        />
        <span className="ml-2 text-sm text-gray-500">max 25</span>
      </section>

      <section className="mb-8 flex flex-col gap-4">
        <TagListInput
          label="Target titles"
          values={prefs.target_titles}
          onChange={(v) => setPrefs({ ...prefs, target_titles: v })}
          placeholder="e.g. Senior Backend Engineer"
        />
        <TagListInput
          label="Locations"
          values={prefs.locations}
          onChange={(v) => setPrefs({ ...prefs, locations: v })}
          placeholder="e.g. Bengaluru, Remote"
        />
        <TagListInput
          label="Industries"
          values={prefs.industries}
          onChange={(v) => setPrefs({ ...prefs, industries: v })}
        />
        <TagListInput
          label="Company size bands"
          values={prefs.company_size_bands}
          onChange={(v) => setPrefs({ ...prefs, company_size_bands: v })}
          placeholder="e.g. 50-200, 1000+"
        />
        <TagListInput
          label="Company blocklist"
          values={prefs.blocklist_companies}
          onChange={(v) => setPrefs({ ...prefs, blocklist_companies: v })}
        />
      </section>

      <section className="mb-8 flex gap-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Min CTC (₹ LPA)</label>
          <input
            type="number"
            value={prefs.ctc_min ?? ''}
            onChange={(e) =>
              setPrefs({ ...prefs, ctc_min: e.target.value === '' ? null : Number(e.target.value) })
            }
            className="w-32 rounded border border-gray-300 px-3 py-2"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Max CTC (₹ LPA)</label>
          <input
            type="number"
            value={prefs.ctc_max ?? ''}
            onChange={(e) =>
              setPrefs({ ...prefs, ctc_max: e.target.value === '' ? null : Number(e.target.value) })
            }
            className="w-32 rounded border border-gray-300 px-3 py-2"
          />
        </div>
      </section>

      <button
        onClick={() => saveMutation.mutate()}
        disabled={saveMutation.isPending || prefs.target_countries.length === 0}
        className="rounded bg-gray-900 px-4 py-2 text-white hover:bg-gray-700 disabled:opacity-50"
      >
        {saveMutation.isPending ? 'Saving…' : 'Save preferences'}
      </button>
      {saved && <span className="ml-3 text-sm text-green-600">Saved</span>}
    </div>
  )
}
