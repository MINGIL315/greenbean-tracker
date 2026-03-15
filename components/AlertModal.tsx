'use client'

import { useState, useEffect } from 'react'
import { X, Bell, Trash2 } from 'lucide-react'
import { supabase } from '@/lib/supabase'
import { ProductWithPrices } from '@/types'

interface Alert {
  id: string
  target_price_per_kg: number
  price_type: string
  is_active: boolean
}

interface Props {
  product: ProductWithPrices | null
  onClose: () => void
}

export default function AlertModal({ product, onClose }: Props) {
  const [targetPrice, setTargetPrice] = useState('')
  const [priceType, setPriceType] = useState<'base' | 'membership' | 'subscription'>('base')
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (product) fetchAlerts()
  }, [product])

  async function fetchAlerts() {
    if (!product) return
    const { data } = await supabase
      .from('price_alerts')
      .select('*')
      .eq('product_id', product.id)
      .eq('is_active', true)
    setAlerts(data ?? [])
  }

  async function saveAlert() {
    if (!product || !targetPrice) return
    setSaving(true)
    await supabase.from('price_alerts').insert({
      product_id: product.id,
      target_price_per_kg: parseInt(targetPrice),
      price_type: priceType,
    })
    setTargetPrice('')
    await fetchAlerts()
    setSaving(false)
  }

  async function deleteAlert(id: string) {
    await supabase.from('price_alerts').update({ is_active: false }).eq('id', id)
    await fetchAlerts()
  }

  if (!product) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-xl bg-white dark:bg-gray-900 shadow-2xl p-6 space-y-4 mx-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 font-semibold text-gray-900 dark:text-gray-100">
            <Bell className="h-4 w-4 text-yellow-500" />
            가격 알림 설정
          </div>
          <button onClick={onClose}><X className="h-5 w-5 text-gray-400 hover:text-gray-600" /></button>
        </div>

        <p className="text-sm text-gray-600 dark:text-gray-400">{product.name}</p>

        {/* 입력 폼 */}
        <div className="space-y-3">
          <div>
            <label className="text-xs text-gray-500 dark:text-gray-400">가격 유형</label>
            <select
              value={priceType}
              onChange={(e) => setPriceType(e.target.value as typeof priceType)}
              className="mt-1 w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="base">기본가</option>
              <option value="membership">멤버십가</option>
              <option value="subscription">구독가</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-500 dark:text-gray-400">목표가 (원/kg)</label>
            <input
              type="number"
              value={targetPrice}
              onChange={(e) => setTargetPrice(e.target.value)}
              placeholder="예: 15000"
              className="mt-1 w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            onClick={saveAlert}
            disabled={saving || !targetPrice}
            className="w-full rounded-md bg-blue-600 text-white py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {saving ? '저장 중...' : '알림 저장'}
          </button>
        </div>

        {/* 활성 알림 목록 */}
        {alerts.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-gray-500 dark:text-gray-400">활성 알림</p>
            {alerts.map((alert) => (
              <div key={alert.id} className="flex items-center justify-between rounded-lg bg-gray-50 dark:bg-gray-800 px-3 py-2 text-sm">
                <span className="text-gray-700 dark:text-gray-300">
                  {alert.price_type} ≤ {alert.target_price_per_kg.toLocaleString()}원
                </span>
                <button onClick={() => deleteAlert(alert.id)}>
                  <Trash2 className="h-4 w-4 text-red-400 hover:text-red-600" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
