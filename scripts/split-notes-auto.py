#!/usr/bin/env python3
"""Split chapter notes.md into sections/{id}-{slug}.md (one file per ## heading)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

PLACEHOLDER = "* **待补充**\n  * > 请粘贴该小节原文，我将按统一格式拆解。\n"

SUMMARY_HEADINGS = {"总结", "小结", "本章速记", "Summary", "Conclusion", "结论"}
SKIP_AS_OWN_FILE = {"本章速记"}


def chapter_num(dirname: str) -> int:
    m = re.match(r"chapter-(\d+)", dirname)
    return int(m.group(1)) if m else 0


def parse_sections(text: str) -> tuple[str, str, list[tuple[str, str]]]:
    parts = re.split(r"\n(?=## )", text)
    preamble = parts[0]
    sections: list[tuple[str, str]] = []
    for part in parts[1:]:
        if not part.startswith("## "):
            continue
        line, _, body = part.partition("\n")
        heading = line[3:].strip()
        sections.append((heading, body.strip()))
    return preamble, text, sections


def chapter_title(preamble: str) -> str:
    m = re.search(r"^# (.+)$", preamble, re.M)
    return m.group(1) if m else "章节"


def chapter_hint(preamble: str) -> str:
    return "\n".join(re.findall(r"^> .+$", preamble, re.M))


def make_slug(heading: str) -> str:
    h = re.sub(r"^\d+\.\d+(?:\.\d+)?\s*", "", heading)
    h = h.split("(")[0].strip()
    h = re.sub(r"⏭️.*", "", h).strip()
    slug = re.sub(r"[\s/\\:?*\"<>|,.]+", "-", h)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return (slug[:48] if slug else "section").lower()


def section_id(heading: str, ch: int, idx: int) -> str:
    m = re.match(r"^(\d+\.\d+(?:\.\d+)?)\s", heading)
    if m:
        return m.group(1)
    return f"{ch}.{idx}"


def display_title(heading: str) -> str:
    h = re.sub(r"^\d+\.\d+(?:\.\d+)?\s*", "", heading)
    return h.split("⏭️")[0].strip()


def write_section(path: Path, sid: str, title: str, hint: str, body: str) -> None:
    lines = [f"# {sid} {title}", ""]
    if hint:
        lines.extend([hint, ""])
    lines.append(body.strip())
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def build_readme(chapter_dir: Path, title: str, hint: str, entries: list[tuple[str, str, str]]) -> None:
    lines = [f"# {title}", ""]
    if hint:
        lines.extend([hint, ""])
    lines.append("## 小节笔记（一书一小节一文件）")
    lines.append("")
    lines.append("| 小节 | 文件 |")
    lines.append("|------|------|")
    for sid, slug, stitle in entries:
        fname = f"{sid}-{slug}.md"
        lines.append(f"| {sid} | [{stitle}](sections/{fname}) |")
    lines.append("")
    lines.append("> 粘贴某小节原文后，只改对应 `sections/` 文件。")
    lines.append("")
    (chapter_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def process_chapter(chapter_dir: Path) -> int:
    notes = chapter_dir / "notes.md"
    if not notes.exists():
        return 0

    preamble, _, raw_sections = parse_sections(notes.read_text(encoding="utf-8"))
    title = chapter_title(preamble)
    hint = chapter_hint(preamble)
    ch = chapter_num(chapter_dir.name)

    # peel off 本章速记
    cheji = ""
    content_sections: list[tuple[str, str]] = []
    for h, b in raw_sections:
        bare = h.split("(")[0].strip()
        if bare in SKIP_AS_OWN_FILE or h.startswith("本章速记"):
            cheji = b
            continue
        content_sections.append((h, b))

    sections_dir = chapter_dir / "sections"
    sections_dir.mkdir(exist_ok=True)
    for f in sections_dir.glob("*.md"):
        f.unlink()

    entries: list[tuple[str, str, str]] = []
    idx = 0
    for heading, body in content_sections:
        idx += 1
        sid = section_id(heading, ch, idx)
        slug = make_slug(heading)
        stitle = display_title(heading)
        fname = f"{sid}-{slug}.md"
        write_section(sections_dir / fname, sid, stitle, hint, body)
        entries.append((sid, slug, stitle))

    if entries and cheji:
        last_path = sections_dir / f"{entries[-1][0]}-{entries[-1][1]}.md"
        text = last_path.read_text(encoding="utf-8")
        if "本章速记" not in text:
            last_path.write_text(text.rstrip() + f"\n\n## 本章速记\n\n{cheji}\n", encoding="utf-8")

    build_readme(chapter_dir, title, hint, entries)

    notes.write_text(
        f"# {title}\n\n"
        f"本章已拆分为 **{len(entries)}** 个小节，见 [README.md](README.md) / [sections/](sections/)。\n",
        encoding="utf-8",
    )
    return len(entries)


def process_book(book_root: Path) -> None:
    total = 0
    chapters = 0
    for chapter_dir in sorted(book_root.glob("chapter-*")):
        if not chapter_dir.is_dir():
            continue
        n = process_chapter(chapter_dir)
        if n:
            chapters += 1
            total += n
            print(f"  {chapter_dir.name}: {n} sections")
    print(f"OK {book_root.name}: {chapters} chapters, {total} section files")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    books = [Path(p) for p in sys.argv[1:]] if len(sys.argv) > 1 else []
    if not books:
        print("Usage: split-notes-auto.py <book-dir> ...")
        sys.exit(1)
    for book in books:
        path = book if book.is_absolute() else root / book
        process_book(path)


if __name__ == "__main__":
    main()
