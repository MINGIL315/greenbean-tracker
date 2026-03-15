'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Plus, Trash2 } from 'lucide-react'
import { supabase } from '@/lib/supabase'

interface Company { id: string; name: string }
interface Product { id: string; name: string }
interface TierRow { min_kg: string; max_kg: string; price_per_kg: string }

export default function AdminPage() {
  const router = useRouter()
  const [companies, setCompanies] = useState<Company[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [selectedCompany, setSelectedCompany] = useState('')
  const [selectedProduct, setSelectedProduct] = useState('')
  const [newProductName, setNewProductName] = useState('')
  const [basePrice, setBasePrice] = useState('')
  const [membershipPrice, setMembershipPrice] = useState('')
  const [subscriptionPrice, setSubscriptionPrice] = useState('')
  const [isInStock, setIsInStock] = useState(true)
  const [tiers, setTiers] = useState<TierRow[]>([])
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    supabase.from('companies').select('id, name').then(({ data }) => setCompanies(data ?? []))
  }, [])

  useEffect(() => {
    if (!selectedCompany) { setProducts([]); return }
    supabase.from('products').select('id, name').eq('company_id', selectedCompany).then(({ data }) => setProducts(data ?? []))
  }, [selectedCompany])

  function addTierRow() {
    setTiers([...tiers, { min_kg: '', max_kg: '', price_per_kg: '' }])
  }

  function updateTier(i: number, field: keyof TierRow, value: string) {
    const next = [...tiers]
    next[i] = { ...next[i], [field]: value }
    setTiers(next)
  }

  function removeTier(i: number) {
    setTiers(tiers.filter((_, idx) => idx !== i))
  }

  async function handleSave() {
    if (!selectedCompany || !basePrice) return
    setSaving(true)

    try {
      // 상품 결정 (기존 or 신규)
      let productId = selectedProduct
      if (!productId && newProductName) {
        const { data } = await supabase.from('products').insert({
          company_id: selectedCompany,
          name: newProductName,
        }).select('id').single()
        productId = data?.id
      }
      if (!productId) { setSaving(false); return }

      // price_entries insert
      const { data: entry } = await supabase.from('price_entries').insert({
        product_id: productId,
        base_price_per_kg: parseInt(basePrice),
        is_in_stock: isInStock,
      }).select('id').single()

      if (!entry) { setSaving(false); return }

      // price_tiers insert
      const tierRows = [
        ...tiers
          .filter((t) => t.price_per_kg)
          .map((t) => ({
            price_entry_id: entry.id,
            tier_type: 'bulk',
            min_kg: t.min_kg ? parseFloat(t.min_kg) : null,
            max_kg: t.max_kg ? parseFloat(t.max_kg) : null,
            price_per_kg: parseInt(t.price_per_kg),
          })),
        ...(membershipPrice ? [{ price_entry_id: entry.id, tier_type: 'membership', min_kg: null, max_kg: null, price_per_kg: parseInt(membershipPrice) }] : []),
        ...(subscriptionPrice ? [{ price_entry_id: entry.id, tier_type: 'subscription', min_kg: null, max_kg: null, price_per_kg: parseInt(subscriptionPrice) }] : []),
      ]
      if (tierRows.length > 0) {
        await supabase.from('price_tiers').insert(tierRows)
      }

      router.push('/')
    } catch (e) {
      console.error(e)
      setSaving(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 p-6">
      <div className="max-w-2xl mx-auto space-y-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">⚙️ 수동 가격 입력</h1>

        <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6 space-y-4">

          {/* 공급사 선택 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">공급사</label>
            <select value={selectedCompany} onChange={(e) => setSelectedCompany(e.target.value)}
              className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="">선택하세요</option>
              {companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>

          {/* 상품 선택 or 신규 입력 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">상품</label>
            <select value={selectedProduct} onChange={(e) => setSelectedProduct(e.target.value)}
              className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 mb-2">
              <option value="">신규 상품 입력</option>
              {products.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
            {!selectedProduct && (
              <input value={newProductName} onChange={(e) => setNewProductName(e.target.value)}
                placeholder="신규 상품명 입력"
                className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            )}
          </div>

          {/* 기본가 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">기본가 (원/kg)</label>
            <input type="number" value={basePrice} onChange={(e) => setBasePrice(e.target.value)} placeholder="예: 18000"
              className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>

          {/* 구간 단가 */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">구간 단가</label>
              <button onClick={addTierRow} className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700">
                <Plus className="h-3 w-3" /> 행 추가
              </button>
            </div>
            {tiers.map((t, i) => (
              <div key={i} className="flex gap-2 mb-2">
                <input type="number" value={t.min_kg} onChange={(e) => updateTier(i, 'min_kg', e.target.value)}
                  placeholder="최소 kg" className="w-24 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                <input type="number" value={t.max_kg} onChange={(e) => updateTier(i, 'max_kg', e.target.value)}
                  placeholder="최대 kg" className="w-24 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                <input type="number" value={t.price_per_kg} onChange={(e) => updateTier(i, 'price_per_kg', e.target.value)}
                  placeholder="단가" className="flex-1 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                <button onClick={() => removeTier(i)} className="text-red-400 hover:text-red-600">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>

          {/* 멤버십가 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">멤버십가 (선택)</label>
            <input type="number" value={membershipPrice} onChange={(e) => setMembershipPrice(e.target.value)} placeholder="예: 15000"
              className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>

          {/* 구독가 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">구독가 (선택)</label>
            <input type="number" value={subscriptionPrice} onChange={(e) => setSubscriptionPrice(e.target.value)} placeholder="예: 13800"
              className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>

          {/* 재고 여부 */}
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">재고</span>
            <button
              onClick={() => setIsInStock(!isInStock)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${isInStock ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'}`}
            >
              <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${isInStock ? 'translate-x-6' : 'translate-x-1'}`} />
            </button>
            <span className="text-sm text-gray-500">{isInStock ? '재고 있음' : '품절'}</span>
          </div>

          {/* 저장 */}
          <button
            onClick={handleSave}
            disabled={saving || !selectedCompany || !basePrice}
            className="w-full rounded-md bg-blue-600 text-white py-2.5 text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {saving ? '저장 중...' : '저장하고 대시보드로'}
          </button>
        </div>
      </div>
    </div>
  )
}
