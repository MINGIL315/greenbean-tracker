'use client'

interface Props {
  origins: string[]
  value: string
  onChange: (v: string) => void
}

export default function OriginFilter({ origins, value, onChange }: Props) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-500 transition-colors cursor-pointer"
    >
      <option value="">전체 원산지</option>
      {origins.map((o) => (
        <option key={o} value={o}>{o}</option>
      ))}
    </select>
  )
}
