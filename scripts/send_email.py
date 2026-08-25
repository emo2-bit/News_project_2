"""5단계: Gmail SMTP로 일일 요약 이메일 발송.

data/{날짜}.report.html(3단계 판단 결과를 종합해 사람이 작성한 리포트 — 리포트
작성 방법은 CLAUDE.md 참고)을 읽어 이메일 본문으로 감싸고, 사이트 링크와 함께
발송한다. 자격증명은 .env(GMAIL_ADDRESS, GMAIL_APP_PASSWORD, EMAIL_TO)에서 읽는다.
"""

import json
import os
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.config import SITE_BASE_URL

ROOT = Path(__file__).resolve().parent.parent


def build_email_html(date: str, report_body: str, total: int, low_count: int) -> str:
    site_url = f"{SITE_BASE_URL}/archive/{date}.html"

    return f"""<!DOCTYPE html>
<html lang="ko">
<body style="font-family:-apple-system,'Malgun Gothic',sans-serif;background:#f3f4f6;margin:0;padding:24px;">
  <div style="max-width:640px;margin:0 auto;background:#fff;border-radius:8px;padding:24px;">
    <h1 style="font-size:18px;margin-bottom:4px;">반도체 뉴스 리포트 — {date}</h1>
    <p style="color:#6b7280;font-size:13px;margin-top:0;margin-bottom:20px;">
      수집 {total}건 · 확신 낮음 {low_count}건 ·
      <a href="{site_url}" style="color:#2563eb;">사이트에서 전체 기사 보기 (피드백 가능)</a>
    </p>
    {report_body}
  </div>
</body>
</html>"""


def send_email(date: str, dry_run: bool = True) -> None:
    load_dotenv(ROOT / ".env")
    gmail_address = os.environ["GMAIL_ADDRESS"]
    gmail_app_password = os.environ["GMAIL_APP_PASSWORD"]
    email_to = os.environ["EMAIL_TO"]

    report_path = ROOT / "data" / f"{date}.report.html"
    if not report_path.exists():
        print(
            f"[send_email] {report_path} 가 없습니다. "
            "먼저 data/{date}.json을 바탕으로 리포트를 작성해주세요 (CLAUDE.md 5단계 참고)."
        )
        return

    data = json.loads((ROOT / "data" / f"{date}.json").read_text(encoding="utf-8"))
    articles = data["articles"]
    low_count = sum(1 for a in articles if a["confidence"] == "low")
    report_body = report_path.read_text(encoding="utf-8")

    html_body = build_email_html(date, report_body, len(articles), low_count)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[반도체 뉴스] {date} 리포트"
    msg["From"] = gmail_address
    msg["To"] = email_to
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    if dry_run:
        out_path = ROOT / "data" / f"{date}.email-preview.html"
        out_path.write_text(html_body, encoding="utf-8")
        print(f"[send_email] DRY RUN — 실제 발송 안 함. 미리보기: {out_path}")
        print(f"  제목: {msg['Subject']}")
        print(f"  받는 사람: {email_to}")
        return

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_address, gmail_app_password)
        server.sendmail(gmail_address, [email_to], msg.as_string())

    print(f"[send_email] {email_to} 로 발송 완료 (총 {len(articles)}건, 확신 낮음 {low_count}건)")


def main():
    date = None
    dry_run = True
    for arg in sys.argv[1:]:
        if arg == "--send":
            dry_run = False
        else:
            date = arg

    if not date:
        candidates = sorted((ROOT / "data").glob("????-??-??.json"))
        if not candidates:
            print("data/{날짜}.json 이 없습니다.")
            return
        date = candidates[-1].stem

    send_email(date, dry_run=dry_run)


if __name__ == "__main__":
    main()
