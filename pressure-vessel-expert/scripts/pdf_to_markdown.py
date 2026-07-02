#!/usr/bin/env python3
"""
PDF → Markdown 转换器（扫描版专用）
使用 Claude Vision API 逐页识别，同时处理：
  - OCR 乱码问题（直接视觉识别，绕过字体编码）
  - 图表提取（识别后转为 Markdown 格式）
  - 表格还原（输出标准 Markdown 表格）

用法：
  python pdf_to_markdown.py input.pdf
  python pdf_to_markdown.py input.pdf --output output.md
  python pdf_to_markdown.py input.pdf --pages 1-10        # 只处理前10页
  python pdf_to_markdown.py input.pdf --dpi 200           # 提高分辨率（默认150）
  python pdf_to_markdown.py input.pdf --resume            # 从上次中断处继续
"""

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

import fitz  # PyMuPDF
import anthropic

# ── 常量 ─────────────────────────────────────────────────────────────────────

MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096
DPI_DEFAULT = 150
RETRY_LIMIT = 3
RETRY_DELAY = 5  # 秒

SYSTEM_PROMPT = """你是一个专业的文档转换助手，专门处理中文技术标准和规范文档的扫描件。

你的任务是将PDF页面图片转换为结构化的Markdown格式。请严格遵循以下规则：

## 文字识别
- 准确识别所有中文、英文、数字和符号
- 保留原文的标题层级（用 # ## ### 等表示）
- 保留段落结构和换行

## 表格处理
- 将所有表格转换为标准 Markdown 表格格式
- 表格前加标注：`<!-- TABLE: 表X-X 表格名称 -->`
- 如果表格太复杂无法完整转换，用描述性文字说明表格内容

## 图表处理
- 对于流程图、示意图、架构图等：
  - 用 `![图X-X 图表描述](figure_页码_序号.png)` 占位
  - 紧接着用文字描述图表内容和关键信息
  - 格式：`<!-- FIGURE: 图X-X 描述 | 内容摘要 -->`
- 对于数据图表（折线图、柱状图等）：
  - 尝试提取关键数据点并以表格形式呈现
  - 标注图表类型和主要结论

## 公式处理
- 数学公式用 $...$ 或 $$...$$ 包裹（LaTeX格式）
- 简单公式直接写出

## 特殊元素
- 注释、警告框等用 > 引用块表示
- 页眉页脚信息忽略（除非是重要标注）
- 页码忽略

## 输出格式
直接输出Markdown内容，不要有任何前言或解释。"""


# ── 核心函数 ──────────────────────────────────────────────────────────────────

def pdf_page_to_base64(doc: fitz.Document, page_num: int, dpi: int = DPI_DEFAULT) -> str:
    """将PDF页面渲染为base64编码的PNG图片"""
    page = doc[page_num]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
    img_bytes = pix.tobytes("png")
    return base64.standard_b64encode(img_bytes).decode("utf-8")


def process_page_with_claude(
    client: anthropic.Anthropic,
    img_b64: str,
    page_num: int,
    total_pages: int,
) -> str:
    """调用 Claude Vision API 处理单页"""
    for attempt in range(RETRY_LIMIT):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": img_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": f"请转换这个PDF页面（第{page_num + 1}页，共{total_pages}页）。",
                            },
                        ],
                    }
                ],
            )
            return response.content[0].text

        except anthropic.RateLimitError:
            if attempt < RETRY_LIMIT - 1:
                wait = RETRY_DELAY * (attempt + 1) * 2
                print(f"  ⚠️  触发限流，等待 {wait}s 后重试...", flush=True)
                time.sleep(wait)
            else:
                raise

        except anthropic.APIError as e:
            if attempt < RETRY_LIMIT - 1:
                print(f"  ⚠️  API错误（{e}），{RETRY_DELAY}s 后重试...", flush=True)
                time.sleep(RETRY_DELAY)
            else:
                raise

    return f"<!-- ERROR: 第{page_num + 1}页处理失败 -->\n"


def load_progress(progress_file: Path) -> dict:
    """加载处理进度"""
    if progress_file.exists():
        with open(progress_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"completed_pages": [], "results": {}}


def save_progress(progress_file: Path, progress: dict):
    """保存处理进度"""
    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def parse_page_range(page_range_str: str, total_pages: int) -> list[int]:
    """解析页码范围，如 '1-10,15,20-25'"""
    pages = set()
    for part in page_range_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            start = max(1, int(start.strip()))
            end = min(total_pages, int(end.strip()))
            pages.update(range(start, end + 1))
        else:
            p = int(part.strip())
            if 1 <= p <= total_pages:
                pages.add(p)
    return sorted(pages)


