"""
후성커피 (fscoffee.kr) 스크래퍼
Firstmall 플랫폼 — goodsSearch() AJAX 동적 로딩
→ Playwright + page.evaluate() 로 렌더링 후 JS로 직접 추출

카테고리별 URL: /goods/catalog?code=XXXX
원산지: 상품명에 괄호로 포함 (예: "(에티오피아) 구지 우라가 G1")
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

# 렌더링 후 JS로 상품 추출
EXTRACT_JS = """() => {
    const results = [];
    const lis = document.querySelectorAll('li');
    lis.forEach(li => {
        const link = li.querySelector('a[href*="/goods/view"]');
        if (!link) return;

        // 상품명
        let name = '';
        const nameEl = li.querySelector('.goods_name, .name, h3, h4, dt, .item_name, .tit');
        if (nameEl) name = nameEl.innerText.trim();
        if (!name) {
            const img = li.querySelector('img');
            if (img) name = (img.alt || '').trim();
        }
        if (!name) name = link.innerText.trim();

        // 가격
        let priceText = '';
        const priceEl = li.querySelector('.price, .goods_price, .selling_price, .item_price, em, strong');
        if (priceEl) priceText = priceEl.innerText.trim();
        if (!priceText) {
            const m = li.innerText.match(/[\\d,]+원/);
            if (m) priceText = m[0];
        }

        // 품절
        const soldout = !!li.querySelector('.soldout, .sold_out, [class*="soldout"]');

        if (name && priceText) {
            results.push({ name, priceText, soldout });
        }
    });
    return results;
}"""


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
        debug_printed = False

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            pw_page = context.new_page()

            for code, origin_hint in CATEGORY_CODES:
                url = f"{BASE_URL}/goods/catalog?code={code}&per=40"
                try:
                    pw_page.goto(url, timeout=30000, wait_until="networkidle")
                    time.sleep(1)

                    # JS로 렌더링된 DOM에서 직접 추출
                    raw = pw_page.evaluate(EXTRACT_JS)

                    # 첫 번째 카테고리에서 디버그 출력
                    if not debug_printed:
                        print(f"  [{self.COMPANY_NAME}] JS 추출 샘플: {raw[:3]}")
                        debug_printed = True

                    new_items = []
                    for r in raw:
                        if r["name"] in seen_names:
                            continue
                        product = self._make_product(r, origin_hint)
                        if product:
                            seen_names.add(r["name"])
                            new_items.append(product)

                    products.extend(new_items)
                    print(f"  [{self.COMPANY_NAME}] {origin_hint}: {len(new_items)}개")

                except Exception as e:
                    print(f"  [{self.COMPANY_NAME}] {origin_hint} 실패: {e}")
                    continue

            browser.close()

        return products

    def _make_product(self, raw: dict, origin_hint: str) -> dict | None:
        name = re.sub(r"\s+", " ", raw["name"]).strip()
        if not name or len(name) < 3:
            return None

        price = self._parse_price(raw.get("priceText", ""))
        if price <= 0:
            return None

        origin_ko = self._extract_origin(name) or origin_hint

        return {
            "company_name": self.COMPANY_NAME,
            "product_name": name,
            "origin_country": normalize_origin(origin_ko) if origin_ko else None,
            "origin_region": None,
            "variety": None,
            "process_method": self._extract_process(name),
            "base_price_per_kg": price,
            "is_in_stock": not raw.get("soldout", False),
            "tiers": [],
        }

    def _parse_price(self, text: str) -> int:
        cleaned = re.sub(r"[^\d]", "", text)
        if not cleaned:
            return 0
        val = int(cleaned)
        return val if 100 <= val <= 10_000_000 else 0

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
