# 🌿 GreenBean Tracker

한국 생두 공급사의 가격을 자동으로 수집·비교하는 대시보드입니다.

## 프로젝트 구조

```
greenbean-tracker/
├── app/                           # Next.js App Router 페이지
│   ├── page.tsx                   # 메인 대시보드
│   ├── product/[id]/page.tsx      # 상품 상세 + 가격 이력 차트
│   ├── origin/[country]/page.tsx  # 원산지별 공급사 비교
│   └── admin/page.tsx             # 수동 가격 입력 관리 페이지
├── components/                    # React 컴포넌트
│   ├── CompanyCard.tsx            # 공급사 아코디언 카드
│   ├── ProductTable.tsx           # 상품 가격 테이블
│   ├── PriceCell.tsx              # 단가 셀 (구간가 툴팁 포함)
│   ├── PriceHistoryChart.tsx      # Recharts 기반 가격 이력 차트
│   ├── AlertModal.tsx             # 가격 알림 설정 모달
│   ├── OriginFilter.tsx           # 원산지 필터 드롭다운
│   ├── PriceTypeToggle.tsx        # 가격 유형 토글
│   ├── LastUpdatedBadge.tsx       # 마지막 수집 시각 배지
│   └── ErrorBoundary.tsx          # 에러 바운더리
├── scraper/                       # Python 스크래퍼 엔진
│   ├── main.py                    # 파이프라인 진입점
│   ├── base_scraper.py            # 추상 베이스 클래스
│   ├── db_client.py               # Supabase 연동
│   ├── normalizer.py              # 원산지명 정규화
│   ├── alert_checker.py           # 가격 알림 체크 + 이메일 발송
│   ├── email_template.py          # 이메일 HTML 템플릿
│   └── scrapers/
│       ├── hiend_coffee.py        # 하이엔드커피
│       ├── coffee_libre.py        # 커피리브레
│       ├── bean_brothers.py       # 빈브라더스
│       └── TEMPLATE.py            # 새 공급사 추가용 템플릿
├── supabase/migrations/           # DB 마이그레이션 SQL
│   ├── 001_initial_schema.sql
│   ├── 002_scrape_logs.sql
│   ├── 003_price_alerts.sql
│   └── 004_add_anomaly_flag.sql
├── lib/supabase.ts                # Supabase 클라이언트
├── types/index.ts                 # TypeScript 타입 정의
└── .github/workflows/
    └── daily_scrape.yml           # GitHub Actions 자동 스크래핑
```

---

## 로컬 개발 환경 설정

### 1. 의존성 설치

```bash
npm install
```

### 2. 환경 변수 설정

```bash
cp .env.local.example .env.local
```

`.env.local` 파일을 열고 Supabase 대시보드에서 값을 복사해 입력합니다:

```
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
```

### 3. 개발 서버 실행

```bash
npm run dev
```

`http://localhost:3000` 접속

---

## Supabase 마이그레이션 실행

Supabase 대시보드 → **SQL Editor** 에서 아래 파일들을 순서대로 실행:

```
supabase/migrations/001_initial_schema.sql
supabase/migrations/002_scrape_logs.sql
supabase/migrations/003_price_alerts.sql
supabase/migrations/004_add_anomaly_flag.sql
```

---

## 새 공급사 스크래퍼 추가 방법

총 5단계로 새 공급사를 추가할 수 있습니다.

### Step 1 — 템플릿 복사

```bash
cp scraper/scrapers/TEMPLATE.py scraper/scrapers/my_company.py
```

### Step 2 — 클래스 및 상수 설정

`my_company.py` 를 열고:
- 클래스명 변경: `NewCompanyScraper` → `MyCompanyScraper`
- `COMPANY_NAME` = 공급사 한글명
- `WEBSITE_URL` = 공급사 홈페이지 URL

### Step 3 — `fetch_products()` 구현

`get_page(url)` 로 HTML을 가져오고 BeautifulSoup으로 파싱합니다.
반환 형식은 다음 dict 구조를 따릅니다:

```python
{
    "company_name":      str,
    "product_name":      str,
    "origin_country":    str,       # normalize_origin() 사용
    "origin_region":     str | None,
    "variety":           str | None,
    "process_method":    str | None,
    "base_price_per_kg": int,
    "is_in_stock":       bool,
    "tiers": [
        {"tier_type": "bulk"|"membership"|"subscription",
         "min_kg": float|None, "max_kg": float|None, "price_per_kg": int}
    ]
}
```

### Step 4 — `main.py` 에 등록

```python
from scrapers.my_company import MyCompanyScraper

SCRAPERS = [
    HiendCoffeeScraper(),
    CoffeeLibreScraper(),
    BeanBrothersScraper(),
    MyCompanyScraper(),   # ← 추가
]
```

### Step 5 — 로컬 테스트

```bash
cd scraper
python -c "from scrapers.my_company import MyCompanyScraper; print(MyCompanyScraper().fetch_products()[:2])"
```

---

## 수동 스크래핑 실행

```bash
cd scraper
pip install -r requirements.txt
playwright install chromium
python main.py
```

---

## GitHub Actions Secrets 설정

GitHub 리포지토리 → **Settings → Secrets and variables → Actions** 에서 등록:

| Secret 이름 | 설명 |
|-------------|------|
| `SUPABASE_URL` | Supabase 프로젝트 URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase Service Role 키 |
| `RESEND_API_KEY` | Resend 이메일 API 키 |
| `ALERT_EMAIL` | 알림 수신 이메일 주소 |

등록 후 **Actions → Daily Green Bean Scraper → Run workflow** 로 수동 실행 테스트 가능합니다.
