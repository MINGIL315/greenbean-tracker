"""
하이엔드커피 (hiend.co.kr) 스크래퍼
생두 상품 목록 및 가격을 파싱합니다.
"""
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from bs4 import BeautifulSoup
from base_scraper import BaseScraper
from normalizer import normalize_origin

BASE_URL = "https://hiend.co.kr"
GREEN_BEAN_URL = f"{BASE_URL}/product/list.html?cate_no=24"


class HiendCoffeeScraper(BaseScraper):
    COMPANY_NAME = "하이엔드커피"
    WEBSITE_URL = BASE_URL

    def fetch_products(self) -> list[dict]:
        products = []
        try:
            html = self.get_page(GREEN_BEAN_URL)
            soup = BeautifulSoup(html, "html.parser")
            items = soup.select("ul.prdList li.xans-record-")

            for item in items:
                try:
                    name_el = item.select_one(".name a, .prd-name a")
                    price_el = item.select_one(".price strong, .cost strong")
                    stock_el = item.select_one(".icon .soldout, .ico_soldout")

                    if not name_el or not price_el:
                        continue

                    name = name_el.get_text(strip=True)
                    base_price = self.parse_price(price_el.get_text(strip=True))
                    is_in_stock = stock_el is None

                    # 원산지 추출 (상품명에서)
                    origin = self._extract_origin(name)

                    products.append({
                        "company_name": self.COMPANY_NAME,
                        "product_name": name,
                        "origin_country": normalize_origin(origin) if origin else None,
                        "origin_region": None,
                        "variety": None,
                        "process_method": self._extract_process(name),
                        "base_price_per_kg": base_price,
                        "is_in_stock": is_in_stock,
                        "tiers": [],
                    })
                except Exception as e:
                    print(f"[{self.COMPANY_NAME}] 상품 파싱 오류: {e}")
                    continue

        except Exception as e:
            print(f"[{self.COMPANY_NAME}] 페이지 로드 실패: {e}")
            raise

        return products

    def _extract_origin(self, name: str) -> str | None:
        """상품명에서 원산지 추출"""
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
        """상품명에서 가공방식 추출"""
        processes = ["워시드", "내추럴", "허니", "아나에로빅", "펄프드"]
        for p in processes:
            if p in name:
                return p
        return None
