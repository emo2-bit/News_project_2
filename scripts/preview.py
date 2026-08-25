"""4단계 확인용: confidence 강조 표시가 실제로 어떻게 보이는지 미리보기 HTML 생성.

5단계(이메일/사이트 발송)에서 정식 템플릿을 만들 때 이 렌더링 로직(lib/render.py)을
그대로 재사용한다. 이 스크립트 자체는 디자인 확인용 임시 산출물이다.
"""

import json
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.render import render_article_list

ROOT = Path(__file__).resolve().parent.parent


def main():
    date = sys.argv[1] if len(sys.argv) > 1 else None
    if not date:
        candidates = sorted((ROOT / "data").glob("????-??-??.json"))
        if not candidates:
            print("data/{날짜}.json 이 없습니다. 먼저 3단계 판단 결과를 만들어주세요.")
            return
        date = candidates[-1].stem

    data_path = ROOT / "data" / f"{date}.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    articles = sorted(data["articles"], key=lambda a: -a["relevance"])

    low_count = sum(1 for a in articles if a["confidence"] == "low")

    html_out = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>미리보기 - {date}</title>
</head>
<body style="font-family:-apple-system,'Malgun Gothic',sans-serif;background:#f3f4f6;padding:24px;">
  <div style="max-width:720px;margin:0 auto;">
    <h1 style="font-size:20px;">반도체 뉴스 판단 결과 — {date}</h1>
    <p style="color:#6b7280;font-size:14px;">총 {len(articles)}건, 확신 낮음 {low_count}건</p>
    {render_article_list(articles)}
  </div>
</body>
</html>"""

    out_path = ROOT / "site" / "preview.html"
    out_path.write_text(html_out, encoding="utf-8")
    print(f"[preview] {out_path} 생성 완료 ({len(articles)}건, 확신 낮음 {low_count}건)")


if __name__ == "__main__":
    main()
