'use client'

import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { CompanyWithProducts, ProductWithPrices } from '@/types'
import ProductTable from './ProductTable'
import ErrorBoundary from './ErrorBoundary'

interface Props {
  company: CompanyWithProducts
  originFilter: string
  onAlertClick?: (product: ProductWithPrices) => void
}

export default function CompanyCard({ company, originFilter, onAlertClick }: Props) {
  const [open, setOpen] = useState(true)

  const filteredProducts = originFilter
    ? company.products.filter((p) => p.origin_country === originFilter)
    : company.products

  const lastScraped = company.products
    .flatMap((p) => p.price_entries)
    .map((e) => e?.scraped_at)
    .filter(Boolean)
    .sort()
    .at(-1) ?? null

  const allPrices = filteredProducts.flatMap((p) => {
    const entry = p.price_entries?.[0]
    if (!entry) return []
    return [entry.base_price_per_kg, ...(entry.price_tiers ?? []).map((t: any) => t.price_per_kg)]
  }).filter((p) => p > 0)
  const lowestPrice = allPrices.length > 0 ? Math.min(...allPrices) : undefined

  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900 overflow-hidden">
      {/* 카드 헤더 */}
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-5 py-3.5 text-left hover:bg-zinc-800/40 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="font-semibold text-zinc-100 text-sm">{company.name}</span>
          <span className="text-xs text-zinc-500 tabular">{filteredProducts.length}개 상품</span>
          {lastScraped && (
            <span className="hidden sm:flex items-center gap-1.5 text-xs text-zinc-600">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              {new Date(lastScraped).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })} 수집
            </span>
          )}
        </div>
        <ChevronDown
          className={`h-4 w-4 text-zinc-500 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
        />
      </button>

      {/* 테이블 */}
      {open && (
        <div className="border-t border-zinc-800/60">
          <ErrorBoundary fallback={
            <p className="px-5 py-4 text-xs text-red-400">
              ⚠️ 수집 실패 — 마지막 성공: {lastScraped ? new Date(lastScraped).toLocaleString('ko-KR') : '—'}
            </p>
          }>
            <ProductTable
              products={filteredProducts}
              globalLowestPrice={lowestPrice}
              onAlertClick={onAlertClick}
            />
          </ErrorBoundary>
        </div>
      )}
    </div>
  )
}
