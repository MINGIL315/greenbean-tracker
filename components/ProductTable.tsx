'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ProductWithPrices, PriceTier } from '@/types'

interface Props {
  products: ProductWithPrices[]
  globalLowestPrice?: number
  onAlertClick?: (product: ProductWithPrices) => void
}

type SortKey = 'name' | 'origin' | 'price' | 'stock'
type SortDir = 'asc' | 'desc'

function getCheapestPrice(basePrice: number, tiers: PriceTier[]): number {
  return Math.min(basePrice, ...tiers.map((t) => t.price_per_kg))
}

export default function ProductTable({ products, globalLowestPrice, onAlertClick }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>('price')
  const [sortDir, setSortDir] = useState<SortDir>('asc')

  if (products.length === 0) {
    return <p className="px-5 py-6 text-xs text-zinc-600">상품 없음</p>
  }

  function handleSort(key: SortKey) {
    if (sortKey === key) setSortDir(sortDir === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('asc') }
  }

  const sorted = [...products].sort((a, b) => {
    const aEntry = a.price_entries?.[0]
    const bEntry = b.price_entries?.[0]
    let cmp = 0
    if (sortKey === 'name') cmp = a.name.localeCompare(b.name, 'ko')
    else if (sortKey === 'origin') cmp = (a.origin_country ?? '').localeCompare(b.origin_country ?? '', 'ko')
    else if (sortKey === 'price') {
      const aPrice = aEntry ? getCheapestPrice(aEntry.base_price_per_kg, aEntry.price_tiers ?? []) : Infinity
      const bPrice = bEntry ? getCheapestPrice(bEntry.base_price_per_kg, bEntry.price_tiers ?? []) : Infinity
      cmp = aPrice - bPrice
    } else if (sortKey === 'stock') {
      cmp = (aEntry?.is_in_stock ? 0 : 1) - (bEntry?.is_in_stock ? 0 : 1)
    }
    return sortDir === 'asc' ? cmp : -cmp
  })

  function SortBtn({ label, sk }: { label: string; sk: SortKey }) {
    const active = sortKey === sk
    return (
      <button
        onClick={() => handleSort(sk)}
        className={`flex items-center gap-1 transition-colors ${active ? 'text-zinc-200' : 'text-zinc-500 hover:text-zinc-300'}`}
      >
        {label}
        <span className="text-[10px]">
          {active ? (sortDir === 'asc' ? '▲' : '▼') : <span className="opacity-30">▲</span>}
        </span>
      </button>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-zinc-800">
            <th className="px-5 py-2.5 text-left font-medium text-xs">
              <SortBtn label="상품명" sk="name" />
            </th>
            <th className="px-3 py-2.5 text-left font-medium text-xs">
              <SortBtn label="원산지" sk="origin" />
            </th>
            <th className="px-3 py-2.5 text-left font-medium text-xs text-zinc-500">품종</th>
            <th className="px-3 py-2.5 text-left font-medium text-xs text-zinc-500">가공</th>
            <th className="px-3 py-2.5 text-left font-medium text-xs">
              <SortBtn label="최저가/kg" sk="price" />
            </th>
            <th className="px-3 py-2.5 text-left font-medium text-xs">
              <SortBtn label="재고" sk="stock" />
            </th>
            <th className="px-3 py-2.5" />
          </tr>
        </thead>
        <tbody>
          {sorted.map((product) => {
            const entry = product.price_entries?.[0]
            const tiers = entry?.price_tiers ?? []
            const basePrice = entry?.base_price_per_kg ?? 0
            const cheapest = basePrice > 0 ? getCheapestPrice(basePrice, tiers) : 0
            const isLowest = globalLowestPrice != null && cheapest === globalLowestPrice

            return (
              <tr
                key={product.id}
                className="border-b border-zinc-800/50 hover:bg-zinc-800/30 transition-colors group"
              >
                {/* 상품명 */}
                <td className="px-5 py-3">
                  <Link
                    href={`/product/${product.id}`}
                    className="text-zinc-200 hover:text-emerald-400 transition-colors"
                  >
                    {product.name}
                  </Link>
                </td>

                {/* 원산지 */}
                <td className="px-3 py-3">
                  {product.origin_country ? (
                    <Link
                      href={`/origin/${product.origin_country}`}
                      className="text-zinc-400 hover:text-zinc-200 transition-colors text-xs"
                    >
                      {product.origin_country}
                    </Link>
                  ) : (
                    <span className="text-zinc-600 text-xs">—</span>
                  )}
                </td>

                {/* 품종 */}
                <td className="px-3 py-3 text-xs text-zinc-500">
                  {product.variety ?? <span className="text-zinc-700">—</span>}
                </td>

                {/* 가공 */}
                <td className="px-3 py-3 text-xs text-zinc-500">
                  {product.process_method ?? <span className="text-zinc-700">—</span>}
                </td>

                {/* 최저가 */}
                <td className="px-3 py-3 tabular">
                  {entry ? (
                    <span className={`font-semibold ${isLowest ? 'text-emerald-400' : 'text-zinc-200'}`}>
                      {entry.is_anomaly && (
                        <span className="mr-1 text-xs text-amber-400">🚨</span>
                      )}
                      {isLowest && (
                        <span className="mr-1 text-[10px] text-emerald-500">●</span>
                      )}
                      {cheapest.toLocaleString('ko-KR')}
                      <span className="ml-0.5 text-xs font-normal text-zinc-500">원</span>
                    </span>
                  ) : (
                    <span className="text-zinc-700">—</span>
                  )}
                </td>

                {/* 재고 */}
                <td className="px-3 py-3">
                  {entry?.is_in_stock ? (
                    <span className="inline-flex items-center gap-1 text-xs text-emerald-400">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                      재고
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-xs text-zinc-600">
                      <span className="w-1.5 h-1.5 rounded-full bg-zinc-600" />
                      품절
                    </span>
                  )}
                </td>

                {/* 알림 */}
                <td className="px-3 py-3">
                  <button
                    onClick={() => onAlertClick?.(product)}
                    className="text-zinc-700 hover:text-amber-400 transition-colors opacity-0 group-hover:opacity-100"
                    title="가격 알림 설정"
                  >
                    🔔
                  </button>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
