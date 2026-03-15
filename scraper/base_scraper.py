import random
import re
import time
from abc import ABC, abstractmethod

import requests
from bs4 import BeautifulSoup

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


class BaseScraper(ABC):
    COMPANY_NAME: str = ""
    WEBSITE_URL: str = ""

    MAX_RETRIES = 3
    RETRY_INTERVAL = 10  # seconds

    def get_page(self, url: str) -> str:
        """URL에서 HTML 반환 (재시도 로직 포함)"""
        for attempt in range(self.MAX_RETRIES):
            try:
                headers = {"User-Agent": random.choice(USER_AGENTS)}
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                # 요청 간 2~5초 랜덤 딜레이
                time.sleep(random.uniform(2, 5))
                return response.text
            except Exception as e:
                if attempt < self.MAX_RETRIES - 1:
                    print(f"[{self.COMPANY_NAME}] 재시도 {attempt + 1}/{self.MAX_RETRIES}: {e}")
                    time.sleep(self.RETRY_INTERVAL)
                else:
                    raise

    def parse_price(self, text: str) -> int:
        """'18,000원/kg' 형태의 텍스트에서 정수 추출"""
        digits = re.sub(r"[^\d]", "", text)
        if not digits:
            raise ValueError(f"가격 파싱 실패: {text!r}")
        return int(digits)

    def validate_product(self, data: dict) -> bool:
        """필수 필드 누락 or 가격 0 이하이면 False 반환"""
        required = ["company_name", "product_name", "base_price_per_kg"]
        for field in required:
            if not data.get(field):
                return False
        if data["base_price_per_kg"] <= 0:
            return False
        return True

    def is_anomaly(self, new_price: int, prev_price: int) -> bool:
        """전일 대비 50% 이상 변동 시 True 반환"""
        if prev_price == 0:
            return False
        return abs(new_price - prev_price) / prev_price > 0.5

    @abstractmethod
    def fetch_products(self) -> list[dict]:
        """공급사별 상품 목록 스크래핑 후 반환"""
        ...
