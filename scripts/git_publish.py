"""6단계: git commit & push 자동화 (스펙 5절).

- 변경 사항 없으면 커밋 스킵 (빈 커밋 방지)
- push 전 origin/main이 존재하면 pull --rebase로 동기화 (최초 push는 생략)
- 인증은 Git Credential Manager(로컬에 credential.helper=manager 설정됨)에 위임 —
  사람 개입 없이 인증 창이 뜨지 않아야 하므로 별도 프롬프트를 넣지 않는다
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent


def run(*args, check=True):
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 실패:\n{result.stderr}")
    return result


def main():
    run("add", "-A")

    diff = run("diff", "--staged", "--quiet", check=False)
    if diff.returncode == 0:
        print("[git_publish] 변경 사항 없음, 커밋 생략")
        return

    date = datetime.now().strftime("%Y-%m-%d")
    run("commit", "-m", f"chore: {date} 반도체 뉴스 업데이트")

    run("fetch", "origin")
    remote_has_main = run("rev-parse", "--verify", "-q", "origin/main", check=False).returncode == 0
    if remote_has_main:
        run("pull", "--rebase", "origin", "main")

    run("push", "-u", "origin", "main")
    print(f"[git_publish] {date} 변경 사항 커밋 & push 완료")


if __name__ == "__main__":
    main()
