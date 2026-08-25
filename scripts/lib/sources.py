"""RSS 소스 정의 및 수집."""

from dataclasses import dataclass, field

import feedparser

from .util import normalize_published_at, strip_html, truncate


@dataclass
class RawItem:
    title: str
    url: str
    source: str
    published_at: str
    description: str = ""


@dataclass
class SourceStat:
    source: str
    fetched: int
    kept_after_filter: int
    error: str | None = None


SOURCES = [
    {"name": "전자신문", "url": "https://rss.etnews.com/Section901.xml"},
    # ZDNet Korea는 반도체 전용 섹션 RSS가 더 이상 제공되지 않아 전체기사 피드를
    # 받아 키워드로 필터링한다.
    {"name": "ZDNet Korea", "url": "https://zdnet.co.kr/feed"},
    {"name": "디일렉", "url": "https://www.thelec.kr/rss/allArticle.xml"},
    {"name": "IT조선", "url": "https://it.chosun.com/rss/allArticle.xml"},
    {"name": "아이뉴스24", "url": "https://rss.inews24.com/rss/news_it.xml"},
    {"name": "블로터", "url": "https://www.bloter.net/rss/allArticle.xml"},
    {"name": "테크M", "url": "https://www.techm.kr/rss/allArticle.xml"},
    # 한국경제는 "산업" 전용 RSS가 없어 가장 근접한 IT·과학 카테고리를 사용한다.
    {"name": "한국경제", "url": "https://www.hankyung.com/feed/it"},
    {"name": "EBN", "url": "https://www.ebn.co.kr/rss/allArticle.xml"},
]

# 일부 매체(한국경제 등)는 기본 User-Agent가 없는 요청을 차단(403)한다.
_REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def fetch_source(name: str, url: str) -> list[RawItem]:
    feed = feedparser.parse(url, request_headers=_REQUEST_HEADERS)
    if feed.bozo and not feed.entries:
        raise RuntimeError(str(feed.bozo_exception))

    items = []
    for entry in feed.entries:
        description = entry.get("summary") or entry.get("description") or ""
        items.append(
            RawItem(
                title=strip_html(entry.get("title", "")),
                url=entry.get("link", ""),
                source=name,
                published_at=normalize_published_at(entry.get("published")),
                description=truncate(strip_html(description)),
            )
        )
    return items
