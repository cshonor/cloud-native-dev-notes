#!/usr/bin/env python3
"""Restore Docker chapter notes.md from git and re-split into section files."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

COMMIT = "0c6b949"
BOOK_NAME = "Docker-Up-and-Running"


def git_show(path: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "show", f"{COMMIT}:{path}"],
            text=True,
            encoding="utf-8",
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return None


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    book = root / BOOK_NAME
    restored = 0
    for chapter in sorted(book.glob("chapter-*")):
        if not chapter.is_dir():
            continue
        rel = f"{BOOK_NAME}/{chapter.name}/notes.md"
        content = git_show(rel)
        if not content or "待补充" in content[:200] and "## " not in content:
            continue
        if len(content) < 200 and "## " not in content:
            continue
        (chapter / "notes.md").write_text(content, encoding="utf-8")
        restored += 1
        print(f"restored {rel}")
    print(f"Restored {restored} notes.md files from {COMMIT}")
    if restored == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
