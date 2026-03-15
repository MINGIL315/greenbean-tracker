"""
빈브라더스 (beanbrothers.co.kr) 스크래퍼
생두 상품 목록 및 가격을 파싱합니다.
"""
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from bs4 import BeautifulSoup
from base_scraper import BaseScraper
from normalizer import normalize_origin

BASE_URL = "https://beanbrothers.co.kr"
GREEN_BEAN_URL = f"{BASE_URL}/product/list.html?cate_no=55"


class BeanBrothersScraper(BaseScraper):
    COMPANY_NAME = "빈브라더스"
    WEBSITE_URL = BASE_URL

    def fetch_products(self) -> list[dict]:
        products = []
        try:
            html = self.get_page(GREEN_BEAN_URL)
            soup = BeautifulSoup(html, "html.parser")
            items = soup.select("ul.prdList li.xans-record-, .product-list li")

            for item in items:
                try:
                    name_el = item.select_one(".name a, .prd-name a, strong.name")
                    price_el = item.select_one(".price strong, .cost strong, .price")
                    stock_el = item.select_one(".soldout, .icon-soldout")

                    if not name_el or not price_el:
                        continue

                    name = name_el.get_text(strip=True)
                    price_text = price_el.get_text(strip=True)
                    if not re.search(r'\d', price_text):
                        continue

                    base_price = self.parse_price(price_text)
                    if base_price <= 0:
                        continue

                    is_in_stock = stock_el is None
                    origin_ko = self._extract_origin(name)
                    tiers = self._extract_tiers(item)

                    products.append({
                        "company_name": self.COMPANY_NAME,
                        "product_name": name,
                        "origin_country": normalize_origin(origin_ko) if origin_ko else None,
                        "origin_region": None,
                        "variety": self._extract_variety(name),
                        "process_method": self._extract_process(name),
                        "base_price_per_kg": base_price,
                        "is_in_stock": is_in_stock,
                        "tiers": tiers,
                    })
                except Exception as e:
                    print(f"[{self.COMPANY_NAME}] 상품 파싱 오류: {e}")
                    continue

        except Exception as e:
            print(f"[{self.COMPANY_NAME}] 페이지 로드 실패: {e}")
            raise

        return products

    def _extract_origin(self, name: str) -> str | None:
        origins = [
            "에티오피아", "콜롬비아", "과테말라", "브라질", "케냐",
            "코스타리카", "파나마", "르완다", "부룬디", "예멘",
            "온두라스", "페루", "인도네시아", "엘살바도르",
        ]
        for origin in origins:
            if origin in name:
                return origin
        return None

    def _extract_process(self, name: str) -> str | None:
        processes = {
            "워시드": "Washed", "내추럴": "Natural", "허니": "Honey",
            "아나에로빅": "Anaerobic", "펄프드": "Pulped Natural",
        }
        for k, v in processes.items():
            if k in name:
                return v
        return None

    def _extract_variety(self, name: str) -> str | None:
        varieties = ["게이샤", "버번", "카투라", "카투아이", "파카마라", "SL28", "SL34"]
        for v in varieties:
            if v in name:
                return v
        return None

    def _extract_tiers(self, item) -> list[dict]:
        """구간 단가 추출 (있는 경우)"""
        tiers = []
        tier_elements = item.select(".tier-price, .bulk-price, [class*='tier']")
        for el in tier_elements:
            try:
                text = el.get_text(strip=True)
                price = self.parse_price(text)
                min_kg_match = re.search(r'(\d+)\s*kg', text, re.IGNORECASE)
                min_kg = float(min_kg_match.group(1)) if min_kg_match else None
                tiers.append({
                    "tier_type": "bulk",
                    "min_kg": min_kg,
                    "max_kg": None,
                    "price_per_kg": price,
                })
            except Exception:
                continue
        return tiers
