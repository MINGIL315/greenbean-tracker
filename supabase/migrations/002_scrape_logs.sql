CREATE TABLE scrape_logs (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  run_at           timestamptz DEFAULT now(),
  total_products   integer DEFAULT 0,
  success_count    integer DEFAULT 0,
  fail_count       integer DEFAULT 0,
  failed_scrapers  text[],
  duration_seconds numeric
);

ALTER TABLE scrape_logs DISABLE ROW LEVEL SECURITY;
