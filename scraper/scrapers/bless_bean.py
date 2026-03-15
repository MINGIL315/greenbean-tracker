"""
블레스빈 (blessbean.co.kr) 스크래퍼
Gnuboard 기반 커스텀 쇼핑몰

AJAX POST: /shop/ajax.item_one_click.php → 전체 상품 HTML 반환
세션 쿠키 필요 (메인 페이지 먼저 GET)
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
SHOP_PAGE = f"{BASE_URL}/shop/item_one_click.php"
AJAX_URL = f"{BASE_URL}/shop/ajax.item_one_click.php"


class BlessBeanScraper(BaseScraper):
    COMPANY_NAME = "블레스빈"
    WEBSITE_URL = BASE_URL

    def fetch_products(self) -> list[dict]:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9",
        })

        # 쿠키 획득
        try:
            session.get(SHOP_PAGE, timeout=15)
        except Exception:
            pass

        # POST 요청
        try:
            resp = session.post(
                AJAX_URL,
                headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Referer": SHOP_PAGE,
                },
                data="",  # 빈 body → 전체 상품
                timeout=20,
            )
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            raise RuntimeError(f"블레스빈 AJAX 요청 실패: {e}")

        print(f"  [{self.COMPANY_NAME}] 응답 길이: {len(html)}자")
        print(f"  [{self.COMPANY_NAME}] 응답 앞 500자: {html[:500]}")

        if len(html) < 100:
            raise RuntimeError(f"블레스빈: 응답이 너무 짧음 ({len(html)}자)")

        soup = BeautifulSoup(html, "html.parser")
        products = []

        # 방법 A: table.oc_table
        table = soup.select_one("table.oc_table") or soup.find("table")
        if table:
            products = self._parse_table(table)

        # 방법 B: .item-list 카드
        if not products:
            products = self._parse_cards(soup)

        # 방법 C: tr 기반 (class 없는 테이블)
        if not products and soup.find("tr"):
            products = self._parse_any_table(soup)

        print(f"  [{self.COMPANY_NAME}] {len(products)}개 상품 파싱")
        return products

    def _parse_table(self, table) -> list[dict]:
        rows = table.find_all("tr")
        products = []
        current_origin = None

        for row in rows:
            classes = row.get("class", [])

            if "ca_sub_name" in classes:
                th = row.find("th") or row.find("td")
                if th:
                    current_origin = th.get_text(strip=True)
                continue

            if "it_list" not in classes:
                continue

            is_soldout = "soldout" in classes or row.get("data-it_soldout") == "1"

            name_el = row.select_one("td.it_name")
            price_el = row.select_one("td.it_price")

            if not name_el:
                continue

            name = re.sub(r"\s+", " ", name_el.get_text(" ", strip=True)).strip()
            price = self._parse_price(price_el.get_text(strip=True)) if price_el else 0

            if not name or price <= 0:
                continue

            origin_ko = self._extract_origin(name) or self._extract_origin(current_origin) or current_origin
            products.append(self._build(name, price, origin_ko, is_soldout))

        return products

    def _parse_cards(self, soup) -> list[dict]:
        products = []
        for item in soup.select(".item-list, .it_list"):
            name_el = item.select_one(".item-content strong, strong, .item-name")
            price_el = item.select_one(".item-price, .it_price")
            if not name_el:
                continue
            name = re.sub(r"\s+", " ", name_el.get_text(" ", strip=True)).strip()
            price = self._parse_price(price_el.get_text(strip=True)) if price_el else 0
            if not name or price <= 0:
                continue
            is_soldout = "soldout" in " ".join(item.get("class", []))
            origin_ko = self._extract_origin(name)
            products.append(self._build(name, price, origin_ko, is_soldout))
        return products

    def _parse_any_table(self, soup) -> list[dict]:
        """class 없는 테이블에서 상품명+가격 패턴 탐색"""
        products = []
        current_origin = None
        for row in soup.find_all("tr"):
            cells = row.find_all(["td", "th"])
            texts = [c.get_text(" ", strip=True) for c in cells]
            non_empty = [t for t in texts if t]

            if not non_empty:
                continue

            # 원산지 헤더: 셀 1개
            if len(non_empty) == 1:
                current_origin = non_empty[0]
                continue

            # 상품 행: 가격(원) 포함 여부 확인
            price = 0
            name = ""
            for i, t in enumerate(texts):
                if "원" in t or re.search(r"\d{4,}", t):
                    p = self._parse_price(t)
                    if 1000 <= p <= 10_000_000:
                        price = p
                        if i > 0:
                            name = texts[0]
                        break

            if name and price > 0:
                origin_ko = self._extract_origin(name) or self._extract_origin(current_origin) or current_origin
                products.append(self._build(name, price, origin_ko, False))

        return products

    def _build(self, name: str, price: int, origin_ko: str | None, is_soldout: bool) -> dict:
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
        if not cleaned:
            return 0
        val = int(cleaned)
        return val if val <= 10_000_000 else 0

    def _extract_origin(self, text: str | None) -> str | None:
        if not text:
            return None
        ko_origins = [
            "에티오피아", "콜롬비아", "과테말라", "브라질", "케냐",
            "코스타리카", "파나마", "르완다", "부룬디", "예멘",
            "온두라스", "페루", "인도네시아", "엘살바도르", "탄자니아",
            "니카라과", "볼리비아", "우간다", "인도", "파푸아뉴기니",
            "베트남", "자메이카",
        ]
        en_map = {
            "Ethiopia": "에티오피아", "Colombia": "콜롬비아", "Guatemala": "과테말라",
            "Brazil": "브라질", "Kenya": "케냐", "Costa Rica": "코스타리카",
            "Panama": "파나마", "Rwanda": "르완다", "Burundi": "부룬디",
            "Yemen": "예멘", "Honduras": "온두라스", "Peru": "페루",
            "Indonesia": "인도네시아", "El Salvador": "엘살바도르",
            "Tanzania": "탄자니아", "Nicaragua": "니카라과",
            "Bolivia": "볼리비아", "Uganda": "우간다", "India": "인도",
            "Papua": "파푸아뉴기니", "Vietnam": "베트남", "Jamaica": "자메이카",
        }
        for origin in ko_origins:
            if origin in text:
                return origin
        for en, ko in en_map.items():
            if en in text:
                return ko
        return None

    def _extract_process(self, name: str) -> str | None:
        mapping = {
            "워시드": "Washed", "Washed": "Washed", "washed": "Washed",
            "내추럴": "Natural", "Natural": "Natural", "natural": "Natural",
            "허니": "Honey", "Honey": "Honey",
            "아나에로빅": "Anaerobic", "Anaerobic": "Anaerobic",
            "펄프드": "Pulped Natural",
        }
        for k, v in mapping.items():
            if k in name:
                return v
        return None
