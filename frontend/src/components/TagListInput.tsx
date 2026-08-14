import { useState, type KeyboardEvent } from 'react'

interface Props {
  label: string
  values: string[]
  onChange: (values: string[]) => void
  placeholder?: string
}

export function TagListInput({ label, values, onChange, placeholder }: Props) {
  const [draft, setDraft] = useState('')

  function addTag() {
    const value = draft.trim()
    if (value && !values.includes(value)) {
      onChange([...values, value])
    }
    setDraft('')
  }

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      addTag()
    }
  }

  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-gray-700">{label}</label>
      <div className="flex flex-wrap items-center gap-2 rounded border border-gray-300 p-2">
        {values.map((v) => (
          <span
            key={v}
            className="flex items-center gap-1 rounded bg-gray-100 px-2 py-1 text-xs text-gray-700"
          >
            {v}
            <button
              type="button"
              onClick={() => onChange(values.filter((x) => x !== v))}
              className="text-gray-400 hover:text-gray-700"
            >
              ×
            </button>
          </span>
        ))}
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={onKeyDown}
          onBlur={addTag}
          placeholder={placeholder}
          className="min-w-[8rem] flex-1 border-none text-sm outline-none"
        />
      </div>
    </div>
  )
}
