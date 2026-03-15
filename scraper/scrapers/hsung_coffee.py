"""
후성커피 (fscoffee.kr) 스크래퍼
Firstmall 플랫폼 — 상품 목록이 goodsSearch() AJAX로 동적 로딩
→ Playwright + networkidle 대기

카테고리별 URL: /goods/catalog?code=XXXX
원산지: 상품명 앞에 괄호로 포함 (예: "(에티오피아) 구지 우라가 G1")
"""
import re
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from base_scraper import BaseScraper
from normalizer import normalize_origin

BASE_URL = "https://www.fscoffee.kr"

CATEGORY_CODES = [
    ("0010", "에티오피아"), ("0009", "콜롬비아"), ("0012", "브라질"),
    ("0014", "과테말라"), ("0011", "케냐"), ("0008", "베트남"),
    ("0019", "인도"), ("0015", "코스타리카"), ("0017", "온두라스"),
    ("0020", "탄자니아"), ("0018", "인도네시아"), ("0016", "엘살바도르"),
    ("0013", "페루"),
]


class HsungCoffeeScraper(BaseScraper):
    COMPANY_NAME = "후성커피"
    WEBSITE_URL = BASE_URL

    def fetch_products(self) -> list[dict]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise RuntimeError("playwright 미설치")

        products = []
        seen_names = set()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            pw_page = context.new_page()

            for code, origin_hint in CATEGORY_CODES:
                url = f"{BASE_URL}/goods/catalog?code={code}&per=40"
                try:
                    # networkidle: 모든 AJAX 완료까지 대기
                    pw_page.goto(url, timeout=30000, wait_until="networkidle")
                    time.sleep(1)  # 추가 렌더링 대기
                    html = pw_page.content()

                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, "html.parser")

                    page_products = self._extract_products(soup, origin_hint)
                    new_items = [p for p in page_products if p["product_name"] not in seen_names]
                    for p in new_items:
                        seen_names.add(p["product_name"])
                    products.extend(new_items)
                    print(f"  [{self.COMPANY_NAME}] {origin_hint}: {len(new_items)}개")

                except Exception as e:
                    print(f"  [{self.COMPANY_NAME}] {origin_hint} 실패: {e}")
                    continue

            browser.close()

        return products

    def _extract_products(self, soup, origin_hint: str) -> list[dict]:
        """
        Firstmall 렌더링 후 상품 요소 추출.
        가격 텍스트(원)를 포함하는 li/div 요소를 탐색.
        """
        from bs4 import BeautifulSoup
        products = []

        # Firstmall 일반 상품 목록 셀렉터 후보
        items = (
            soup.select("ul.goods_list > li")
            or soup.select("#goodsList li")
            or soup.select(".goods_list_wrap li")
            or soup.select("ul[class*='goods'] li")
            or soup.select("div[class*='goods_item']")
        )

        # 셀렉터 실패 시: 가격 텍스트를 포함하는 li 요소 탐색
        if not items:
            items = [
                li for li in soup.find_all("li")
                if re.search(r"\d{4,}원", li.get_text())
                and li.find("a", href=re.compile(r"/goods/view"))
            ]

        for item in items:
            try:
                product = self._parse_item(item, origin_hint)
                if product:
                    products.append(product)
            except Exception:
                continue

        return products

    def _parse_item(self, item, origin_hint: str) -> dict | None:
        # 상품명: a[href*='view'] 텍스트, h3, .goods_name, .name 순으로 시도
        name = ""
        for sel in [".goods_name", ".name", "h3", "dt", "strong"]:
            el = item.select_one(sel)
            if el:
                candidate = el.get_text(" ", strip=True)
                candidate = re.sub(r"\s+", " ", candidate).strip()
                if len(candidate) > 3:
                    name = candidate
                    break

        if not name:
            a = item.find("a", href=re.compile(r"/goods/view"))
            if a:
                name = a.get_text(" ", strip=True).strip()
                name = re.sub(r"\s+", " ", name).strip()

        if not name:
            return None

        # 가격: "원" 포함 텍스트에서 숫자 추출
        price = 0
        for sel in [".price", ".goods_price", ".selling_price", "em", "strong", "span"]:
            for el in item.select(sel):
                t = el.get_text(strip=True)
                if "원" in t:
                    p = self._parse_price(t)
                    if p > 0:
                        price = p
                        break
            if price > 0:
                break

        # 전체 텍스트에서 가격 패턴 탐색 (fallback)
        if price <= 0:
            all_text = item.get_text()
            matches = re.findall(r"([\d,]+)원", all_text)
            for m in matches:
                p = int(re.sub(r"[^\d]", "", m))
                if p >= 1000:
                    price = p
                    break

        if price <= 0:
            return None

        is_soldout = bool(
            item.select_one(".soldout, .sold_out, [class*='soldout']")
            or item.find("img", alt=re.compile(r"품절"))
        )

        origin_ko = self._extract_origin(name) or origin_hint

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

    def _extract_origin(self, name: str | None) -> str | None:
        if not name:
            return None
        origins = [
            "에티오피아", "콜롬비아", "과테말라", "브라질", "케냐",
            "코스타리카", "파나마", "르완다", "부룬디", "예멘",
            "온두라스", "페루", "인도네시아", "엘살바도르", "탄자니아",
            "니카라과", "볼리비아", "우간다", "인도", "파푸아뉴기니",
            "베트남", "자메이카",
        ]
        for origin in origins:
            if origin in name:
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
