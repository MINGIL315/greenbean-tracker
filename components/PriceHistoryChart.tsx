'use client'

import { useState, useMemo } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { format, subDays } from 'date-fns'
import { ko } from 'date-fns/locale'
import { PriceEntry, PriceTier } from '@/types'

interface HistoryEntry extends PriceEntry {
  price_tiers: PriceTier[]
}

interface Props {
  entries: HistoryEntry[]
}

type Period = 7 | 30 | 90 | 'all'

export default function PriceHistoryChart({ entries }: Props) {
  const [period, setPeriod] = useState<Period>(30)

  const filtered = useMemo(() => {
    if (period === 'all') return entries
    const cutoff = subDays(new Date(), period)
    return entries.filter((e) => new Date(e.scraped_at) >= cutoff)
  }, [entries, period])

  const chartData = filtered.map((e) => {
    const bulk5kg = e.price_tiers.find((t) => t.tier_type === 'bulk' && (t.min_kg ?? 0) >= 5)
    const membership = e.price_tiers.find((t) => t.tier_type === 'membership')
    const subscription = e.price_tiers.find((t) => t.tier_type === 'subscription')
    return {
      date: format(new Date(e.scraped_at), 'MM/dd', { locale: ko }),
      기본가: e.base_price_per_kg,
      '구간가(5kg)': bulk5kg?.price_per_kg ?? null,
      멤버십가: membership?.price_per_kg ?? null,
      구독가: subscription?.price_per_kg ?? null,
    }
  })

  const prices = filtered.map((e) => e.base_price_per_kg)
  const maxPrice = prices.length ? Math.max(...prices) : 0
  const minPrice = prices.length ? Math.min(...prices) : 0
  const avgPrice = prices.length ? Math.round(prices.reduce((a, b) => a + b, 0) / prices.length) : 0

  const fmt = (n: number) => n.toLocaleString('ko-KR') + '원'

  return (
    <div className="space-y-4">
      {/* 기간 필터 */}
      <div className="flex gap-2">
        {([7, 30, 90, 'all'] as Period[]).map((p) => (
          <button
            key={p}
            onClick={() => setPeriod(p)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              period === p
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
            }`}
          >
            {p === 'all' ? '전체' : `${p}일`}
          </button>
        ))}
      </div>

      {/* 차트 */}
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} />
          <YAxis tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
          <Tooltip formatter={(value) => [`${Number(value).toLocaleString()}원`, '']} />
          <Legend />
          <Line type="monotone" dataKey="기본가" stroke="#6b7280" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="구간가(5kg)" stroke="#3b82f6" strokeWidth={1.5} dot={false} strokeDasharray="4 2" />
          <Line type="monotone" dataKey="멤버십가" stroke="#9333ea" strokeWidth={1.5} dot={false} strokeDasharray="4 2" />
          <Line type="monotone" dataKey="구독가" stroke="#22c55e" strokeWidth={1.5} dot={false} strokeDasharray="4 2" />
        </LineChart>
      </ResponsiveContainer>

      {/* 요약 카드 */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: '최고가', value: fmt(maxPrice), color: 'text-red-500' },
          { label: '최저가', value: fmt(minPrice), color: 'text-green-500' },
          { label: '평균가', value: fmt(avgPrice), color: 'text-blue-500' },
        ].map(({ label, value, color }) => (
          <div key={label} className="rounded-lg border border-gray-200 dark:border-gray-700 p-3 text-center">
            <div className="text-xs text-gray-500 dark:text-gray-400">{label}</div>
            <div className={`text-lg font-bold font-tabular-nums ${color}`}>{value}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
