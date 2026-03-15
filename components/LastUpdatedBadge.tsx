'use client'

import { formatDistanceToNow } from 'date-fns'
import { ko } from 'date-fns/locale'

export default function LastUpdatedBadge({ date }: { date: string | null }) {
  if (!date) return null
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-zinc-500">
      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
      {formatDistanceToNow(new Date(date), { addSuffix: true, locale: ko })} 수집
    </span>
  )
}
