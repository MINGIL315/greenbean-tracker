'use client'

import { useEffect, useState } from 'react'

interface PricePoint { current: number; prev: number }
interface MarketData { usdKrw: PricePoint | null; coffeeUsd: PricePoint | null }

function Change({ current, prev, decimals }: { current: number; prev: number; decimals: number }) {
  const diff = current - prev
  const pct = prev !== 0 ? (diff / prev) * 100 : 0
  if (Math.abs(pct) < 0.01) return null
  const up = diff > 0
  return (
    <span className={`text-[10px] ml-1 ${up ? 'text-red-400' : 'text-blue-400'}`}>
      {up ? '▲' : '▼'}{Math.abs(diff).toFixed(decimals)} ({Math.abs(pct).toFixed(1)}%)
    </span>
  )
}

export default function MarketTicker() {
  const [data, setData] = useState<MarketData | null>(null)

  useEffect(() => {
    fetch('/api/market').then((r) => r.json()).then(setData).catch(() => {})
  }, [])

  if (!data) {
    return (
      <div className="flex items-center gap-5">
        <div className="w-32 h-3 rounded bg-zinc-800 animate-pulse" />
        <div className="w-32 h-3 rounded bg-zinc-800 animate-pulse" />
      </div>
    )
  }

  return (
    <div className="flex items-center gap-5 text-xs font-mono">
      {data.usdKrw && (
        <span title="USD/KRW 환율">
          <span className="text-zinc-500 mr-1.5">USD/KRW</span>
          <span className="text-zinc-200 font-semibold">
            {data.usdKrw.current.toLocaleString('ko-KR', { maximumFractionDigits: 0 })}
          </span>
          <span className="text-zinc-500">원</span>
          <Change current={data.usdKrw.current} prev={data.usdKrw.prev} decimals={0} />
        </span>
      )}
      {data.usdKrw && data.coffeeUsd && (
        <span className="text-zinc-800">|</span>
      )}
      {data.coffeeUsd && (
        <span title="ICE 아라비카 커피 C 선물 (¢/lb)">
          <span className="text-zinc-500 mr-1.5">커피지수</span>
          <span className="text-zinc-200 font-semibold">{data.coffeeUsd.current.toFixed(2)}</span>
          <span className="text-zinc-500">¢/lb</span>
          <Change current={data.coffeeUsd.current} prev={data.coffeeUsd.prev} decimals={2} />
        </span>
      )}
    </div>
  )
}
