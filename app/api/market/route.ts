import { NextResponse } from 'next/server'

export const revalidate = 300 // 5분 캐시

export async function GET() {
  const [rateResult, coffeeResult] = await Promise.allSettled([
    fetchUSDKRW(),
    fetchCoffeeFutures(),
  ])

  return NextResponse.json({
    usdKrw: rateResult.status === 'fulfilled' ? rateResult.value : null,
    coffeeUsd: coffeeResult.status === 'fulfilled' ? coffeeResult.value : null,
  })
}

async function fetchUSDKRW(): Promise<{ current: number; prev: number } | null> {
  const res = await fetch('https://api.frankfurter.app/latest?from=USD&to=KRW', {
    next: { revalidate: 300 },
  })
  if (!res.ok) return null
  const data = await res.json()
  const current: number = data?.rates?.KRW
  if (!current) return null

  // 전날 날짜 (weekday 기준: 월요일이면 금요일로)
  const prevDate = getPrevBusinessDay(new Date(data.date))
  const res2 = await fetch(
    `https://api.frankfurter.app/${prevDate}?from=USD&to=KRW`,
    { next: { revalidate: 3600 } }
  )
  if (!res2.ok) return { current, prev: current }
  const data2 = await res2.json()
  const prev: number = data2?.rates?.KRW ?? current

  return { current, prev }
}

async function fetchCoffeeFutures(): Promise<{ current: number; prev: number } | null> {
  // ICE 아라비카 커피 C 선물 (KC=F) — Yahoo Finance, 5일치 조회
  const res = await fetch(
    'https://query1.finance.yahoo.com/v8/finance/chart/KC=F?interval=1d&range=5d',
    {
      headers: { 'User-Agent': 'Mozilla/5.0' },
      next: { revalidate: 300 },
    }
  )
  if (!res.ok) return null
  const data = await res.json()
  const meta = data?.chart?.result?.[0]?.meta
  const closes: number[] = data?.chart?.result?.[0]?.indicators?.quote?.[0]?.close ?? []

  const current: number = meta?.regularMarketPrice
  if (!current) return null

  // 전날 종가: closes 배열의 마지막에서 두 번째 유효값
  const validCloses = closes.filter((v) => v != null && !isNaN(v))
  const prev = validCloses.length >= 2 ? validCloses[validCloses.length - 2] : current

  return { current, prev }
}

function getPrevBusinessDay(date: Date): string {
  const d = new Date(date)
  d.setDate(d.getDate() - 1)
  while (d.getDay() === 0 || d.getDay() === 6) {
    d.setDate(d.getDate() - 1)
  }
  return d.toISOString().split('T')[0]
}
