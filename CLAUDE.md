# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Frontend (Next.js)
```bash
npm run dev       # 개발 서버 (localhost:3000)
npm run build     # 프로덕션 빌드
npm run lint      # ESLint
```

### Scraper (Python)
```bash
cd scraper
pip install -r requirements.txt
playwright install chromium

# 전체 파이프라인 실행 (환경변수 직접 전달)
SUPABASE_URL=https://xxx.supabase.co SUPABASE_SERVICE_ROLE_KEY=xxx python main.py

# 단일 스크래퍼 테스트
python -c "from scrapers.coffee_libre import CoffeeLibreScraper; print(CoffeeLibreScraper().fetch_products()[:1])"
```

### DB 마이그레이션
Supabase 대시보드 SQL Editor에서 `supabase/migrations/` 파일을 001→004 순서로 실행.
(직접 DB 연결 불가 — Supabase 프로젝트가 IPv6 전용이라 로컬 환경에서 psql/pg 접속 안 됨)

---

## Architecture

### 데이터 흐름
```
Python scraper (daily) → Supabase DB → Next.js frontend
```

스크래퍼는 GitHub Actions(`daily_scrape.yml`)로 매일 KST 07:00 자동 실행됩니다. `main.py`가 각 공급사 스크래퍼를 순차 실행하고, 결과를 `db_client.py`를 통해 Supabase에 저장합니다. 실행 후 `alert_checker.py`가 가격 알림 조건을 확인해 Resend API로 이메일을 발송합니다.

### DB 스키마 관계
```
companies → products → price_entries → price_tiers
                    ↑
              price_alerts (product_id 참조)
              scrape_logs  (독립 테이블)
```

- `price_entries`: 스크래핑 시점마다 스냅샷 저장 (이력 유지, 덮어쓰지 않음)
- `price_tiers`: 구간가(`bulk`), 멤버십가(`membership`), 구독가(`subscription`) 분리 저장
- `is_anomaly`: 전일 대비 50% 이상 가격 변동 시 `true`

### 현재 활성 스크래퍼
- **커피리브레** (`scrapers/coffee_libre.py`): `/product/list.html?cate_no=48`, 316개 상품
- **커피시스** (`scrapers/coffee_sys.py`): `/category/개인회원마켓/395/`, 52개 상품, 3페이지. 기본가는 `div.description[ec-data-price]`, 멤버십가는 `[ec-data-custom]`, 상품은 `li[id^="anchorBoxId_"]`로 필터링.
- **커피플랜트** (`scrapers/coffee_plant.py`): `/price`, 77개 상품. JS 렌더링 필요 → Playwright 사용. 컬럼: 카테고리&품명|수확년도|사업자(20kg)|소비자(5kg)|소비자(1kg)|가공방식|커핑노트|품종. "Nkg M원" 형태 = N kg 구매 시 kg당 M원. 카테고리 행: non_empty 셀이 1개인 행.
- 하이엔드커피: 사이트 접속 불가 (연결 거부)
- 빈브라더스: 생두 카테고리 없음 (원두 전문)

### 품절 판별 로직 (커피리브레)
`.soldOut` 요소가 항상 DOM에 존재하므로 단순 존재 여부로 판단하면 안 됨.
`displaynone` 클래스가 있으면 재고 있음, 없으면 품절.
```python
soldout_el = item.select_one(".soldOut")
is_in_stock = soldout_el is None or "displaynone" in (soldout_el.get("class") or [])
```

### `db_client.py` upsert 방식
`companies` 테이블에 `name` unique constraint가 없으므로 `.upsert(on_conflict=...)` 사용 불가.
select → 없으면 insert 패턴으로 처리.

### Frontend 대시보드 (`/`)
- 클라이언트 컴포넌트. Supabase에서 `companies → products → price_entries → price_tiers` 중첩 select로 한 번에 fetch
- `ProductTable`: 각 상품의 **최저가**(base_price와 모든 tier 중 min)를 표시. 컬럼(상품명/원산지/최저가/재고) 클릭으로 정렬 가능
- `/product/[id]` — SSR. 가격 이력 차트 + 7일/30일/90일/전체 필터
- `/origin/[country]` — SSR. 해당 원산지 공급사 비교
- `/admin` — 수동 가격 입력 폼

### Supabase 클라이언트
`lib/supabase.ts`는 Proxy 패턴으로 지연 초기화. 빌드 시 환경변수 없어도 에러 없이 통과하고 런타임 호출 시점에서 예외 발생.

### 새 공급사 스크래퍼 추가
1. `scraper/scrapers/TEMPLATE.py` 복사 후 `fetch_products()` 구현
2. `main.py`의 `SCRAPERS` 리스트에 추가
3. 필요 시 `normalizer.py`의 `ORIGIN_MAP`에 원산지 추가

### 환경변수
| 변수 | 용도 |
|------|------|
| `NEXT_PUBLIC_SUPABASE_URL` | 프론트엔드 Supabase URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | 프론트엔드 익명 키 |
| `SUPABASE_SERVICE_ROLE_KEY` | 스크래퍼 Service Role 키 |
| `RESEND_API_KEY` | 이메일 알림 (스크래퍼, 선택) |
| `ALERT_EMAIL` | 알림 수신 이메일 (스크래퍼, 선택) |

GitHub Actions Secrets에 `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `RESEND_API_KEY`, `ALERT_EMAIL` 등록 필요.
