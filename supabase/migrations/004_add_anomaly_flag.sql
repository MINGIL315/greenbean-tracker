ALTER TABLE price_entries ADD COLUMN IF NOT EXISTS is_anomaly boolean DEFAULT false;
