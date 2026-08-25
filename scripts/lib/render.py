"""기사 카드 HTML 렌더링. 이메일(5단계)과 사이트(5단계)가 함께 재사용한다.

confidence가 "low"인 항목만 시각적으로 강조한다(스펙 3절 확정 사항). 그 외
카테고리 배지, relevance 점수는 부가 정보로 표시한다.

피드백 버튼(👍/👎)은 사이트에만 넣는다 — 이메일 클라이언트는 대부분 JS를 막아서
버튼 클릭이 동작하지 않기 때문이다(include_feedback=False가 기본값).
"""

import html

CATEGORY_LABELS = {"articles": "기사", "announcements": "발표", "other": "기타"}
CATEGORY_COLORS = {
    "articles": "#2563eb",
    "announcements": "#7c3aed",
    "other": "#6b7280",
}

# 사이트 페이지 하단에 한 번만 삽입되는 공용 스크립트.
# Google Form의 formResponse URL로 no-cors POST를 보내 페이지 이동 없이 처리한다(스펙 4절).
FEEDBACK_SCRIPT = """
<script>
function submitVote(articleId, vote, btn) {
  fetch("__FORM_SUBMIT_URL__", {
    method: "POST",
    mode: "no-cors",
    body: new URLSearchParams({
      "__ENTRY_ARTICLE_ID__": articleId,
      "__ENTRY_VOTE__": vote
    })
  });
  var group = btn.parentElement;
  group.querySelectorAll("button").forEach(function (b) { b.disabled = true; b.style.opacity = 0.4; });
  btn.style.opacity = 1;
  btn.insertAdjacentHTML("afterend", '<span style="margin-left:6px;color:#6b7280;font-size:12px;">감사합니다!</span>');
}
</script>
"""


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def render_feedback_script(form_submit_url: str, entry_article_id: str, entry_vote: str) -> str:
    return (
        FEEDBACK_SCRIPT.replace("__FORM_SUBMIT_URL__", form_submit_url)
        .replace("__ENTRY_ARTICLE_ID__", entry_article_id)
        .replace("__ENTRY_VOTE__", entry_vote)
    )


def render_article_card(article: dict, include_feedback: bool = False) -> str:
    is_low = article["confidence"] == "low"
    category = article.get("category", "other")
    cat_label = CATEGORY_LABELS.get(category, category)
    cat_color = CATEGORY_COLORS.get(category, "#6b7280")

    card_style = (
        "border:1px solid #e5e7eb;border-left:4px solid #f59e0b;background:#fffbeb;"
        if is_low
        else "border:1px solid #e5e7eb;border-left:4px solid transparent;background:#ffffff;"
    )

    low_badge = (
        '<span style="display:inline-block;background:#f59e0b;color:#fff;'
        'font-size:12px;font-weight:600;padding:2px 8px;border-radius:999px;'
        'margin-left:8px;">⚠ 확신 낮음</span>'
        if is_low
        else ""
    )

    feedback_html = ""
    if include_feedback:
        article_id = _esc(article["id"])
        feedback_html = f"""
  <div style="margin-top:10px;">
    <button onclick="submitVote('{article_id}','up',this)"
      style="border:1px solid #e5e7eb;background:#fff;border-radius:6px;padding:4px 10px;
      cursor:pointer;font-size:14px;">👍</button>
    <button onclick="submitVote('{article_id}','down',this)"
      style="border:1px solid #e5e7eb;background:#fff;border-radius:6px;padding:4px 10px;
      cursor:pointer;font-size:14px;margin-left:4px;">👎</button>
  </div>"""

    return f"""
<div style="{card_style}border-radius:8px;padding:16px;margin-bottom:12px;">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
    <span style="display:inline-block;background:{cat_color};color:#fff;font-size:12px;
      font-weight:600;padding:2px 8px;border-radius:999px;">{_esc(cat_label)}</span>
    <span style="color:#6b7280;font-size:13px;">{_esc(article['source'])}</span>
    <span style="color:#9ca3af;font-size:13px;">관련도 {article['relevance']}</span>
    {low_badge}
  </div>
  <a href="{_esc(article['url'])}" target="_blank" rel="noopener"
     style="font-size:16px;font-weight:600;color:#111827;text-decoration:none;">
    {_esc(article['title'])}
  </a>
  <div style="color:#6b7280;font-size:13px;margin-top:6px;">{_esc(article['reason'])}</div>{feedback_html}
</div>"""


def render_article_list(articles: list[dict], include_feedback: bool = False) -> str:
    return "\n".join(render_article_card(a, include_feedback=include_feedback) for a in articles)
