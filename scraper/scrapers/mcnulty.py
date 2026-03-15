"""
맥널티생두몰 (greenbeans.co.kr) 스크래퍼
Cafe24 플랫폼 — 맥널티인터내셔널 운영 생두 전용몰
URL: /product/list.html?cate_no=128 (전체)
총 ~34개 상품, 3페이지
원산지: 카테고리명 또는 상품명에서 추출
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

# 원산지별 카테고리 (origin 파싱 보조용)
ORIGIN_CATEGORIES = {
    "42": "브라질", "35": "에티오피아", "47": "콜롬비아",
    "48": "베트남", "49": "인도", "25": "아메리카",
    "27": "아프리카", "26": "아시아", "28": "오세아니아",
}


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

            # Cafe24 표준 구조 시도 (커스텀 테마라도 ec-data- 속성은 유지되는 경우 많음)
            items = [
                li for li in soup.select("ul.prdList li.xans-record-, li[id^='anchorBoxId_'], .prdList li")
                if li.get("id", "").startswith("anchorBoxId_") or li.select_one("[ec-data-price]")
            ]

            # 표준 구조 없으면 상품 링크 기반으로 파싱
            if not items:
                items = self._find_items_by_link(soup)

            if not items:
                print(f"  [{self.COMPANY_NAME}] 페이지 {page}: 상품 없음 → 종료")
                break

            print(f"  [{self.COMPANY_NAME}] 페이지 {page}: {len(items)}개 발견")

            for item in items:
                try:
                    product = self._parse_item(item)
                    if product:
                        products.append(product)
                except Exception as e:
                    print(f"  [{self.COMPANY_NAME}] 상품 파싱 오류: {e}")

            # 다음 페이지 확인
            has_next = bool(soup.select_one(f"a[href*='page={page + 1}']"))
            if not has_next:
                break
            page += 1
            if page > 10:
                break

        return products

    def _find_items_by_link(self, soup) -> list:
        """상품 링크 패턴으로 상품 컨테이너 탐색"""
        links = soup.find_all("a", href=re.compile(r"/product/[^/]+/\d+/"))
        containers = []
        seen = set()
        for a in links:
            parent = a.find_parent("li") or a.find_parent("div")
            if parent and id(parent) not in seen:
                seen.add(id(parent))
                containers.append(parent)
        return containers

    def _parse_item(self, item) -> dict | None:
        # 상품명
        name = ""
        desc = item.select_one("div.description, .prdInfo, .name")
        if desc:
            name_el = desc.select_one("strong.name a, .prdName, .name a, a")
            if name_el:
                for hidden in name_el.select(".displaynone, .blind"):
                    hidden.decompose()
                name = name_el.get_text(" ", strip=True)
        if not name:
            # ec-data-price가 있는 a 태그에서 찾기
            a = item.find("a", href=re.compile(r"/product/[^/]+/\d+/"))
            if a:
                for hidden in a.select(".displaynone, .blind"):
                    hidden.decompose()
                name = a.get_text(" ", strip=True)

        name = re.sub(r"\s+", " ", name).strip()
        if not name:
            return None

        # 가격: ec-data-price 속성 우선
        desc_el = item.select_one("[ec-data-price]")
        if desc_el:
            price_attr = desc_el.get("ec-data-price", "")
            price = int(price_attr) if price_attr.isdigit() else 0
        else:
            # 텍스트에서 가격 파싱
            price_el = item.select_one(".price, .cost, strong, em")
            price = self._parse_price(price_el.get_text(strip=True)) if price_el else 0

        if price <= 0:
            return None

        # 품절
        soldout_el = item.select_one(".soldout, .sold_out, [class*='soldout']")
        is_soldout = False
        if soldout_el:
            is_soldout = "displaynone" not in (soldout_el.get("class") or [])

        # 원산지: 상품명에서 추출
        # 상품 URL에서 카테고리 코드 추출해 원산지 힌트 얻기
        origin_ko = self._extract_origin(name)
        if not origin_ko:
            a = item.find("a", href=re.compile(r"/product/"))
            if a:
                m = re.search(r"/category/(\d+)/", a.get("href", ""))
                if m:
                    origin_ko = ORIGIN_CATEGORIES.get(m.group(1))

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
