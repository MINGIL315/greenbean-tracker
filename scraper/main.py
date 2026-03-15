"""
GreenBean Tracker — 스크래퍼 메인 파이프라인
"""
import time
from dotenv import load_dotenv

load_dotenv()

import db_client
from alert_checker import AlertChecker
from scrapers.coffee_libre import CoffeeLibreScraper
from scrapers.coffee_sys import CoffeeSysScraper
from scrapers.coffee_plant import CoffeePlantScraper
from scrapers.hsung_coffee import HsungCoffeeScraper
from scrapers.mcnulty import McNultyScraper
from scrapers.bless_bean import BlessBeanScraper

SCRAPERS = [
    CoffeeLibreScraper(),
    CoffeeSysScraper(),
    CoffeePlantScraper(),
    HsungCoffeeScraper(),
    McNultyScraper(),
    BlessBeanScraper(),
    # 하이엔드커피: 사이트 접속 불가 (연결 거부)
    # 빈브라더스: 생두 카테고리 없음
]


def run_pipeline():
    start_time = time.time()
    total_products = 0
    success_count = 0
    failed_scrapers = []

    for scraper in SCRAPERS:
        print(f"\n[{scraper.COMPANY_NAME}] 스크래핑 시작...")
        try:
            products = scraper.fetch_products()
            saved = 0
            for data in products:
                if not scraper.validate_product(data):
                    print(f"  ⚠️  유효하지 않은 상품 데이터 건너뜀: {data.get('product_name')}")
                    continue
                try:
                    product_id = db_client.upsert_product(data)
                    prev_price = db_client.get_latest_price(product_id)
                    is_anomaly = False
                    if prev_price is not None:
                        is_anomaly = scraper.is_anomaly(data["base_price_per_kg"], prev_price)
                        if is_anomaly:
                            print(f"  🚨 이상값 감지: {data['product_name']} "
                                  f"({prev_price:,}원 → {data['base_price_per_kg']:,}원)")

                    entry_id = db_client.insert_price_entry(product_id, data, is_anomaly=is_anomaly)
                    db_client.insert_price_tiers(entry_id, data.get("tiers", []))
                    saved += 1
                except Exception as e:
                    print(f"  ❌ DB 저장 실패: {data.get('product_name')} — {e}")

            total_products += saved
            success_count += saved
            print(f"  ✅ {scraper.COMPANY_NAME}: {saved}건 저장 완료")

        except Exception as e:
            print(f"  ❌ [{scraper.COMPANY_NAME}] 스크래퍼 실패: {e}")
            failed_scrapers.append(scraper.COMPANY_NAME)

    # 가격 알림 체크
    try:
        checker = AlertChecker()
        checker.run()
    except Exception as e:
        print(f"  ⚠️  알림 체크 실패: {e}")

    duration = round(time.time() - start_time, 2)

    # 실행 결과 로그 저장
    try:
        db_client.insert_scrape_log(
            total_products=total_products,
            success_count=success_count,
            fail_count=len(failed_scrapers),
            failed_scrapers=failed_scrapers,
            duration_seconds=duration,
        )
    except Exception as e:
        print(f"  ⚠️  스크래핑 로그 저장 실패: {e}")

    # 실행 결과 요약 출력
    print("\n" + "=" * 50)
    print(f"✅ 성공: {success_count}건", end="  |  ")
    if failed_scrapers:
        print(f"❌ 실패: {len(failed_scrapers)}개 스크래퍼 ({', '.join(failed_scrapers)})")
    else:
        print("❌ 실패: 없음")
    print(f"⏱️  소요 시간: {duration}초")
    print("=" * 50)


if __name__ == "__main__":
    run_pipeline()
