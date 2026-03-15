'use client'

import { useState } from 'react'
import { PriceTier } from '@/types'

interface Props {
  basePrice: number
  tiers: PriceTier[]
  isAnomaly?: boolean
  showBulk?: boolean
  showMembership?: boolean
  showSubscription?: boolean
  isLowest?: boolean
}

export default function PriceCell({
  basePrice,
  tiers,
  isAnomaly = false,
  showBulk = true,
  showMembership = true,
  showSubscription = true,
  isLowest = false,
}: Props) {
  const [showTooltip, setShowTooltip] = useState(false)

  const bulkTiers = tiers.filter((t) => t.tier_type === 'bulk')
  const membershipTier = tiers.find((t) => t.tier_type === 'membership')
  const subscriptionTier = tiers.find((t) => t.tier_type === 'subscription')

  const fmt = (n: number) => n.toLocaleString('ko-KR') + '원'

  return (
    <div className="space-y-1">
      {/* 기본가 */}
      <div
        className={`flex items-center gap-1 font-tabular-nums text-sm ${
          isLowest ? 'text-green-600 dark:text-green-400 font-bold' : 'text-gray-800 dark:text-gray-200'
        }`}
      >
        {isAnomaly && <span title="이상값">🚨</span>}
        <span>{fmt(basePrice)}</span>
        {isLowest && <span className="text-xs bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded px-1">최저</span>}
      </div>

      {/* 구간가 (hover 툴팁) */}
      {showBulk && bulkTiers.length > 0 && (
        <div
          className="relative inline-block"
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
        >
          <span className="cursor-pointer text-blue-600 dark:text-blue-400 text-xs underline decoration-dotted">
            구간가 ▾
          </span>
          {showTooltip && (
            <div className="absolute z-50 bottom-full left-0 mb-1 min-w-[160px] rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-lg p-2 text-xs">
              {bulkTiers.map((t, i) => (
                <div key={i} className="flex justify-between gap-4 py-0.5 text-blue-700 dark:text-blue-300">
                  <span>{t.min_kg != null ? `${t.min_kg}kg 이상` : '기본'}</span>
                  <span className="font-tabular-nums">{fmt(t.price_per_kg)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 멤버십가 */}
      {showMembership && membershipTier && (
        <div className="text-purple-600 dark:text-purple-400 text-xs font-tabular-nums">
          🔖 {fmt(membershipTier.price_per_kg)}
        </div>
      )}

      {/* 구독가 */}
      {showSubscription && subscriptionTier && (
        <div className="text-green-600 dark:text-green-400 text-xs font-tabular-nums">
          🔄 {fmt(subscriptionTier.price_per_kg)}
        </div>
      )}
    </div>
  )
}
