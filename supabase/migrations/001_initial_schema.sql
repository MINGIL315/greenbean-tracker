-- 공급사
CREATE TABLE companies (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name        text NOT NULL,
  website_url text,
  logo_url    text,
  is_active   boolean DEFAULT true,
  created_at  timestamptz DEFAULT now()
);

-- 상품
CREATE TABLE products (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id     uuid REFERENCES companies(id),
  name           text NOT NULL,
  origin_country text,
  origin_region  text,
  variety        text,
  process_method text,
  is_active      boolean DEFAULT true,
  created_at     timestamptz DEFAULT now()
);

-- 가격 스냅샷
CREATE TABLE price_entries (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id       uuid REFERENCES products(id),
  base_price_per_kg integer NOT NULL,
  is_in_stock      boolean DEFAULT true,
  scraped_at       timestamptz DEFAULT now(),
  created_at       timestamptz DEFAULT now()
);

-- 구간/멤버십/구독 단가
CREATE TABLE price_tiers (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  price_entry_id uuid REFERENCES price_entries(id),
  tier_type      text CHECK (tier_type IN ('bulk', 'membership', 'subscription')),
  min_kg         numeric,
  max_kg         numeric,
  price_per_kg   integer NOT NULL
);

-- 인덱스
CREATE INDEX idx_price_entries_product_scraped
  ON price_entries(product_id, scraped_at DESC);

CREATE INDEX idx_products_company_origin
  ON products(company_id, origin_country);

-- Row Level Security 비활성화 (개인 사용 전용)
ALTER TABLE companies     DISABLE ROW LEVEL SECURITY;
ALTER TABLE products      DISABLE ROW LEVEL SECURITY;
ALTER TABLE price_entries DISABLE ROW LEVEL SECURITY;
ALTER TABLE price_tiers   DISABLE ROW LEVEL SECURITY;
