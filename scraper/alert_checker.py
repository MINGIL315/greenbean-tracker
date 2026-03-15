"""
가격 알림 체크 및 이메일 발송 모듈
"""
import os
import requests
from email_template import build_alert_email
import db_client


class AlertChecker:
    def __init__(self):
        self.resend_api_key = os.environ.get("RESEND_API_KEY")
        self.alert_email = os.environ.get("ALERT_EMAIL")

    def run(self):
        """활성 알림 목록을 조회하고 조건 충족 시 이메일 발송"""
        if not self.resend_api_key or not self.alert_email:
            print("[AlertChecker] RESEND_API_KEY 또는 ALERT_EMAIL 미설정, 알림 체크 건너뜀")
            return

        client = db_client.get_client()

        # 활성 알림 목록 조회
        alerts_result = (
            client.table("price_alerts")
            .select("*, products(name, origin_country, companies(name, website_url))")
            .eq("is_active", True)
            .execute()
        )

        for alert in alerts_result.data:
            try:
                product_id = alert["product_id"]
                target_price = alert["target_price_per_kg"]
                price_type = alert["price_type"]
                product = alert.get("products", {})

                # 최신 가격 조회
                entry_result = (
                    client.table("price_entries")
                    .select("*, price_tiers(*)")
                    .eq("product_id", product_id)
                    .order("scraped_at", desc=True)
                    .limit(1)
                    .execute()
                )

                if not entry_result.data:
                    continue

                entry = entry_result.data[0]
                tiers = entry.get("price_tiers", [])

                # 가격 유형에 따라 현재가 선택
                current_price = None
                if price_type == "base":
                    current_price = entry["base_price_per_kg"]
                elif price_type == "membership":
                    t = next((t for t in tiers if t["tier_type"] == "membership"), None)
                    current_price = t["price_per_kg"] if t else None
                elif price_type == "subscription":
                    t = next((t for t in tiers if t["tier_type"] == "subscription"), None)
                    current_price = t["price_per_kg"] if t else None

                if current_price is None:
                    continue

                # 목표가 달성 조건 확인
                if current_price <= target_price:
                    company = product.get("companies") or {}
                    email_data = build_alert_email(
                        product_name=product.get("name", ""),
                        company_name=company.get("name", ""),
                        origin=product.get("origin_country", ""),
                        current_price=current_price,
                        target_price=target_price,
                        website_url=company.get("website_url", ""),
                    )
                    self._send_email(email_data)

                    # 알림 비활성화
                    client.table("price_alerts").update({"is_active": False}).eq("id", alert["id"]).execute()
                    print(f"  🔔 알림 발송: {product.get('name')} ({current_price:,}원 ≤ {target_price:,}원)")

            except Exception as e:
                print(f"  ⚠️  알림 처리 오류 (id={alert.get('id')}): {e}")

    def _send_email(self, email_data: dict):
        """Resend API로 이메일 발송"""
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {self.resend_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": "GreenBean Tracker <noreply@resend.dev>",
                "to": [self.alert_email],
                "subject": email_data["subject"],
                "html": email_data["html"],
            },
        )
        response.raise_for_status()
