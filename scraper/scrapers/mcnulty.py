"""
맥널티생두몰 (greenbeans.co.kr) 스크래퍼
Cafe24 플랫폼

실제 HTML 구조:
- 목록: ul.product-list > li
- 상품명: <span style="font-size:13px;color:#666666;">상품명</span>
          또는 img alt 텍스트
- 가격: <strong>21,000원</strong>
"""
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from bs4 import BeautifulSoup
from base_scraper import BaseScraper
from normalizer import normalize_origin

BASE_URL = "https://greenbeans.co.kr"
LIST_URL = f"{BASE_URL}/product/list.html?cate_no=128"


class McNultyScraper(BaseScraper):
    COMPANY_NAME = "맥널티생두몰"
    WEBSITE_URL = BASE_URL

    def fetch_products(self) -> list[dict]:
        products = []
        page = 1

        while True:
            url = LIST_URL if page == 1 else f"{LIST_URL}&page={page}"
            try:
                html = self.get_page(url)
            except Exception as e:
                print(f"  [{self.COMPANY_NAME}] 페이지 {page} 로드 실패: {e}")
                break

            soup = BeautifulSoup(html, "html.parser")
            items = soup.select("ul.product-list > li")

            if not items:
                # fallback: 상품 링크가 포함된 li
                items = [
                    li for li in soup.find_all("li")
                    if li.find("a", href=re.compile(r"/product/[^/]+/\d+/"))
                ]

            if not items:
                print(f"  [{self.COMPANY_NAME}] 페이지 {page}: 상품 없음 → 종료")
                break

            # 첫 페이지 첫 항목 구조 디버그 출력
            if page == 1 and items:
                print(f"  [{self.COMPANY_NAME}] 첫 항목 HTML: {str(items[0])[:500]}")

            print(f"  [{self.COMPANY_NAME}] 페이지 {page}: {len(items)}개 발견")

            for item in items:
                try:
                    product = self._parse_item(item)
                    if product:
                        products.append(product)
                except Exception as e:
                    print(f"  [{self.COMPANY_NAME}] 상품 파싱 오류: {e}")

            has_next = bool(soup.select_one(f"a[href*='page={page + 1}']"))
            if not has_next:
                break
            page += 1
            if page > 10:
                break

        return products

    def _parse_item(self, item) -> dict | None:
        # 상품명 1순위: span[style*="font-size:13px"]
        name = ""
        name_span = item.select_one('span[style*="font-size:13px"]')
        if name_span:
            name = name_span.get_text(" ", strip=True)

        # 2순위: img alt
        if not name:
            img = item.find("img", alt=True)
            if img and img["alt"].strip():
                name = img["alt"].strip()

        # 3순위: 상품 링크 텍스트
        if not name:
            a = item.find("a", href=re.compile(r"/product/[^/]+/\d+/"))
            if a:
                for hidden in a.select(".displaynone, .blind"):
                    hidden.decompose()
                name = a.get_text(" ", strip=True)

        name = re.sub(r"\s+", " ", name).strip()
        if not name:
            return None

        # 가격: strong 태그 중 "원" 포함 또는 4자리 이상 숫자 포함
        price = 0
        for strong in item.find_all("strong"):
            t = strong.get_text(strip=True)
            if "원" in t:
                price = self._parse_price(t)
                if price > 0:
                    break

        # 가격 fallback: "N,NNN원" 패턴 직접 탐색
        if price <= 0:
            all_text = item.get_text()
            matches = re.findall(r"([\d,]+)원", all_text)
            for m in matches:
                p = int(re.sub(r"[^\d]", "", m))
                if 1000 <= p <= 10_000_000:
                    price = p
                    break

        if price <= 0:
            print(f"  [{self.COMPANY_NAME}] 가격 파싱 실패: {name[:30]}")
            return None

        # 품절
        soldout_el = item.select_one(".soldout, .sold_out, [class*='soldout']")
        is_soldout = bool(soldout_el) and "displaynone" not in (soldout_el.get("class") or [])

        origin_ko = self._extract_origin(name)

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
        # 비정상적으로 큰 값 제거
        return val if val <= 10_000_000 else 0

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
            "Washed": "Washed", "Natural": "Natural", "Honey": "Honey",
        }
        for k, v in mapping.items():
            if k in name:
                return v
        return None
