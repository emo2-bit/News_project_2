"""1~2단계: RSS 수집 + 규칙 기반 1차 분류.

세 매체(전자신문/ZDNet Korea/디일렉)의 RSS를 수집하고, 키워드 필터로 반도체
관련 기사만 남긴 뒤 제목 유사도로 중복을 제거하고 카테고리를 분류한다.
결과는 data/candidates/{date}.json에 저장된다.

이 시점까지는 AI 판단이 개입하지 않는다 (relevance/confidence/reason 없음).
다음 단계(3단계, AI 관련도 판단)에서 Claude Code 세션이 이 후보 목록을 읽어
최종 data/{date}.json을 만든다.
"""

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from lib.classify import classify_item
from lib.dedupe import dedupe_by_similar_title
from lib.keywords import is_semiconductor_related
from lib.sources import SOURCES, SourceStat, fetch_source
from lib.util import KST

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "data" / "candidates"


def make_id(url: str) -> str:
    return hashlib.md5(url.encode("utf-8")).hexdigest()[:10]


def collect_all():
    filtered_by_source = []
    source_stats: list[SourceStat] = []

    for source in SOURCES:
        try:
            raw_items = fetch_source(source["name"], source["url"])
        except Exception as exc:  # noqa: BLE001 - 소스 하나 실패해도 나머지는 계속 진행
            source_stats.append(SourceStat(source=source["name"], fetched=0, kept_after_filter=0, error=str(exc)))
            filtered_by_source.append([])
            continue

        filtered = [
            item for item in raw_items if is_semiconductor_related(f"{item.title} {item.description}")
        ]
        source_stats.append(
            SourceStat(source=source["name"], fetched=len(raw_items), kept_after_filter=len(filtered), error=None)
        )
        filtered_by_source.append(filtered)

    merged = [item for group in filtered_by_source for item in group]
    deduped = dedupe_by_similar_title(merged)
    deduped_count = len(merged) - len(deduped)

    candidates = []
    for item in deduped:
        candidates.append(
            {
                "id": make_id(item.url),
                "title": item.title,
                "url": item.url,
                "source": item.source,
                "published_at": item.published_at,
                "description": item.description,
                "category": classify_item(item),
            }
        )

    return candidates, source_stats, deduped_count


def main():
    today = datetime.now(KST).strftime("%Y-%m-%d")
    candidates, source_stats, deduped_count = collect_all()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{today}.json"
    output_path.write_text(
        json.dumps(
            {
                "date": today,
                "candidates": candidates,
                "source_stats": [vars(s) for s in source_stats],
                "deduped_count": deduped_count,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"[collect] {today} 수집 완료 → {output_path}")
    for stat in source_stats:
        status = f"error: {stat.error}" if stat.error else f"{stat.fetched}건 → 필터 후 {stat.kept_after_filter}건"
        print(f"  - {stat.source}: {status}")
    print(f"  - 중복 제거: {deduped_count}건")
    print(f"  - 최종 후보: {len(candidates)}건 (AI 판단 대기)")

    if not candidates and any(s.error for s in source_stats):
        sys.exit(1)


if __name__ == "__main__":
    main()
