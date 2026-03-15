"""
커피플랜트 (coffeeplant.co.kr) 스크래퍼
가격표 페이지: /price
JavaScript 렌더링 필요 → Playwright 사용

테이블 컬럼 (8개):
  [0] 카테고리&품명
  [1] 수확년도
  [2] 사업자(20kg) — bulk tier
  [3] 소비자(5kg)  — 5kg tier
  [4] 소비자(1kg)  — base price
  [5] 가공방식
  [6] 커핑노트
  [7] 품종
"""
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from base_scraper import BaseScraper
from normalizer import normalize_origin

BASE_URL = "https://coffeeplant.co.kr"
PRICE_URL = f"{BASE_URL}/price"


class CoffeePlantScraper(BaseScraper):
    COMPANY_NAME = "커피플랜트"
    WEBSITE_URL = BASE_URL

    def fetch_products(self) -> list[dict]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise RuntimeError("playwright가 설치되지 않았습니다. pip install playwright && playwright install chromium")

        products = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(PRICE_URL, timeout=60000, wait_until="networkidle")
                # 테이블이 로드될 때까지 대기
                page.wait_for_selector("table", timeout=30000)
                html = page.content()
            finally:
                browser.close()

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        tables = soup.find_all("table")
        if not tables:
            raise RuntimeError("가격표를 찾을 수 없습니다 (table 요소 없음)")

        # 2번째 테이블이 생두 가격표 (첫 번째는 공지/헤더 테이블)
        price_table = tables[1] if len(tables) >= 2 else tables[0]
        rows = price_table.find_all("tr")
        print(f"  [{self.COMPANY_NAME}] 테이블 {len(rows)}행 발견")

        current_category = None

        for row in rows:
            cells = row.find_all(["td", "th"])
            cell_texts = [c.get_text(" ", strip=True) for c in cells]

            # 빈 행 건너뜀
            if len(cells) == 0:
                continue

            non_empty_texts = [t for t in cell_texts if t]

            # 헤더 행 건너뜀
            if non_empty_texts and non_empty_texts[0] in ("카테고리& 품 명", "카테고리&품명", "카테고리", "품명"):
                continue

            # 카테고리 헤더 행: 첫 번째 셀만 내용 있고 나머지 비어있음
            if len(non_empty_texts) == 1:
                current_category = non_empty_texts[0]
                continue

            # 상품 행: 최소 5개 컬럼에 내용 있어야 함
            if len(cells) < 5:
                continue

            try:
                product = self._parse_row(cell_texts, current_category)
                if product:
                    products.append(product)
            except Exception as e:
                print(f"  [{self.COMPANY_NAME}] 행 파싱 오류: {e} | {cell_texts}")
                continue

        return products

    def _parse_row(self, cells: list[str], category: str | None) -> dict | None:
        name = cells[0].strip()
        if not name:
            return None

        # 카테고리명 자체가 들어온 경우 skip
        if len(cells) < 5:
            return None

        # 1kg 소비자가 = base price (index 4)
        base_price_text = cells[4] if len(cells) > 4 else ""
        if not re.search(r"\d", base_price_text):
            return None

        base_price = self._parse_price_safe(base_price_text)
        if base_price <= 0:
            return None

        tiers = []

        # 사업자 20kg 가격 (index 2) → bulk tier
        # "24kg 46,000" = 24kg 구매 시 kg당 46,000원 (총액이 아님)
        bulk_text = cells[2] if len(cells) > 2 else ""
        bulk_min_kg, bulk_price = self._parse_bulk_text(bulk_text)
        if bulk_price and bulk_price > 0:
            tiers.append({
                "tier_type": "bulk",
                "min_kg": float(bulk_min_kg),
                "max_kg": None,
                "price_per_kg": bulk_price,
            })

        # 소비자 5kg 가격 (index 3) → subscription tier
        five_text = cells[3] if len(cells) > 3 else ""
        five_price = self._parse_price_safe(five_text)
        if five_price and five_price > 0 and five_price != base_price:
            tiers.append({
                "tier_type": "subscription",
                "min_kg": 5.0,
                "max_kg": None,
                "price_per_kg": five_price,
            })

        # 가공방식 (index 5)
        process_raw = cells[5] if len(cells) > 5 else ""
        process = self._normalize_process(process_raw)

        # 품종 (index 7)
        variety = cells[7].strip() if len(cells) > 7 else None
        if variety in ("", "-", "—"):
            variety = None

        # 이름에서 원산지 추출, 없으면 카테고리에서 추출
        origin_ko = self._extract_origin(name) or (
            self._extract_origin(category) if category else None
        )

        return {
            "company_name": self.COMPANY_NAME,
            "product_name": name,
            "origin_country": normalize_origin(origin_ko) if origin_ko else None,
            "origin_region": None,
            "variety": variety if variety else None,
            "process_method": process,
            "base_price_per_kg": base_price,
            "is_in_stock": True,  # 가격표에 표기된 상품은 재고 있음으로 간주
            "tiers": tiers,
        }

    def _parse_price_safe(self, text: str) -> int:
        """가격 텍스트에서 숫자 추출. 실패 시 0 반환"""
        if not text or not re.search(r"\d", text):
            return 0
        # 공백 포함 숫자 처리: "18 ,500" → "18500"
        cleaned = re.sub(r"[\s,]+", "", text)
        nums = re.findall(r"\d+", cleaned)
        if not nums:
            return 0
        # 가장 큰 숫자 선택
        for n in sorted(nums, key=lambda x: -int(x)):
            val = int(n)
            if val >= 1000:
                return val
        return 0

    def _parse_bulk_text(self, text: str) -> tuple[int, int]:
        """
        사업자(20kg) 컬럼 파싱.
        "Nkg M,000" 형태 → (N, M) : N kg 구매 시 kg당 M원
        "M,000" 형태 → (20, M) : 20kg 기준 kg당 M원
        반환: (min_kg, price_per_kg)
        """
        if not text or text.strip() in ("", "-", "—"):
            return (20, 0)
        if not re.search(r"\d", text):
            return (20, 0)

        # "24kg 46,000" 패턴: Nkg가 최소 구매량, 이후 숫자가 kg당 가격
        m = re.search(r"(\d+)\s*kg\s*([\d\s,]+)", text, re.IGNORECASE)
        if m:
            min_kg = int(m.group(1))
            price_text = m.group(2)
            price = self._parse_price_safe(price_text)
            return (min_kg, price)

        # 그냥 가격만 있는 경우 (기본 20kg)
        return (20, self._parse_price_safe(text))

    def _normalize_process(self, text: str) -> str | None:
        text = text.strip()
        if not text or text in ("-", "—"):
            return None
        mapping = {
            "워시드": "Washed", "washed": "Washed",
            "내추럴": "Natural", "natural": "Natural",
            "허니": "Honey", "honey": "Honey",
            "아나에로빅": "Anaerobic", "anaerobic": "Anaerobic",
            "펄프드": "Pulped Natural",
        }
        lower = text.lower()
        for k, v in mapping.items():
            if k.lower() in lower:
                return v
        return text  # 매핑 없으면 원문 반환

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
