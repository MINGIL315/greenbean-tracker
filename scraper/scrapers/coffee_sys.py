"""
커피시스 (coffeesys.co.kr) 스크래퍼
생두 카테고리: /category/개인회원마켓/395/
총 ~52개 상품, 3페이지

HTML 구조:
- 상품: ul.prdList li.xans-record-[id^="anchorBoxId_"]
- 상품명: div.description strong.name a (span.displaynone 제외)
- 기본가: div.description[ec-data-price]
- 멤버십가: div.description[ec-data-custom] (있을 때만)
- 품절: thumbnail 영역에 img[alt="품절"]
"""
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from bs4 import BeautifulSoup
from base_scraper import BaseScraper
from normalizer import normalize_origin

BASE_URL = "https://coffeesys.co.kr"
CATEGORY_URL = f"{BASE_URL}/category/%EA%B0%9C%EC%9D%B8%ED%9A%8C%EC%9B%90%EB%A7%88%EC%BC%93/395/"


class CoffeeSysScraper(BaseScraper):
    COMPANY_NAME = "커피시스"
    WEBSITE_URL = BASE_URL

    def fetch_products(self) -> list[dict]:
        products = []
        page = 1

        while True:
            url = CATEGORY_URL if page == 1 else f"{CATEGORY_URL}?page={page}"
            try:
                html = self.get_page(url)
            except Exception as e:
                print(f"  [{self.COMPANY_NAME}] 페이지 {page} 로드 실패: {e}")
                break

            soup = BeautifulSoup(html, "html.parser")
            # id가 "anchorBoxId_"로 시작하는 실제 상품 항목만 선택
            items = [
                li for li in soup.select("ul.prdList li.xans-record-")
                if (li.get("id") or "").startswith("anchorBoxId_")
            ]

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
                    continue

            # 다음 페이지 확인: 현재 페이지 번호보다 큰 페이지 링크 존재 여부
            paging = soup.select_one(".ec-base-paginate")
            has_next = False
            if paging:
                current_page_el = paging.select_one("a.this")
                if current_page_el:
                    try:
                        current_num = int(re.search(r"page=(\d+)", current_page_el.get("href", "")).group(1))
                        for a in paging.select("a.other"):
                            m = re.search(r"page=(\d+)", a.get("href", ""))
                            if m and int(m.group(1)) > current_num:
                                has_next = True
                                break
                    except Exception:
                        pass
            if not has_next:
                break
            page += 1
            if page > 10:
                break

        return products

    def _parse_item(self, item) -> dict | None:
        desc = item.select_one("div.description")
        if not desc:
            return None

        # 상품명: displaynone span 제거 후 텍스트 추출
        name_el = desc.select_one("strong.name a")
        if not name_el:
            return None
        for hidden in name_el.select("span.displaynone, .title.displaynone"):
            hidden.decompose()
        name = name_el.get_text(" ", strip=True)
        name = re.sub(r"\s+", " ", name).strip()
        if not name:
            return None

        # 기본가: ec-data-price 속성
        price_attr = desc.get("ec-data-price", "")
        if not price_attr or not price_attr.isdigit():
            return None
        base_price = int(price_attr)
        if base_price <= 0:
            return None

        # 멤버십가: ec-data-custom 속성
        tiers = []
        custom_attr = desc.get("ec-data-custom", "")
        if custom_attr and custom_attr.isdigit():
            m_price = int(custom_attr)
            if m_price > 0 and m_price != base_price:
                tiers.append({
                    "tier_type": "membership",
                    "min_kg": None,
                    "max_kg": None,
                    "price_per_kg": m_price,
                })

        # 품절 여부: thumbnail 내 img[alt="품절"] 존재 여부
        thumbnail = item.select_one("div.thumbnail")
        soldout_img = thumbnail.find("img", alt="품절") if thumbnail else None
        if soldout_img:
            is_in_stock = False
        else:
            soldout_el = item.select_one(".soldOut")
            is_in_stock = soldout_el is None or "displaynone" in (soldout_el.get("class") or [])

        origin_ko = self._extract_origin(name)
        process = self._extract_process(name)
        variety = self._extract_variety(name)

        return {
            "company_name": self.COMPANY_NAME,
            "product_name": name,
            "origin_country": normalize_origin(origin_ko) if origin_ko else None,
            "origin_region": None,
            "variety": variety,
            "process_method": process,
            "base_price_per_kg": base_price,
            "is_in_stock": is_in_stock,
            "tiers": tiers,
        }

    def _extract_origin(self, name: str) -> str | None:
        origins = [
            "에티오피아", "콜롬비아", "과테말라", "브라질", "케냐",
            "코스타리카", "파나마", "르완다", "부룬디", "예멘",
            "온두라스", "페루", "인도네시아", "엘살바도르", "탄자니아",
            "니카라과", "볼리비아", "우간다", "인도", "파푸아뉴기니",
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
        varieties = ["게이샤", "버번", "카투라", "SL28", "SL34", "74110", "74112", "파카마라", "게샤"]
        for v in varieties:
            if v in name:
                return v
        return None
