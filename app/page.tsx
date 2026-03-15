'use client'

import { useEffect, useState, useMemo } from 'react'
import { supabase } from '@/lib/supabase'
import { CompanyWithProducts, ProductWithPrices } from '@/types'
import CompanyCard from '@/components/CompanyCard'
import OriginFilter from '@/components/OriginFilter'
import LastUpdatedBadge from '@/components/LastUpdatedBadge'
import AlertModal from '@/components/AlertModal'
import MarketTicker from '@/components/MarketTicker'

export default function HomePage() {
  const [companies, setCompanies] = useState<CompanyWithProducts[]>([])
  const [loading, setLoading] = useState(true)
  const [originFilter, setOriginFilter] = useState('')
  const [alertProduct, setAlertProduct] = useState<ProductWithPrices | null>(null)

  useEffect(() => { fetchData() }, [])

  async function fetchData() {
    setLoading(true)
    const { data, error } = await supabase
      .from('companies')
      .select(`*, products (*, price_entries (*, price_tiers (*)))`)
      .eq('is_active', true)
      .order('name')

    if (!error && data) {
      const sorted = (data as any[]).map((c) => ({
        ...c,
        products: c.products.map((p: any) => ({
          ...p,
          price_entries: [...(p.price_entries ?? [])].sort(
            (a: any, b: any) => new Date(b.scraped_at).getTime() - new Date(a.scraped_at).getTime()
          ),
        })),
      }))
      setCompanies(sorted)
    }
    setLoading(false)
  }

  const allOrigins = useMemo(() => {
    const set = new Set<string>()
    companies.forEach((c) => c.products.forEach((p) => { if (p.origin_country) set.add(p.origin_country) }))
    return [...set].sort()
  }, [companies])

  const lastUpdated = useMemo(() => {
    const dates = companies.flatMap((c) => c.products).flatMap((p) => p.price_entries)
      .map((e: any) => e?.scraped_at).filter(Boolean).sort()
    return dates.at(-1) ?? null
  }, [companies])

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 p-6 space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-36 rounded-2xl bg-zinc-900 animate-pulse" />
        ))}
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-zinc-950">
      {/* 헤더 */}
      <header className="sticky top-0 z-40 border-b border-zinc-800/60 bg-zinc-950/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center gap-6">
          {/* 로고 */}
          <div className="flex items-center gap-2.5 shrink-0">
            <div className="w-7 h-7 rounded-lg bg-emerald-500 flex items-center justify-center text-sm font-bold text-zinc-950">
              G
            </div>
            <span className="font-semibold text-zinc-100 tracking-tight">GreenBean</span>
            <span className="hidden sm:inline text-xs text-zinc-500 font-medium px-2 py-0.5 rounded-full border border-zinc-800">
              생두 가격 비교
            </span>
          </div>

          {/* 마켓 티커 */}
          <div className="flex-1 flex justify-center">
            <MarketTicker />
          </div>

          {/* 우측 컨트롤 */}
          <div className="flex items-center gap-3 shrink-0">
            <LastUpdatedBadge date={lastUpdated} />
            <OriginFilter origins={allOrigins} value={originFilter} onChange={setOriginFilter} />
          </div>
        </div>
      </header>

      {/* 본문 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-3">
        {companies.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-32 text-zinc-600">
            <div className="text-4xl mb-4">⚠️</div>
            <p className="text-sm">데이터를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.</p>
          </div>
        ) : (
          companies.map((company) => (
            <CompanyCard
              key={company.id}
              company={company}
              originFilter={originFilter}
              onAlertClick={setAlertProduct}
            />
          ))
        )}
      </main>

      <AlertModal product={alertProduct} onClose={() => setAlertProduct(null)} />
    </div>
  )
}
