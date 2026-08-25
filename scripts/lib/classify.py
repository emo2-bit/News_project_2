"""규칙 기반 카테고리 분류: articles(기사) | announcements(회사 발표) | other(기타)."""

from urllib.parse import urlparse

# 기업 뉴스룸 도메인은 "회사 발표"로 분류
COMPANY_NEWSROOM_DOMAINS = ["news.samsung.com", "news.skhynix.com"]

OTHER_KEYWORDS = ["채용", "공고", "모집", "컨퍼런스", "세미나", "박람회", "전시회"]


def classify_item(raw) -> str:
    try:
        domain = urlparse(raw.url).hostname or ""
    except ValueError:
        domain = ""

    if any(d in domain for d in COMPANY_NEWSROOM_DOMAINS):
        return "announcements"

    text = f"{raw.title} {raw.description}"
    if any(keyword in text for keyword in OTHER_KEYWORDS):
        return "other"

    return "articles"
