"""github 소스 플러그인마다 ref가 가리키는 커밋을 sha로 고정한다.

claude.ai의 "Sync automatically"는 이 저장소의 기본 브랜치에 push가 있을 때만 동기화하므로,
플러그인 저장소가 바뀌면 이 저장소에 sha 변경 커밋이 생겨야 claude.ai가 새 버전을 받는다.
workflow가 의존성 설치 없이 python3로 실행하므로 표준 라이브러리만 쓴다.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable

SHA = re.compile(r"[0-9a-f]{40}")


def ls_remote(repo: str, ref: str | None) -> str:
    url = f"https://github.com/{repo}"
    patterns = ["HEAD"] if ref is None else [f"refs/heads/{ref}", f"refs/tags/{ref}^{{}}", f"refs/tags/{ref}"]
    out = subprocess.run(["git", "ls-remote", url, *patterns], check=True, capture_output=True, text=True).stdout
    found = dict(reversed(line.split("\t", 1)) for line in out.splitlines() if "\t" in line)
    for pattern in patterns:
        if pattern in found and SHA.fullmatch(found[pattern]):
            return found[pattern]
    raise LookupError(f"{repo}: ref {ref or 'HEAD'} not found")


def pin(marketplace: dict, resolve: Callable[[str, str | None], str]) -> list[str]:
    changes = []
    for entry in marketplace.get("plugins", []):
        source = entry.get("source")
        if not isinstance(source, dict) or source.get("source") != "github":
            continue
        sha = resolve(source["repo"], source.get("ref"))
        if source.get("sha") != sha:
            changes.append(f"{entry['name']} {source.get('sha', 'none')[:12]} -> {sha[:12]}")
            source["sha"] = sha
    return changes


def main(argv: list[str] | None = None, resolve: Callable[[str, str | None], str] = ls_remote) -> int:
    p = argparse.ArgumentParser(description="marketplace.json의 github 소스를 ref의 최신 커밋 sha로 고정", allow_abbrev=False)
    p.add_argument("path", nargs="?", default=str(Path(__file__).resolve().parent.parent / ".claude-plugin" / "marketplace.json"))
    args = p.parse_args(argv)
    path = Path(args.path)
    data = json.loads(path.read_text(encoding="utf-8"))
    try:
        changes = pin(data, resolve)
    except (LookupError, subprocess.CalledProcessError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if changes:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for line in changes:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
