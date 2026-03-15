'use client'

export type PriceType = 'base' | 'bulk' | 'membership' | 'subscription'

interface Props {
  active: PriceType[]
  onChange: (types: PriceType[]) => void
}

const OPTIONS: { value: PriceType; label: string }[] = [
  { value: 'base', label: '기본가' },
  { value: 'bulk', label: '구간가' },
  { value: 'membership', label: '멤버십가' },
  { value: 'subscription', label: '구독가' },
]

export default function PriceTypeToggle({ active, onChange }: Props) {
  const toggle = (type: PriceType) => {
    if (active.includes(type)) {
      onChange(active.filter((t) => t !== type))
    } else {
      onChange([...active, type])
    }
  }

  return (
    <div className="flex gap-2 flex-wrap">
      {OPTIONS.map(({ value, label }) => (
        <button
          key={value}
          onClick={() => toggle(value)}
          className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
            active.includes(value)
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  )
}
