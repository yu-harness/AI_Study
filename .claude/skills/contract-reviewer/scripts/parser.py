"""
合同文件解析器 — Word (.docx) → Markdown 转换工具

用法：
    python parser.py <合同文件路径.docx>

输出：
    转换后的 Markdown 文本（输出到 stdout，Claude 通过 Bash 工具读取）

依赖：
    pip install python-docx

支持格式：
    - .docx (Word 2007+)
    - 段落、标题、加粗、列表等基本格式转换
    - 表格 → Markdown 表格
"""

import sys
import os
import re


def parse_docx(filepath: str) -> str:
    """将 .docx 文件转换为 Markdown 文本"""
    try:
        from docx import Document
    except ImportError:
        print(
            "❌ 缺少 python-docx 库。请运行：pip install python-docx",
            file=sys.stderr,
        )
        sys.exit(1)

    if not os.path.exists(filepath):
        print(f"❌ 文件不存在：{filepath}", file=sys.stderr)
        sys.exit(1)

    if not filepath.lower().endswith(".docx"):
        print(f"⚠️ 文件扩展名不是 .docx，尝试继续解析...", file=sys.stderr)

    doc = Document(filepath)
    lines: list[str] = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            lines.append("")
            continue

        style_name = para.style.name.lower() if para.style.name else ""

        # 标题样式映射
        if style_name.startswith("heading 1") or style_name.startswith("heading1"):
            lines.append(f"# {text}")
        elif style_name.startswith("heading 2") or style_name.startswith("heading2"):
            lines.append(f"## {text}")
        elif style_name.startswith("heading 3") or style_name.startswith("heading3"):
            lines.append(f"### {text}")
        elif style_name.startswith("heading"):
            level_match = re.search(r"heading\s*(\d)", style_name)
            level = int(level_match.group(1)) if level_match else 4
            lines.append(f"{'#' * level} {text}")
        else:
            # 检查是否为加粗（作为小标题）
            runs_bold = all(
                run.bold for run in para.runs if run.text.strip()
            )
            if runs_bold and para.runs:
                lines.append(f"**{text}**")
            else:
                lines.append(text)

    # 处理表格
    if doc.tables:
        lines.append("")
        for idx, table in enumerate(doc.tables):
            lines.append(f"<!-- 表格 {idx + 1} -->")
            lines.append("")
            for row_idx, row in enumerate(table.rows):
                cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
                lines.append("| " + " | ".join(cells) + " |")
                if row_idx == 0:
                    lines.append("|" + "|".join(["---"] * len(cells)) + "|")
            lines.append("")

    # 合并连续空行
    result_lines: list[str] = []
    prev_empty = False
    for line in lines:
        is_empty = line.strip() == "" and not line.startswith("<!--")
        if is_empty and prev_empty:
            continue
        prev_empty = is_empty
        result_lines.append(line)

    return "\n".join(result_lines).strip()


def main():
    if len(sys.argv) < 2:
        print("用法：python parser.py <合同文件路径.docx>", file=sys.stderr)
        print("示例：python parser.py contract.docx", file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]
    markdown = parse_docx(filepath)
    print(markdown)


if __name__ == "__main__":
    main()
