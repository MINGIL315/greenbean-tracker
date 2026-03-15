"""
커피리브레 (coffeelibre.kr) 스크래퍼
생두 카테고리: /product/list.html?cate_no=48
"""
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from bs4 import BeautifulSoup
from base_scraper import BaseScraper
from normalizer import normalize_origin

BASE_URL = "https://coffeelibre.kr"
GREEN_BEAN_URL = f"{BASE_URL}/product/list.html?cate_no=48"


class CoffeeLibreScraper(BaseScraper):
    COMPANY_NAME = "커피리브레"
    WEBSITE_URL = BASE_URL

    def fetch_products(self) -> list[dict]:
        products = []
        try:
            html = self.get_page(GREEN_BEAN_URL)
            soup = BeautifulSoup(html, "html.parser")
            items = soup.select("ul.prdList li.xans-record-")
            print(f"  [{self.COMPANY_NAME}] 상품 {len(items)}개 발견")

            for item in items:
                try:
                    name_el = item.select_one(".name a")
                    price_el = item.select_one("li.price")
                    if not name_el or not price_el:
                        continue

                    name = name_el.get_text(" ", strip=True)
                    # [생두] 접두사 제거
                    name = re.sub(r"^\[생두\]\s*", "", name).strip()

                    price_text = price_el.get_text(strip=True)
                    if not re.search(r"\d", price_text):
                        continue

                    base_price = self.parse_price(price_text)
                    if base_price <= 0:
                        continue

                    # .soldOut 요소가 존재하고 displaynone 클래스가 없으면 품절
                    soldout_el = item.select_one(".soldOut")
                    is_in_stock = soldout_el is None or "displaynone" in (soldout_el.get("class") or [])

                    origin_ko = self._extract_origin(name)
                    process = self._extract_process(name)
                    variety = self._extract_variety(name)

                    products.append({
                        "company_name": self.COMPANY_NAME,
                        "product_name": name,
                        "origin_country": normalize_origin(origin_ko) if origin_ko else None,
                        "origin_region": None,
                        "variety": variety,
                        "process_method": process,
                        "base_price_per_kg": base_price,
                        "is_in_stock": is_in_stock,
                        "tiers": [],
                    })
                except Exception as e:
                    print(f"  [{self.COMPANY_NAME}] 상품 파싱 오류: {e}")
                    continue

        except Exception as e:
            print(f"  [{self.COMPANY_NAME}] 페이지 로드 실패: {e}")
            raise

        return products

    def _extract_origin(self, name: str) -> str | None:
        origins = [
            "에티오피아", "콜롬비아", "과테말라", "브라질", "케냐",
            "코스타리카", "파나마", "르완다", "부룬디", "예멘",
            "온두라스", "페루", "인도네시아", "엘살바도르", "탄자니아",
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
        varieties = ["게이샤", "버번", "카투라", "SL28", "SL34", "74110", "74112", "파카마라"]
        for v in varieties:
            if v in name:
                return v
        return None
