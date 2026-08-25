# 반도체 뉴스 판단 에이전트 — 프로젝트 spec

> 이 문서는 Claude Code에게 그대로 전달하는 구현 spec입니다. 각 섹션 하단의 "확정" 항목은
> 그대로 구현하고, "Claude Code가 정할 것"은 구현 중 자유롭게 판단해도 됩니다.
> **진행 원칙: 큰 단계(1~6)마다 완료 후 사용자 승인을 받고 다음 단계로 넘어갈 것.**

---

## 0. 프로젝트 목적 (SK하이닉스 경험기술서 소재)

기존 News_project(별도 프로젝트, 건드리지 않음)와 문제의식은 비슷하지만 완전히 새로 만드는
프로젝트. 핵심 차별점은 **"AI가 모든 판단을 혼자 하지 않고, 불확실성을 스스로 감지해서
사람에게 되묻는 하이브리드 구조"**.

경험기술서 평가 기준(AI 에이전트화를 통한 업무 재정의 / 프로세스 검토 / 문제 상황 대응 /
워크플로우화) 매핑:

| 경험기술서 항목 | 이 프로젝트에서 채울 내용 |
|---|---|
| 워크플로우 설계 | 규칙 기반 1차 필터(명확한 것) + AI 판단(애매한 것) + confidence 낮은 항목만 사람에게 되묻는 3단 구조 설계 |
| 검증 및 개선 | 주간 자기교정 루프(Cowork)가 피드백 데이터를 분석해 판단 기준 개선안을 스스로 제안 → 사람이 검토 후 반영하는 순환 구조 |
| 결과 | (구현 후 채움) 예: "확신 낮음"으로 표시된 항목 중 실제로 피드백이 갈린 비율, 반영 전후 관련도 판단 정확도 변화 등 |

---

## 1. 확정된 아키텍처

### 일일 파이프라인 (로컬, Claude Code Desktop 로컬 스케줄 작업 = Routines)

```
[Windows 자동 기상 + Claude Desktop 자동 실행 + Keep computer awake]
        │
        ▼
1. RSS 수집 (전자신문 / ZDNet Korea / 디일렉)  — 스크립트
2. 규칙 기반 1차 분류 (키워드 필터)             — 스크립트
3. AI 관련도 판단 (Claude Code 세션 자체가 판단자 — 별도 API 호출 아님, Pro 구독 사용량)
   → 기사별로 relevance(0-100) + confidence(high/medium/low) + reason 출력
4. confidence가 낮은 항목 1~2개 표시
5. 결과 발송
   - 이메일: Gmail SMTP, 오늘 요약 + 확신 낮은 항목 강조 + 사이트 링크
   - 웹사이트: 날짜별 아카이브 + 👍/👎 피드백 버튼(Google Form 제출) + 확신 낮은 항목 강조 표시
6. git commit & push → GitHub Actions가 GitHub Pages 배포 (AI 판단 없는 단순 빌드만 하므로
   Actions Secrets에 API 키 불필요)
```

### 주간 자기교정 루프 (Cowork Scheduled Task, 원격 실행 — PC 상태 무관)

```
1. Google Sheets(피드백 응답)를 Google Drive 커넥터로 CSV 읽기
2. 그 주 판단 오류 패턴 분석 (confidence 낮았던 항목 중 실제 반응이 갈린 것들 위주)
3. 판단 기준(프롬프트) 개선안 리포트 생성 → 사람에게 전달
4. 사람이 검토 후, 다음 daily 판단 프롬프트에 반영은 Claude Code에게 별도 요청
```

---

## 2. 확정된 서비스/기술 스택

| 항목 | 선택 | 비고 |
|---|---|---|
| 이메일 발송 | **Gmail SMTP + 앱 비밀번호** | 새 계정/도메인 불필요. 자격 증명은 `.env`에 저장, `.gitignore`에 반드시 포함 |
| 피드백 저장 | **Google Form + Google Sheets** | 무료·무제한. 응답이 시트에 자동 누적됨 |
| 피드백 읽기(주간) | Cowork의 Google Drive 커넥터로 시트를 CSV로 읽기 (읽기 전용, 이번 용도엔 충분) — **사용자가 Cowork에 Google Drive 커넥터를 미리 연결해둬야 함 (Customize → Connectors)** |
| 일일 스케줄 | Claude Code Desktop → Code 탭 → Routines → New routine → Local |
| 주간 스케줄 | Cowork → Scheduled → New task |
| 배포 | GitHub Pages, 로컬에서 git push → GitHub Actions는 단순 빌드만 |
| API 키 | 이번 프로젝트에서 Anthropic Console API 키 사용 안 함 (Claude Code 세션 자체가 판단) |

