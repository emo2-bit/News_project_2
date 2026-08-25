"""5단계: GitHub Pages용 정적 사이트 생성 (날짜별 아카이브 + 피드백 버튼).

data/{날짜}.json 전체를 읽어 site/index.html(최신일 + 아카이브 목록)과
site/archive/{날짜}.html(해당 날짜 전체)을 만든다. git_publish.py(6단계)가
이 산출물을 커밋/푸시하면 GitHub Actions가 그대로 배포한다(스펙 1절 — 빌드에
AI 판단이 없으므로 Actions에 API 키가 필요 없음).
"""

import json
import sys
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.config import FORM_ENTRY_ARTICLE_ID, FORM_ENTRY_VOTE, FORM_SUBMIT_URL
from lib.render import render_article_list, render_feedback_script

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SITE_DIR = ROOT / "site"

PAGE_STYLE = (
    "font-family:-apple-system,'Malgun Gothic',sans-serif;background:#f3f4f6;"
    "margin:0;padding:24px;"
)


def _page(title: str, date_label: str, body: str, nav: str, feedback_script: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
</head>
<body style="{PAGE_STYLE}">
  <div style="max-width:720px;margin:0 auto;">
    <h1 style="font-size:20px;margin-bottom:4px;">반도체 뉴스 판단 결과</h1>
    <p style="color:#6b7280;font-size:14px;margin-top:0;">{date_label}</p>
    {nav}
    {body}
    <p style="color:#9ca3af;font-size:12px;margin-top:24px;">
      마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')} KST
    </p>
  </div>
  {feedback_script}
</body>
</html>"""


def load_all_dates() -> list[str]:
    return sorted(p.stem for p in DATA_DIR.glob("????-??-??.json"))


def build_archive_page(date: str, all_dates: list[str]) -> None:
    data = json.loads((DATA_DIR / f"{date}.json").read_text(encoding="utf-8"))
    articles = sorted(data["articles"], key=lambda a: -a["relevance"])
    low_count = sum(1 for a in articles if a["confidence"] == "low")

    nav = '<p style="margin-bottom:16px;"><a href="../index.html" style="color:#2563eb;">← 전체 아카이브</a></p>'
    body = render_article_list(articles, include_feedback=True)
    feedback_script = render_feedback_script(FORM_SUBMIT_URL, FORM_ENTRY_ARTICLE_ID, FORM_ENTRY_VOTE)

    html_out = _page(
        title=f"{date} - 반도체 뉴스",
        date_label=f"{date} · 총 {len(articles)}건 · 확신 낮음 {low_count}건",
        body=body,
        nav=nav,
        feedback_script=feedback_script,
    )

    archive_dir = SITE_DIR / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    (archive_dir / f"{date}.html").write_text(html_out, encoding="utf-8")


def build_index_page(all_dates: list[str]) -> None:
    latest = all_dates[-1]
    data = json.loads((DATA_DIR / f"{latest}.json").read_text(encoding="utf-8"))
    articles = sorted(data["articles"], key=lambda a: -a["relevance"])
    low_count = sum(1 for a in articles if a["confidence"] == "low")

    archive_links = "\n".join(
        f'<li><a href="archive/{d}.html" style="color:#2563eb;">{d}</a></li>'
        for d in reversed(all_dates)
    )
    nav = f"""
    <details style="margin-bottom:16px;">
      <summary style="cursor:pointer;color:#2563eb;">날짜별 아카이브 ({len(all_dates)}일)</summary>
      <ul>{archive_links}</ul>
    </details>"""

    body = render_article_list(articles, include_feedback=True)
    feedback_script = render_feedback_script(FORM_SUBMIT_URL, FORM_ENTRY_ARTICLE_ID, FORM_ENTRY_VOTE)

    html_out = _page(
        title="반도체 뉴스 판단 에이전트",
        date_label=f"최신: {latest} · 총 {len(articles)}건 · 확신 낮음 {low_count}건",
        body=body,
        nav=nav,
        feedback_script=feedback_script,
    )

    SITE_DIR.mkdir(parents=True, exist_ok=True)
    (SITE_DIR / "index.html").write_text(html_out, encoding="utf-8")


def main():
    all_dates = load_all_dates()
    if not all_dates:
        print("data/{날짜}.json 이 없습니다.")
        return

    for date in all_dates:
        build_archive_page(date, all_dates)
    build_index_page(all_dates)

    print(f"[build_site] {len(all_dates)}개 날짜 → site/index.html + site/archive/*.html 생성 완료")


if __name__ == "__main__":
    main()
