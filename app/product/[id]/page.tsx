import { supabase } from '@/lib/supabase'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import PriceHistoryChart from '@/components/PriceHistoryChart'

export const revalidate = 1800

interface Props {
  params: Promise<{ id: string }>
}

export default async function ProductDetailPage({ params }: Props) {
  const { id } = await params

  const { data: product } = await supabase
    .from('products')
    .select(`
      *,
      price_entries (
        *,
        price_tiers (*)
      ),
      companies (name, website_url)
    `)
    .eq('id', id)
    .single()

  if (!product) notFound()

  const entries = [...(product.price_entries ?? [])].sort(
    (a: any, b: any) => new Date(a.scraped_at).getTime() - new Date(b.scraped_at).getTime()
  )
  const latest = entries.at(-1) as any

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* 브레드크럼 */}
        <nav className="text-sm text-gray-500 dark:text-gray-400">
          <Link href="/" className="hover:underline">홈</Link>
          <span className="mx-2">/</span>
          <span>{product.name}</span>
        </nav>

        {/* 상품 정보 */}
        <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6 space-y-3">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{product.name}</h1>
          <div className="flex flex-wrap gap-3 text-sm text-gray-600 dark:text-gray-400">
            <span>🏭 {(product as any).companies?.name}</span>
            {product.origin_country && (
              <Link href={`/origin/${product.origin_country}`} className="hover:underline text-blue-600 dark:text-blue-400">
                🌍 {product.origin_country}
              </Link>
            )}
            {product.origin_region && <span>📍 {product.origin_region}</span>}
            {product.variety && <span>🌱 {product.variety}</span>}
            {product.process_method && <span>⚙️ {product.process_method}</span>}
          </div>
          {latest && (
            <div className="text-3xl font-bold text-gray-900 dark:text-gray-100 font-tabular-nums">
              {latest.base_price_per_kg.toLocaleString('ko-KR')}원/kg
              {!latest.is_in_stock && <span className="ml-3 text-base text-red-500">품절</span>}
            </div>
          )}
        </div>

        {/* 가격 이력 차트 */}
        <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">가격 이력</h2>
          {entries.length > 0 ? (
            <PriceHistoryChart entries={entries as any} />
          ) : (
            <p className="text-gray-500 dark:text-gray-400 text-sm">이력 데이터 없음</p>
          )}
        </div>
      </div>
    </div>
  )
}
