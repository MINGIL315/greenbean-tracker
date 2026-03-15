CREATE TABLE price_alerts (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id           uuid REFERENCES products(id),
  target_price_per_kg  integer NOT NULL,
  price_type           text CHECK (price_type IN ('base', 'membership', 'subscription')),
  is_active            boolean DEFAULT true,
  created_at           timestamptz DEFAULT now()
);

ALTER TABLE price_alerts DISABLE ROW LEVEL SECURITY;
