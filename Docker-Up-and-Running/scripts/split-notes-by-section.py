#!/usr/bin/env python3
"""Split chapter notes.md into one file per book subsection."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# chapter_dir -> list of (section_id, slug, ## heading prefix to match)
# heading match: section content starts with line "## {heading}"
CHAPTER_MAP: dict[str, list[tuple[str, str, str]]] = {
    "chapter-01-introduction": [
        ("1.1", "docker带来的希望", "Docker 的诞生"),
        ("1.2", "希望", "Docker 带来的希望"),
        ("1.3", "docker式工作流程", "Docker 式工作流程的好处"),
        ("1.4", "docker不是什么", "Docker 不是什么"),
    ],
    "chapter-02-docker-landscape": [
        ("2.1", "简化流程", "简化业务流程"),
        ("2.2", "广泛支持和采用", "广泛支持和采用"),
        ("2.3", "架构", "架构"),
        ("2.4", "合理利用docker", "充分理解 Docker"),
        ("2.5", "docker工作流程", "Docker 式工作流程"),
        ("2.6", "小结", "__merge_ecosystem_summary__"),
    ],
    "chapter-03-installing-docker": [
        ("3.1", "重要术语", "重要的术语"),
        ("3.2", "安装客户端", "安装 Docker 客户端"),
        ("3.3", "安装服务器", "安装 Docker 服务器"),
        ("3.4", "测试安装", "测试安装的 Docker"),
        ("3.5", "小结", "小结"),
    ],
    "chapter-04-docker-images": [
        ("4.1", "dockerfile剖析", "剖析 Dockerfile 文件"),
        ("4.2", "构建映像", "构建映像"),
        ("4.3", "运行映像", "运行映像"),
        ("4.4", "定制基础映像", "定制基础映像"),
        ("4.5", "存储映像", "存储映像"),
        ("4.6", "优化映像", None),
        ("4.7", "诊断构建", None),
        ("4.8", "多架构构建", None),
        ("4.9", "小结", "本章速记"),
    ],
    "chapter-05-containers": [
        ("5.1", "容器是什么", "容器是什么"),
        ("5.2", "创建容器", "创建容器"),
        ("5.3", "启动容器", "启动容器"),
        ("5.4", "自动重启", "自动重启容器"),
        ("5.5", "停止容器", "停止容器"),
        ("5.6", "清除容器", "清除容器"),
        ("5.7", "暂停和恢复", "暂停和恢复容器"),
        ("5.8", "清理容器和映像", "清理容器和映像"),
        ("5.9", "windows容器", None),
        ("5.10", "小结", "接下来"),
    ],
    "chapter-06-exploring-docker": [
        ("6.1", "打印版本号", "打印 Docker 的版本号"),
        ("6.2", "服务器信息", "服务器信息"),
        ("6.3", "下载映像更新", "下载映像的更新"),
        ("6.4", "审查容器", "审查容器"),
        ("6.5", "shell中探索", "在 shell 中探索"),
        ("6.6", "返回结果", "返回结果"),
        ("6.7", "进入容器", "进入运行中的容器"),
        ("6.8", "处理日志", "Docker 的日志"),
        ("6.9", "监控docker", "监控 Docker"),
        ("6.10", "prometheus", None),
        ("6.11", "继续探索", None),
        ("6.12", "小结", "小结"),
    ],
    "chapter-07-debugging": [
        ("7.1", "列出进程", "列出进程"),
        ("7.2", "审查进程", "检查进程"),
        ("7.3", "管控进程", "管理进程"),
        ("7.4", "审查网络", "检查网络"),
        ("7.5", "映像历史", "查看映像的历史"),
        ("7.6", "审查容器", "检查容器"),
        ("7.7", "审查文件系统", "检查文件系统"),
        ("7.8", "小结", "接下来"),
    ],
    "chapter-08-docker-compose": [
        ("8.1", "配置docker-compose", "8.1 配置 Docker Compose"),
        ("8.2", "启动服务", "8.2 启动服务"),
        ("8.3", "探索rocketchat", "8.3 探索 Rocket.Chat"),
        ("8.4", "compose命令", "8.4 Docker Compose 命令"),
        ("8.5.1", "默认值", "8.5 管理配置"),
        ("8.6", "小结", "8.6 小结"),
    ],
    "chapter-09-path-to-production": [
        ("9.1", "部署", "部署"),
        ("9.2", "测试容器", "测试容器"),
        ("9.3", "外部依赖", "外部依赖"),
        ("9.4", "小结", "本章速记"),
    ],
    "chapter-10-docker-at-scale": [
        ("10.1", "docker-swarm", "Docker Swarm"),
        ("10.2", "kubernetes", None),
        ("10.3", "ecs-fargate", "Amazon EC2 Container Service (ECS)"),
        ("10.4", "小结", "小结"),
    ],
    "chapter-11-advanced-topics": [
        ("11.1", "容器详解", "容器详解"),
        ("11.2", "安全性", "安全性"),
        ("11.3", "配置", None),
        ("11.4", "存储", "可更换的后端"),
        ("11.5", "nsenter", None),
        ("11.6", "docker结构", None),
        ("11.7", "替换运行时", None),
        ("11.8", "小结", "网络"),
    ],
}


def parse_sections(text: str) -> dict[str, str]:
    """Return {heading_without_##: body}"""
    parts = re.split(r"\n(?=## )", text)
    preamble = parts[0]
    sections: dict[str, str] = {"__preamble__": preamble}
    for part in parts[1:]:
        if not part.startswith("## "):
            continue
        first_line, _, body = part.partition("\n")
        heading = first_line[3:].strip()
        sections[heading] = body.strip()
    return sections


def split_8_5(content: str) -> dict[str, str]:
    """Split 8.5 into 8.5.1, 8.5.2, 8.5.3."""
    out: dict[str, str] = {}
    intro, _, rest = content.partition("### 8.5.1 默认值")
    if rest:
        p1, _, rest2 = rest.partition("### 8.5.2 强制值")
        p2, _, p3 = rest2.partition("### 8.5.3 dotenv 文件（.env）")
        out["8.5-intro"] = intro.strip()
        out["8.5.1"] = p1.strip()
        out["8.5.2"] = p2.strip()
        out["8.5.3"] = p3.strip()
    else:
        out["8.5-full"] = content
    return out


def chapter_title_from_preamble(preamble: str) -> str:
    m = re.search(r"^# (.+)$", preamble, re.M)
    return m.group(1) if m else "章节"


def hint_from_preamble(preamble: str) -> str:
    hints = re.findall(r"^> .+$", preamble, re.M)
    return "\n".join(hints)


def write_section(path: Path, section_id: str, title: str, hint: str, body: str) -> None:
    lines = [f"# {section_id} {title}", ""]
    if hint:
        lines.append(hint)
        lines.append("")
    lines.append(body.strip())
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def build_chapter_readme(chapter_dir: Path, chapter_title: str, hint: str, entries: list[tuple[str, str, str]]) -> None:
    lines = [
        f"# {chapter_title}",
        "",
    ]
    if hint:
        lines.append(hint)
        lines.append("")
    lines.append("## 小节笔记（一书一小节一文件）")
    lines.append("")
    lines.append("| 小节 | 文件 |")
    lines.append("|------|------|")
    for sid, slug, title in entries:
        fname = f"{sid}-{slug}.md"
        lines.append(f"| {sid} | [{title}]({fname}) |")
    lines.append("")
    lines.append("> 你粘贴某小节原文后，在对应文件中增补即可。")
    lines.append("")
    path = chapter_dir / "README.md"
    path.write_text("\n".join(lines), encoding="utf-8")


def process_chapter(chapter_name: str, mapping: list[tuple[str, str, str]]) -> None:
    chapter_dir = ROOT / chapter_name
    notes_path = chapter_dir / "notes.md"
    if not notes_path.exists():
        return

    text = notes_path.read_text(encoding="utf-8")
    parsed = parse_sections(text)
    preamble = parsed.get("__preamble__", "")
    chapter_title = chapter_title_from_preamble(preamble)
    hint = hint_from_preamble(preamble)

    out_dir = chapter_dir
    for f in out_dir.glob("[0-9]*.md"):
        f.unlink()

    entries: list[tuple[str, str, str]] = []
    used_headings: set[str] = set()

    for section_id, slug, heading_key in mapping:
        if heading_key is None or heading_key.startswith("__"):
            title = slug.replace("-", " ")
            body = "* **待补充**\n  * > 请粘贴该小节原文，我将按统一格式拆解。"
            fname = f"{section_id}-{slug}.md"
            write_section(out_dir / fname, section_id, title, hint, body)
            entries.append((section_id, slug, title))
            continue
        if heading_key not in parsed:
            # placeholder
            title = slug.replace("-", " ")
            body = "* **待补充**\n  * > 请粘贴该小节原文，我将按统一格式拆解。"
            fname = f"{section_id}-{slug}.md"
            write_section(out_dir / fname, section_id, title, hint, body)
            entries.append((section_id, slug, title))
            continue

        if heading_key in used_headings:
            continue
        used_headings.add(heading_key)
        body = parsed[heading_key]

        # Special: chapter 8 section 8.5 split
        if chapter_name == "chapter-08-docker-compose" and section_id == "8.5.1":
            parts = split_8_5(body)
            if "8.5-intro" in parts:
                intro = parts.get("8.5-intro", "")
                for sid, sslug, stitle, key in [
                    ("8.5.1", "默认值", "默认值", "8.5.1"),
                    ("8.5.2", "强制值", "强制值", "8.5.2"),
                    ("8.5.3", "dotenv文件", "dotenv 文件", "8.5.3"),
                ]:
                    chunk = parts.get(key, "")
                    full_body = (intro + "\n\n" + chunk).strip() if sid == "8.5.1" else chunk
                    fname = f"{sid}-{sslug}.md"
                    write_section(out_dir / fname, sid, stitle, hint, full_body)
                    entries.append((sid, sslug, stitle))
            else:
                fname = f"{section_id}-{slug}.md"
                write_section(out_dir / fname, section_id, "管理配置", hint, body)
                entries.append((section_id, slug, "管理配置"))
            continue

        if chapter_name == "chapter-08-docker-compose" and section_id.startswith("8.5.") and section_id != "8.5.1":
            continue

        if heading_key == "__merge_ecosystem_summary__":
            eco = parsed.get("Docker 的生态系统", "")
            summ = parsed.get("小结", "")
            body = (eco + "\n\n" + summ).strip()
            title = "小结"
            fname = f"{section_id}-{slug}.md"
            write_section(out_dir / fname, section_id, title, hint, body)
            entries.append((section_id, slug, title))
            continue

        if chapter_name == "chapter-10-docker-at-scale" and section_id == "10.1":
            extra = parsed.get("章节核心主旨与背景", "")
            centurion = parsed.get("Centurion", "")
            if extra:
                body = extra + "\n\n---\n\n" + body
            if centurion:
                body += "\n\n---\n\n## 附录：Centurion（旧版笔记）\n\n" + centurion

        title = heading_key.replace("8.1 ", "").replace("8.2 ", "").replace("8.3 ", "").replace("8.4 ", "").replace("8.6 ", "")
        fname = f"{section_id}-{slug}.md"
        write_section(out_dir / fname, section_id, title, hint, body)
        entries.append((section_id, slug, title))

    # Append 本章速记 to last section if exists
    if "本章速记" in parsed and chapter_name != "chapter-08-docker-compose":
        last = entries[-1]
        last_file = out_dir / f"{last[0]}-{last[1]}.md"
        if last_file.exists():
            content = last_file.read_text(encoding="utf-8")
            if "本章速记" not in content:
                last_file.write_text(
                    content.rstrip() + "\n\n## 本章速记\n\n" + parsed["本章速记"] + "\n",
                    encoding="utf-8",
                )

    # ch08: merge 本章速记 into 8.6
    if chapter_name == "chapter-08-docker-compose" and "本章速记" in parsed:
        f86 = out_dir / "8.6-小结.md"
        if f86.exists():
            content = f86.read_text(encoding="utf-8")
            if "本章速记" not in content:
                f86.write_text(
                    content.rstrip() + "\n\n## 本章速记\n\n" + parsed["本章速记"] + "\n",
                    encoding="utf-8",
                )

    # ch07: merge 本章速记 into 7.8
    if chapter_name == "chapter-07-debugging" and "本章速记" in parsed:
        f78 = out_dir / "7.8-小结.md"
        if f78.exists():
            content = f78.read_text(encoding="utf-8")
            extra = parsed.get("接下来", "")
            sk = parsed["本章速记"]
            block = ""
            if extra:
                block += f"\n\n## 过渡\n\n{extra}\n"
            block += f"\n\n## 本章速记\n\n{sk}\n"
            f78.write_text(content.rstrip() + block, encoding="utf-8")

    build_chapter_readme(chapter_dir, chapter_title, hint, entries)

    # Replace notes.md with pointer
    notes_path.write_text(
        f"# {chapter_title}\n\n"
        f"本章已拆分为 **{len(entries)}** 个小节文件，见 [README.md](README.md)。\n",
        encoding="utf-8",
    )


def main() -> None:
    for chapter, mapping in CHAPTER_MAP.items():
        process_chapter(chapter, mapping)
        print(f"OK {chapter} -> {len(mapping)} sections")


if __name__ == "__main__":
    main()
