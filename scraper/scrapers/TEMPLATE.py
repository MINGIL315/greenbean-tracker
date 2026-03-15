# TODO: 1. 클래스명을 공급사명으로 변경
# TODO: 2. COMPANY_NAME, WEBSITE_URL 설정
# TODO: 3. fetch_products() 구현
# TODO: 4. main.py SCRAPERS 리스트에 추가

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from base_scraper import BaseScraper
from normalizer import normalize_origin


class NewCompanyScraper(BaseScraper):
    COMPANY_NAME = "공급사명"
    WEBSITE_URL  = "https://example.com"

    def fetch_products(self) -> list[dict]:
        # TODO: 여기에 파싱 로직 구현
        # 반환 형식 예시:
        # return [{
        #     "company_name":      self.COMPANY_NAME,
        #     "product_name":      "에티오피아 예가체프 G1",
        #     "origin_country":    normalize_origin("에티오피아"),
        #     "origin_region":     "예가체프",
        #     "variety":           "헤이룸",
        #     "process_method":    "Washed",
        #     "base_price_per_kg": 18000,
        #     "is_in_stock":       True,
        #     "tiers": [
        #         {"tier_type": "bulk", "min_kg": 5.0, "max_kg": None, "price_per_kg": 16500},
        #         {"tier_type": "membership", "min_kg": None, "max_kg": None, "price_per_kg": 15000},
        #     ],
        # }]
        raise NotImplementedError
