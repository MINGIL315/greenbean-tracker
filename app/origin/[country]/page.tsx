import { supabase } from '@/lib/supabase'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import PriceHistoryChart from '@/components/PriceHistoryChart'

export const revalidate = 1800

interface Props {
  params: Promise<{ country: string }>
}

export default async function OriginPage({ params }: Props) {
  const { country } = await params
  const decodedCountry = decodeURIComponent(country)

  const { data: products } = await supabase
    .from('products')
    .select(`
      *,
      price_entries (
        *,
        price_tiers (*)
      ),
      companies (name, website_url)
    `)
    .eq('origin_country', decodedCountry)
    .eq('is_active', true)

  if (!products || products.length === 0) notFound()

  // 기본가 오름차순 정렬
  const sorted = [...products].sort((a: any, b: any) => {
    const aPrice = a.price_entries?.[0]?.base_price_per_kg ?? Infinity
    const bPrice = b.price_entries?.[0]?.base_price_per_kg ?? Infinity
    return aPrice - bPrice
  })

  const lowestPrice = sorted[0]?.price_entries?.[0]?.base_price_per_kg ?? null

  // 최근 30일 평균가 추이를 위한 데이터 수집
  const allEntries = products
    .flatMap((p: any) => p.price_entries ?? [])
    .sort((a: any, b: any) => new Date(a.scraped_at).getTime() - new Date(b.scraped_at).getTime())

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* 브레드크럼 */}
        <nav className="text-sm text-gray-500 dark:text-gray-400">
          <Link href="/" className="hover:underline">홈</Link>
          <span className="mx-2">/</span>
          <span>{decodedCountry}</span>
        </nav>

        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          🌍 {decodedCountry} 생두 비교
        </h1>

        {/* 상품 비교 테이블 */}
        <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800/50">
                  <th className="py-3 px-4 text-left">공급사</th>
                  <th className="py-3 px-4 text-left">상품명</th>
                  <th className="py-3 px-4 text-left">품종</th>
                  <th className="py-3 px-4 text-left">가공</th>
                  <th className="py-3 px-4 text-right">기본가</th>
                  <th className="py-3 px-4 text-right">멤버십</th>
                  <th className="py-3 px-4 text-right">구독</th>
                  <th className="py-3 px-4 text-center">재고</th>
                </tr>
              </thead>
              <tbody>
                {sorted.map((product: any) => {
                  const latest = product.price_entries?.[0]
                  const membership = latest?.price_tiers?.find((t: any) => t.tier_type === 'membership')
                  const subscription = latest?.price_tiers?.find((t: any) => t.tier_type === 'subscription')
                  const isLowest = latest?.base_price_per_kg === lowestPrice

                  return (
                    <tr key={product.id} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/30">
                      <td className="py-3 px-4 text-gray-600 dark:text-gray-400">
                        {product.companies?.name ?? '—'}
                      </td>
                      <td className="py-3 px-4">
                        <Link href={`/product/${product.id}`} className="hover:underline text-blue-700 dark:text-blue-300">
                          {product.name}
                        </Link>
                      </td>
                      <td className="py-3 px-4 text-gray-600 dark:text-gray-400">{product.variety ?? '—'}</td>
                      <td className="py-3 px-4 text-gray-600 dark:text-gray-400">{product.process_method ?? '—'}</td>
                      <td className="py-3 px-4 text-right font-tabular-nums">
                        {latest ? (
                          <span className={isLowest ? 'text-green-600 dark:text-green-400 font-bold' : 'text-gray-800 dark:text-gray-200'}>
                            {isLowest && <span className="mr-1 text-xs">🏆</span>}
                            {latest.base_price_per_kg.toLocaleString()}원
                          </span>
                        ) : '—'}
                      </td>
                      <td className="py-3 px-4 text-right text-purple-600 dark:text-purple-400 font-tabular-nums text-xs">
                        {membership ? `🔖 ${membership.price_per_kg.toLocaleString()}원` : '—'}
                      </td>
                      <td className="py-3 px-4 text-right text-green-600 dark:text-green-400 font-tabular-nums text-xs">
                        {subscription ? `🔄 ${subscription.price_per_kg.toLocaleString()}원` : '—'}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {latest?.is_in_stock
                          ? <span className="text-green-500 text-xs">● 재고</span>
                          : <span className="text-red-500 text-xs">● 품절</span>}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* 평균가 추이 차트 */}
        {allEntries.length > 0 && (
          <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              {decodedCountry} 평균 기본가 추이
            </h2>
            <PriceHistoryChart entries={allEntries as any} />
          </div>
        )}
      </div>
    </div>
  )
}
