"""
후성커피 (fscoffee.kr) 스크래퍼
Firstmall 플랫폼 — 상품 목록이 goodsSearch() AJAX로 동적 로딩
→ Playwright 사용

카테고리별 URL: /goods/catalog?code=XXXX
원산지: 상품명 앞에 괄호로 포함 (예: "(에티오피아) 구지 우라가 G1")
"""
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from base_scraper import BaseScraper
from normalizer import normalize_origin

BASE_URL = "https://www.fscoffee.kr"

# 카테고리 코드 → 원산지 힌트 (파싱 보조용)
CATEGORY_CODES = [
    ("0010", "에티오피아"),
    ("0009", "콜롬비아"),
    ("0012", "브라질"),
    ("0014", "과테말라"),
    ("0011", "케냐"),
    ("0008", "베트남"),
    ("0019", "인도"),
    ("0015", "코스타리카"),
    ("0017", "온두라스"),
    ("0020", "탄자니아"),
    ("0018", "인도네시아"),
    ("0016", "엘살바도르"),
    ("0013", "페루"),
]


class HsungCoffeeScraper(BaseScraper):
    COMPANY_NAME = "후성커피"
    WEBSITE_URL = BASE_URL

    def fetch_products(self) -> list[dict]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise RuntimeError("playwright 미설치. pip install playwright && playwright install chromium")

        products = []
        seen_names = set()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = context.new_page()

            for code, origin_hint in CATEGORY_CODES:
                url = f"{BASE_URL}/goods/catalog?code={code}"
                try:
                    page_num = 1
                    while True:
                        paged_url = url if page_num == 1 else f"{url}&page={page_num}&per=40"
                        page.goto(paged_url, timeout=30000, wait_until="domcontentloaded")
                        # 상품 목록이 AJAX로 로드될 때까지 대기
                        try:
                            page.wait_for_selector(".goods_list_item, .item_list li, ul.goods_list li, .prdList li", timeout=8000)
                        except Exception:
                            pass  # 상품 없는 카테고리일 수 있음

                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(page.content(), "html.parser")

                        # Firstmall 상품 목록 후보 셀렉터
                        items = (
                            soup.select("ul.goods_list li")
                            or soup.select(".goods_list_item")
                            or soup.select(".item_list li")
                            or soup.select("li.goods")
                        )

                        if not items:
                            break

                        page_products = []
                        for item in items:
                            try:
                                product = self._parse_item(item, origin_hint)
                                if product and product["product_name"] not in seen_names:
                                    seen_names.add(product["product_name"])
                                    page_products.append(product)
                            except Exception as e:
                                print(f"  [{self.COMPANY_NAME}] 상품 파싱 오류: {e}")

                        products.extend(page_products)
                        print(f"  [{self.COMPANY_NAME}] {origin_hint} p{page_num}: {len(page_products)}개")

                        if len(page_products) == 0:
                            break

                        # 다음 페이지 링크 확인
                        next_link = soup.select_one(f"a[href*='page={page_num + 1}']")
                        if not next_link:
                            break
                        page_num += 1
                        if page_num > 10:
                            break

                except Exception as e:
                    print(f"  [{self.COMPANY_NAME}] {origin_hint} 로드 실패: {e}")
                    continue

            browser.close()

        return products

    def _parse_item(self, item, origin_hint: str) -> dict | None:
        from bs4 import BeautifulSoup

        # 상품명: h3, .name, .goods_name, a[href*='view'] 등 시도
        name = ""
        for sel in ["h3", ".goods_name", ".name", ".item_name", "dt"]:
            el = item.select_one(sel)
            if el:
                name = el.get_text(" ", strip=True)
                name = re.sub(r"\s+", " ", name).strip()
                if name:
                    break

        if not name:
            a = item.find("a", href=re.compile(r"/goods/view"))
            if a:
                name = a.get_text(" ", strip=True).strip()

        if not name:
            return None

        # 가격: .price, .goods_price, span[class*='price'] 등
        price = 0
        for sel in [".price", ".goods_price", ".item_price", ".selling_price", "em"]:
            el = item.select_one(sel)
            if el:
                price = self._parse_price(el.get_text(strip=True))
                if price > 0:
                    break

        if price <= 0:
            return None

        # 품절: .soldout, [class*='soldout'], img[alt*='품절']
        is_soldout = bool(
            item.select_one(".soldout, .sold_out, [class*='soldout']")
            or item.find("img", alt=re.compile(r"품절"))
        )

        # 원산지: 상품명에서 추출, 없으면 카테고리 힌트 사용
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

    def _extract_origin(self, name: str) -> str | None:
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
