'use client'

import { useState } from 'react'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { ChevronDown, GripVertical } from 'lucide-react'
import { CompanyWithProducts, ProductWithPrices } from '@/types'
import ProductTable from './ProductTable'
import ErrorBoundary from './ErrorBoundary'

interface Props {
  company: CompanyWithProducts
  originFilter: string
  searchQuery?: string
  onAlertClick?: (product: ProductWithPrices) => void
}

export default function CompanyCard({ company, originFilter, searchQuery = '', onAlertClick }: Props) {
  const [open, setOpen] = useState(false)

  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: String(company.id),
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    zIndex: isDragging ? 50 : undefined,
  }

  const filteredProducts = company.products
    .filter((p) => !originFilter || p.origin_country === originFilter)
    .filter((p) => !searchQuery || p.name.toLowerCase().includes(searchQuery.toLowerCase()))

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
    <div ref={setNodeRef} style={style} className="rounded-2xl border border-zinc-800 bg-zinc-900 overflow-hidden">
      {/* 카드 헤더 */}
      <div className="w-full flex items-center justify-between px-3 py-3.5 text-left">
        {/* 드래그 핸들 */}
        <button
          {...attributes}
          {...listeners}
          className="p-1 mr-1 rounded text-zinc-600 hover:text-zinc-400 cursor-grab active:cursor-grabbing touch-none"
          tabIndex={-1}
        >
          <GripVertical className="h-4 w-4" />
        </button>

        {/* 회사 정보 (클릭 시 열기/닫기) */}
        <button
          onClick={() => setOpen(!open)}
          className="flex-1 flex items-center gap-3 text-left hover:bg-zinc-800/40 rounded-lg px-2 py-1 transition-colors"
        >
          <span className="font-semibold text-zinc-100 text-sm">{company.name}</span>
          <span className="text-xs text-zinc-500 tabular">{filteredProducts.length}개 상품</span>
          {lastScraped && (
            <span className="hidden sm:flex items-center gap-1.5 text-xs text-zinc-600">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              {new Date(lastScraped).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })} 수집
            </span>
          )}
        </button>

        <ChevronDown
          onClick={() => setOpen(!open)}
          className={`h-4 w-4 text-zinc-500 transition-transform duration-200 cursor-pointer mr-1 ${open ? 'rotate-180' : ''}`}
        />
      </div>

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
