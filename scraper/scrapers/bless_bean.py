"""
블레스빈 (blessbean.co.kr) 스크래퍼
Gnuboard 기반 커스텀 쇼핑몰
상품 목록: POST /shop/ajax.item_one_click.php (빈 body → 전체 상품)

테이블 구조:
- <tr class="ca_sub_name"> : 국가(원산지) 헤더 행
- <tr class="it_list">     : 상품 행
  - <td class="it_name">  : 상품명
  - <td class="it_price"> : kg당 가격
- <tr class="it_list soldout" data-it_soldout="1"> : 품절 상품
"""
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import requests
from bs4 import BeautifulSoup
from base_scraper import BaseScraper
from normalizer import normalize_origin

BASE_URL = "https://www.blessbean.co.kr"
AJAX_URL = f"{BASE_URL}/shop/ajax.item_one_click.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": f"{BASE_URL}/shop/item_one_click.php",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded",
}


class BlessBeanScraper(BaseScraper):
    COMPANY_NAME = "블레스빈"
    WEBSITE_URL = BASE_URL

    def fetch_products(self) -> list[dict]:
        # 빈 POST → 전체 상품 반환
        try:
            resp = requests.post(AJAX_URL, headers=HEADERS, data={}, timeout=20)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            raise RuntimeError(f"블레스빈 AJAX 요청 실패: {e}")

        soup = BeautifulSoup(html, "html.parser")
        table = soup.select_one("table.oc_table") or soup.find("table")
        if not table:
            raise RuntimeError("블레스빈: 상품 테이블을 찾을 수 없습니다")

        rows = table.find_all("tr")
        print(f"  [{self.COMPANY_NAME}] {len(rows)}행 발견")

        products = []
        current_origin = None

        for row in rows:
            classes = row.get("class", [])

            # 원산지 헤더 행
            if "ca_sub_name" in classes:
                th = row.find("th") or row.find("td")
                if th:
                    current_origin = th.get_text(strip=True)
                continue

            # 상품 행
            if "it_list" not in classes:
                continue

            is_soldout = (
                "soldout" in classes
                or row.get("data-it_soldout") == "1"
            )

            try:
                product = self._parse_row(row, current_origin, is_soldout)
                if product:
                    products.append(product)
            except Exception as e:
                print(f"  [{self.COMPANY_NAME}] 행 파싱 오류: {e}")

        return products

    def _parse_row(self, row, current_origin: str | None, is_soldout: bool) -> dict | None:
        # 상품명
        name_el = row.select_one("td.it_name")
        if not name_el:
            return None
        name = name_el.get_text(" ", strip=True)
        name = re.sub(r"\s+", " ", name).strip()
        if not name:
            return None

        # 가격: td.it_price
        price_el = row.select_one("td.it_price")
        price = self._parse_price(price_el.get_text(strip=True)) if price_el else 0

        # 가격이 없으면 수량 입력란에서 data 속성 시도
        if price <= 0:
            inp = row.select_one("input[data-price]")
            if inp:
                price = self._parse_price(inp.get("data-price", ""))

        if price <= 0:
            return None

        # 원산지: 상품명에서 추출, 없으면 현재 헤더 사용
        origin_ko = self._extract_origin(name) or (
            self._extract_origin(current_origin) if current_origin else None
        ) or current_origin

        return {
            "company_name": self.COMPANY_NAME,
            "product_name": name,
            "origin_country": normalize_origin(origin_ko) if origin_ko else None,
            "origin_region": None,
            "variety": None,
            "process_method": self._extract_process(name),
            "base_price_per_kg": price,
            "is_in_stock": not is_soldout,
            "tiers": [],
        }

    def _parse_price(self, text: str) -> int:
        cleaned = re.sub(r"[^\d]", "", text)
        return int(cleaned) if cleaned else 0

    def _extract_origin(self, text: str | None) -> str | None:
        if not text:
            return None
        origins = [
            "에티오피아", "콜롬비아", "과테말라", "브라질", "케냐",
            "코스타리카", "파나마", "르완다", "부룬디", "예멘",
            "온두라스", "페루", "인도네시아", "엘살바도르", "탄자니아",
            "니카라과", "볼리비아", "우간다", "인도", "파푸아뉴기니",
            "베트남", "자메이카",
        ]
        for origin in origins:
            if origin in text:
                return origin
        return None

    def _extract_process(self, name: str) -> str | None:
        mapping = {
            "워시드": "Washed", "내추럴": "Natural", "허니": "Honey",
            "아나에로빅": "Anaerobic", "펄프드": "Pulped Natural",
        }
        for k, v in mapping.items():
            if k in name:
                return v
        return None
