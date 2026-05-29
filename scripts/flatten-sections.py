#!/usr/bin/env python3
"""Move sections/*.md to chapter root (sibling of notes.md)."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BOOKS = [
    "Docker-Up-and-Running",
    "Kubernetes-Up-and-Running",
    "Learning-GitHub-Actions",
]


def flatten_chapter(chapter_dir: Path) -> int:
    sections = chapter_dir / "sections"
    if not sections.is_dir():
        return 0

    moved = 0
    for f in sorted(sections.glob("*.md")):
        dest = chapter_dir / f.name
        if dest.exists():
            dest.unlink()
        shutil.move(str(f), str(dest))
        moved += 1

    shutil.rmtree(sections)

    readme = chapter_dir / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        text = text.replace("](sections/", "](")
        text = text.replace("`sections/`", "本章目录下对应小节文件")
        text = text.replace("对应 `sections/` 文件", "对应小节 `.md` 文件")
        readme.write_text(text, encoding="utf-8")

    notes = chapter_dir / "notes.md"
    if notes.exists():
        title = "章节"
        m = re.search(r"^# (.+)$", notes.read_text(encoding="utf-8"), re.M)
        if m:
            title = m.group(1)
        notes.write_text(
            f"# {title}\n\n"
            f"本章各小节笔记与本文件**同级**，见 [README.md](README.md) 中的链接。\n",
            encoding="utf-8",
        )

    return moved


def update_book_readme(book: Path) -> None:
    readme = book / "README.md"
    if not readme.exists():
        return
    text = readme.read_text(encoding="utf-8")
    text = text.replace("sections/", "")
    text = text.replace(
        "  sections/\n    4.1-命名空间.md\n    4.2-上下文.md\n    ...",
        "  4.1-命名空间.md\n  4.2-上下文.md\n  ...",
    )
    text = text.replace(
        "  sections/\n    4.1-在存储库中创建第一个工作流.md\n    ...",
        "  4.1-在存储库中创建第一个工作流.md\n  ...",
    )
    text = text.replace(
        "```\nchapter-04-kubectl/\n  README.md       ← 章索引\n  notes.md        ← 跳转说明\n  4.1-命名空间.md",
        "```\nchapter-04-kubectl/\n  README.md       ← 章索引\n  notes.md        ← 跳转说明\n  4.1-命名空间.md",
    )
    # Fix docker readme block
    old = """```
chapter-08-docker-compose/
  README.md          ← 章索引（链到各小节）
  notes.md           ← 跳转说明
  sections/
    8.1-配置docker-compose.md
    8.2-启动服务.md
    ...
```"""
    new = """```
chapter-08-docker-compose/
  README.md
  notes.md
  8.1-配置docker-compose.md
  8.2-启动服务.md
  ...
```"""
    text = text.replace(old, new)
    text = text.replace("只改对应 `sections/` 文件", "只改对应小节 `.md` 文件")
    text = text.replace("见 [`sections/`](sections/)", "见 [README.md](README.md)")
    readme.write_text(text, encoding="utf-8")


def main() -> None:
    total = 0
    for book_name in BOOKS:
        book = ROOT / book_name
        for chapter in sorted(book.glob("chapter-*")):
            n = flatten_chapter(chapter)
            if n:
                print(f"  {chapter.relative_to(ROOT)}: {n} files")
                total += n
        update_book_readme(book)
        print(f"OK {book_name}")
    print(f"Done: {total} section files flattened")


if __name__ == "__main__":
    main()
