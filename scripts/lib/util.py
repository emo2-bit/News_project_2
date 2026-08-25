"""공통 유틸: HTML 제거, 발행일 정규화, 본문 길이 제한."""

import re
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

KST = timezone(timedelta(hours=9))


def strip_html(text: str | None) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]*>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_published_at(pub_date: str | None) -> str:
    """RSS pubDate를 KST(+09:00) ISO8601로 정규화한다.
    파싱 실패 시 현재 시각(KST)을 대신 사용한다.
    """
    if pub_date:
        try:
            dt = parsedate_to_datetime(pub_date)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=KST)
            return dt.astimezone(KST).isoformat()
        except (TypeError, ValueError):
            pass
    return datetime.now(KST).isoformat()


def truncate(text: str, max_length: int = 300) -> str:
    """AI 판단 시 입력 길이를 통제하기 위해 본문을 고정 길이로 자른다."""
    if len(text) <= max_length:
        return text
    return text[:max_length].strip() + "…"
