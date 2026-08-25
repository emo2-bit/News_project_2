"""제목 유사도 기반 중복 제거.

서로 다른 매체가 같은 사건을 보도한 경우, 제목 유사도(문자 bigram Jaccard)로
감지해서 먼저 수집된 쪽만 남기고 나머지는 제외한다. AI 판단 전에 걸러서
같은 뉴스를 중복으로 판단하지 않도록 한다.
"""

import re

SIMILARITY_THRESHOLD = 0.4


def _normalize_title(title: str) -> str:
    title = re.sub(r"\[[^\]]*\]", "", title)  # "[ZD브리핑]" 같은 코너명 태그 제거
    title = re.sub(r"[^\w]", "", title, flags=re.UNICODE)  # 공백/문장부호 제거
    return title.lower()


def _bigrams(text: str) -> set[str]:
    return {text[i : i + 2] for i in range(len(text) - 1)}


def _jaccard_similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    return intersection / (len(a) + len(b) - intersection)


def dedupe_by_similar_title(items: list) -> list:
    kept = []
    kept_grams: list[set[str]] = []

    for item in items:
        grams = _bigrams(_normalize_title(item.title))
        is_duplicate = any(
            _jaccard_similarity(existing, grams) >= SIMILARITY_THRESHOLD for existing in kept_grams
        )
        if not is_duplicate:
            kept.append(item)
            kept_grams.append(grams)

    return kept
