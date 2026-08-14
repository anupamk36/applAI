import { COUNTRIES } from '../lib/countries'

interface Props {
  selected: string[]
  onChange: (codes: string[]) => void
}

export function CountryChips({ selected, onChange }: Props) {
  function toggle(code: string) {
    onChange(selected.includes(code) ? selected.filter((c) => c !== code) : [...selected, code])
  }

  return (
    <div className="flex flex-wrap gap-2">
      {COUNTRIES.map((c) => {
        const active = selected.includes(c.code)
        return (
          <button
            key={c.code}
            type="button"
            onClick={() => toggle(c.code)}
            className={`rounded-full border px-3 py-1 text-sm ${
              active
                ? 'border-gray-900 bg-gray-900 text-white'
                : 'border-gray-300 text-gray-600 hover:border-gray-500'
            }`}
          >
            {c.name}
          </button>
        )
      })}
    </div>
  )
}
