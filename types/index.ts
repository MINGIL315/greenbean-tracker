export type TierType = 'bulk' | 'membership' | 'subscription'

export interface Company {
  id: string
  name: string
  website_url: string | null
  logo_url: string | null
  is_active: boolean
  created_at: string
}

export interface Product {
  id: string
  company_id: string
  name: string
  origin_country: string | null
  origin_region: string | null
  variety: string | null
  process_method: string | null
  is_active: boolean
  created_at: string
}

export interface PriceEntry {
  id: string
  product_id: string
  base_price_per_kg: number
  is_in_stock: boolean
  is_anomaly: boolean
  scraped_at: string
  created_at: string
}

export interface PriceTier {
  id: string
  price_entry_id: string
  tier_type: TierType
  min_kg: number | null
  max_kg: number | null
  price_per_kg: number
}

export interface ProductWithPrices extends Product {
  price_entries: (PriceEntry & {
    price_tiers: PriceTier[]
  })[]
}

export interface CompanyWithProducts extends Company {
  products: ProductWithPrices[]
}