# ── 主流程 ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="扫描版PDF → Markdown转换器（使用Claude Vision）"
    )
    parser.add_argument("input", help="输入PDF路径")
    parser.add_argument("--output", "-o", help="输出Markdown路径（默认与PDF同名）")
    parser.add_argument(
        "--pages", "-p",
        help="处理的页码范围，如 '1-10' 或 '1-5,8,10-15'（默认全部）"
    )
    parser.add_argument(
        "--dpi", type=int, default=DPI_DEFAULT,
        help=f"渲染分辨率（默认{DPI_DEFAULT}，扫描件推荐200-300）"
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="从上次中断处继续（跳过已处理的页面）"
    )
    parser.add_argument(
        "--delay", type=float, default=1.0,
        help="每页处理后的延迟秒数（避免限流，默认1.0）"
    )
    args = parser.parse_args()

    # ── 路径设置 ──────────────────────────────────────────────────────────────
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 文件不存在: {input_path}")
        sys.exit(1)

    output_path = Path(args.output) if args.output else input_path.with_suffix(".md")
    progress_file = output_path.with_suffix(".progress.json")

    # ── 检查 API Key ──────────────────────────────────────────────────────────
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ 未找到 ANTHROPIC_API_KEY 环境变量")
        print("   请设置：export ANTHROPIC_API_KEY=your_key_here")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # ── 打开PDF ───────────────────────────────────────────────────────────────
    print(f"\n📄 打开PDF: {input_path}")
    doc = fitz.open(str(input_path))
    total_pages = len(doc)
    print(f"   共 {total_pages} 页")

    # ── 确定处理页码 ──────────────────────────────────────────────────────────
    if args.pages:
        target_pages = [p - 1 for p in parse_page_range(args.pages, total_pages)]
        print(f"   处理范围: 第{args.pages}页（共{len(target_pages)}页）")
    else:
        target_pages = list(range(total_pages))

    # ── 加载进度 ──────────────────────────────────────────────────────────────
    progress = load_progress(progress_file) if args.resume else {"completed_pages": [], "results": {}}

    if args.resume and progress["completed_pages"]:
        already_done = set(progress["completed_pages"])
        target_pages = [p for p in target_pages if p not in already_done]
        print(f"   ✅ 已完成 {len(already_done)} 页，继续处理剩余 {len(target_pages)} 页")

    # ── 逐页处理 ──────────────────────────────────────────────────────────────
    print(f"\n🚀 开始处理（DPI={args.dpi}，模型={MODEL}）\n")

    for i, page_num in enumerate(target_pages):
        print(f"  [{i + 1}/{len(target_pages)}] 处理第 {page_num + 1} 页...", end=" ", flush=True)
        t0 = time.time()

        try:
            img_b64 = pdf_page_to_base64(doc, page_num, args.dpi)
            md_content = process_page_with_claude(client, img_b64, page_num, total_pages)

            progress["results"][str(page_num)] = md_content
            progress["completed_pages"].append(page_num)
            save_progress(progress_file, progress)

            elapsed = time.time() - t0
            # 预估字符数（粗略判断内容量）
            chars = len(md_content)
            print(f"✓ ({elapsed:.1f}s, {chars}字符)")

        except Exception as e:
            print(f"❌ 失败: {e}")
            progress["results"][str(page_num)] = f"\n<!-- ERROR 第{page_num + 1}页处理失败: {e} -->\n"
            save_progress(progress_file, progress)

        # 请求间隔，避免限流
        if i < len(target_pages) - 1 and args.delay > 0:
            time.sleep(args.delay)

    doc.close()

    # ── 合并输出 ──────────────────────────────────────────────────────────────
    print(f"\n📝 合并输出到: {output_path}")

    all_pages = sorted(progress["results"].keys(), key=lambda x: int(x))
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# {input_path.stem}\n\n")
        f.write(f"> 转换自: `{input_path.name}`  \n")
        f.write(f"> 总页数: {total_pages}页  \n")
        f.write(f"> 转换工具: Claude Vision (pdf_to_markdown.py)\n\n")
        f.write("---\n\n")

        for page_key in all_pages:
            page_num = int(page_key)
            f.write(f"\n<!-- PAGE {page_num + 1} -->\n\n")
            f.write(progress["results"][page_key])
            f.write("\n\n---")

    # ── 完成统计 ──────────────────────────────────────────────────────────────
    completed = len(progress["completed_pages"])
    total_target = completed + len(target_pages) - len(target_pages)  # 已全部处理

    print(f"\n✅ 完成！")
    print(f"   处理页数: {completed}/{total_pages}")
    print(f"   输出文件: {output_path}")

    if progress_file.exists():
        progress_file.unlink()  # 清理进度文件
        print(f"   进度文件已清理")


if __name__ == "__main__":
    main()