import os

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        _client = create_client(url, key)
    return _client


def upsert_company(name: str, website_url: str = None) -> str:
    """공급사 upsert 후 id 반환"""
    client = get_client()
    existing = client.table("companies").select("id").eq("name", name).execute()
    if existing.data:
        return existing.data[0]["id"]
    result = client.table("companies").insert({"name": name, "website_url": website_url}).execute()
    return result.data[0]["id"]


def upsert_product(data: dict) -> str:
    """상품 upsert 후 id 반환"""
    client = get_client()
    company_id = upsert_company(data["company_name"])
    payload = {
        "company_id": company_id,
        "name": data["product_name"],
        "origin_country": data.get("origin_country"),
        "origin_region": data.get("origin_region"),
        "variety": data.get("variety"),
        "process_method": data.get("process_method"),
    }
    # company_id + name 조합으로 upsert
    existing = (
        client.table("products")
        .select("id")
        .eq("company_id", company_id)
        .eq("name", data["product_name"])
        .execute()
    )
    if existing.data:
        product_id = existing.data[0]["id"]
        client.table("products").update(payload).eq("id", product_id).execute()
    else:
        result = client.table("products").insert(payload).execute()
        product_id = result.data[0]["id"]
    return product_id


def insert_price_entry(product_id: str, data: dict, is_anomaly: bool = False) -> str:
    """가격 스냅샷 insert 후 id 반환"""
    client = get_client()
    payload = {
        "product_id": product_id,
        "base_price_per_kg": data["base_price_per_kg"],
        "is_in_stock": data.get("is_in_stock", True),
        "is_anomaly": is_anomaly,
    }
    result = client.table("price_entries").insert(payload).execute()
    return result.data[0]["id"]


def insert_price_tiers(entry_id: str, tiers: list) -> None:
    """구간/멤버십/구독 단가 insert"""
    if not tiers:
        return
    client = get_client()
    rows = [
        {
            "price_entry_id": entry_id,
            "tier_type": t["tier_type"],
            "min_kg": t.get("min_kg"),
            "max_kg": t.get("max_kg"),
            "price_per_kg": t["price_per_kg"],
        }
        for t in tiers
    ]
    client.table("price_tiers").insert(rows).execute()


def get_latest_price(product_id: str) -> int | None:
    """해당 상품의 가장 최근 기본가 반환"""
    client = get_client()
    result = (
        client.table("price_entries")
        .select("base_price_per_kg")
        .eq("product_id", product_id)
        .order("scraped_at", desc=True)
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]["base_price_per_kg"]
    return None


def insert_scrape_log(
    total_products: int,
    success_count: int,
    fail_count: int,
    failed_scrapers: list[str],
    duration_seconds: float,
) -> None:
    """스크래핑 실행 결과 로그 insert"""
    client = get_client()
    client.table("scrape_logs").insert({
        "total_products": total_products,
        "success_count": success_count,
        "fail_count": fail_count,
        "failed_scrapers": failed_scrapers,
        "duration_seconds": duration_seconds,
    }).execute()
