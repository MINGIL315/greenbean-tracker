def build_alert_email(product_name: str, company_name: str, origin: str,
                      current_price: int, target_price: int, website_url: str) -> dict:
    """가격 알림 이메일 제목 + HTML 본문 반환"""
    subject = f"🎯 [{product_name}] 목표가 달성!"

    html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f9fafb; margin: 0; padding: 20px; }}
    .container {{ max-width: 480px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
    .header {{ background: #16a34a; color: white; padding: 24px; }}
    .header h1 {{ margin: 0; font-size: 20px; }}
    .body {{ padding: 24px; }}
    .row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f0f0f0; font-size: 14px; }}
    .label {{ color: #6b7280; }}
    .value {{ font-weight: 600; color: #111827; }}
    .price-current {{ font-size: 24px; font-weight: 700; color: #16a34a; }}
    .price-target {{ font-size: 14px; color: #9ca3af; }}
    .btn {{ display: block; margin: 20px 0 0; text-align: center; background: #16a34a; color: white; padding: 12px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 14px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🎯 목표가 달성 알림</h1>
      <p style="margin:4px 0 0; opacity:.8; font-size:13px;">설정하신 목표가 이하로 가격이 내려왔습니다.</p>
    </div>
    <div class="body">
      <div class="row"><span class="label">상품명</span><span class="value">{product_name}</span></div>
      <div class="row"><span class="label">공급사</span><span class="value">{company_name}</span></div>
      <div class="row"><span class="label">원산지</span><span class="value">{origin or '—'}</span></div>
      <div style="padding: 16px 0; text-align:center;">
        <div class="price-current">{current_price:,}원/kg</div>
        <div class="price-target">설정 목표가: {target_price:,}원/kg</div>
      </div>
      {"<a href='" + website_url + "' class='btn'>공급사 바로가기</a>" if website_url else ""}
    </div>
  </div>
</body>
</html>
"""
    return {"subject": subject, "html": html}
