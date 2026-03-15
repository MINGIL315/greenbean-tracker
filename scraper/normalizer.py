ORIGIN_MAP = {
    "에티오피아": "Ethiopia",
    "콜롬비아":   "Colombia",
    "과테말라":   "Guatemala",
    "브라질":     "Brazil",
    "케냐":       "Kenya",
    "코스타리카": "Costa Rica",
    "파나마":     "Panama",
    "르완다":     "Rwanda",
    "부룬디":     "Burundi",
    "예멘":       "Yemen",
    "온두라스":   "Honduras",
    "페루":       "Peru",
    "인도네시아": "Indonesia",
    "엘살바도르": "El Salvador",
    "니카라과":   "Nicaragua",
    "멕시코":     "Mexico",
    "탄자니아":   "Tanzania",
    "우간다":     "Uganda",
    "볼리비아":   "Bolivia",
    "인도":       "India",
    "중국":       "China",
    "하와이":     "Hawaii",
    "자메이카":   "Jamaica",
    "파푸아뉴기니": "Papua New Guinea",
    "짐바브웨":   "Zimbabwe",
    "베트남":     "Vietnam",
    "자메이카":   "Jamaica",
}


def normalize_origin(raw: str) -> str:
    """한국어 원산지명을 영문 표준명으로 변환"""
    raw = raw.strip()
    for ko, en in ORIGIN_MAP.items():
        if ko in raw:
            return en
    return raw