---

## 3. 데이터 스키마 (일일 판단 결과)

```json
{
  "date": "2026-08-25",
  "articles": [
    {
      "id": "unique-id",
      "title": "...",
      "url": "...",
      "source": "전자신문",
      "category": "articles | announcements | other",
      "relevance": 78,
      "confidence": "high | medium | low",
      "reason": "판단 근거 한 줄"
    }
  ]
}
```

- `confidence`는 relevance 점수와 별개로 AI가 직접 출력 (점수 구간으로 유추하지 않음 —
  판단 자체가 애매했는지를 AI 스스로 판단하게 하는 것이 이 프로젝트의 핵심이므로)
- confidence가 "low"인 항목만 이메일/사이트에서 강조 표시

---

## 4. 피드백 버튼 구현 방식

Google Form의 제출 URL로 백그라운드 POST 요청을 보내 페이지 이동 없이 처리:

```js
fetch("https://docs.google.com/forms/d/e/{FORM_ID}/formResponse", {
  method: "POST",
  mode: "no-cors",
  body: new URLSearchParams({
    "entry.XXXXXXXXX": articleId,
    "entry.YYYYYYYYY": "up" // or "down"
  })
});
```

- Form ID와 entry ID는 Google Form에서 "미리 채워진 링크 받기" 기능으로 확인 (Claude Code가
  Form 생성 가이드까지는 못 하므로, 사용자가 Google Form을 만들고 필드 2개(article_id,
  vote)를 추가한 뒤 entry ID를 Claude Code에게 전달하는 단계가 필요함 — **1단계 착수 전
  사용자 확인 필요**)
- 토큰/키를 클라이언트 코드에 노출하지 않는 방식이므로 정적 사이트에서 안전

---

## 5. git push 자동화 요구사항

- 실행 전 `git diff --quiet`로 변경 사항 없으면 커밋 스킵 (빈 커밋 방지)
- push 전 `git pull --rebase` 로 안전하게 동기화
- 인증은 Git Credential Manager 또는 PAT 캐싱 사용 (사람 개입 없이 인증 창이 뜨지 않도록)
- 로컬 스케줄 작업 폴더는 반드시 Claude Desktop에서 신뢰(trust)된 폴더여야 함

---

## 6. 폴더 구조 제안 (Claude Code가 조정 가능)

```
semiconductor-news-agent/
├── .env                  # Gmail 앱 비밀번호 등 (git 제외)
├── .gitignore
├── scripts/
│   ├── collect.py        # RSS 수집 + 1차 분류
│   ├── send_email.py     # Gmail SMTP 발송
│   └── git_publish.py    # diff 체크 + commit + pull --rebase + push
├── data/
│   └── 2026-08-25.json   # 일일 판단 결과
├── site/                 # GitHub Pages 소스
│   ├── index.html
│   └── archive/
├── .github/workflows/
│   └── deploy.yml        # 단순 빌드/배포만, API 키 불필요
└── CLAUDE.md              # Routines가 실행될 때 참고할 프로젝트 컨텍스트
```

---

## 7. Claude Code가 구현 중 자유롭게 정할 것

- RSS 파싱 라이브러리, 키워드 필터 세부 로직 (News_project 참고 가능)
- 이메일 템플릿 디자인 (간결하게, 확신 낮은 항목 강조)
- 사이트 UI (카드형, 날짜별 아카이브)
- confidence "low" 표시 방식 (배지, 색상 등)

## 8. 착수 전 사용자가 준비해야 할 것 (Claude Code 시작 전 확인)

- [ ] Gmail 2단계 인증 켜고 앱 비밀번호 발급
- [ ] Google Form 생성 (article_id, vote 필드) 후 entry ID 확인
- [ ] Cowork에 Google Drive 커넥터 연결
- [ ] 새 GitHub 저장소 생성
