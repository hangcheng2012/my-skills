#!/usr/bin/env python3
"""
压力容器专家 — PDF 标准文档提取与索引工具
支持文本型 PDF 和扫描版 PDF（自动 OCR），中英文混合识别。

基础依赖: pip install pdfplumber
OCR 依赖: pip install pytesseract pdf2image Pillow
系统依赖: apt install tesseract-ocr tesseract-ocr-chi-sim poppler-utils
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Skill 根目录（脚本在 scripts/ 下，往上一级就是 skill 根）
SKILL_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = SKILL_ROOT / "knowledge"
STANDARDS_DIR = KNOWLEDGE_DIR / "standards"
EXTRACTED_DIR = KNOWLEDGE_DIR / "extracted"
INDEX_FILE = KNOWLEDGE_DIR / "index.json"

# ── 工具函数 ──────────────────────────────────────────────

def _check_tesseract_chinese() -> bool:
    """检查 Tesseract 是否安装了中文语言包。"""
    import subprocess
    try:
        result = subprocess.run(
            ["tesseract", "--list-langs"],
            capture_output=True, text=True, timeout=10
        )
        langs = result.stdout.strip().splitlines()
        # Tesseract 4+ 输出第一行是信息行，跳过
        available = [l.strip() for l in langs if l.strip() and not l.startswith("List")]
        return "chi_sim" in available
    except Exception:
        return False


# ── 文本提取（非 OCR）────────────────────────────────────

def extract_text_pdfplumber(pdf_path: Path) -> str | None:
    """用 pdfplumber 提取文本，中文兼容性最佳。"""
    try:
        import pdfplumber
    except ImportError:
        return None
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages = []
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    pages.append(f"--- 第 {i+1} 页 ---\n{text}")
            return "\n\n".join(pages) if pages else None
    except Exception as e:
        print(f"  ⚠ pdfplumber 失败: {e}", file=sys.stderr)
        return None


def extract_text_pdftotext(pdf_path: Path) -> str | None:
    """用系统 pdftotext 提取。"""
    import subprocess
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", str(pdf_path), "-"],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"  ⚠ pdftotext 失败: {e}", file=sys.stderr)
    return None


# ── OCR 提取（扫描版 PDF）─────────────────────────────────

def extract_text_ocr(pdf_path: Path, dpi: int = 400, lang: str = "chi_sim+eng") -> str | None:
    """
    对扫描版 PDF 逐页 OCR。
    需要: tesseract-ocr + tesseract-ocr-chi-sim + poppler-utils
    Python: pytesseract, pdf2image, Pillow
    """
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError:
        print("  ⚠ OCR 需要安装: pip install pytesseract pdf2image Pillow", file=sys.stderr)
        return None

    if not _check_tesseract_chinese():
        print("  ⚠ 未检测到 Tesseract 中文语言包", file=sys.stderr)
        print("    安装: apt install tesseract-ocr tesseract-ocr-chi-sim", file=sys.stderr)
        return None

    try:
        images = convert_from_path(pdf_path, dpi=dpi)
    except Exception as e:
        print(f"  ⚠ PDF 转图片失败: {e}", file=sys.stderr)
        print("    可能需要: apt install poppler-utils", file=sys.stderr)
        return None

    total = len(images)
    pages = []
    for i, img in enumerate(images):
        try:
            text = pytesseract.image_to_string(img, lang=lang, config="--psm 6")
            pages.append(f"--- 第 {i+1} 页 ---\n{text.strip()}")
        except Exception as e:
            pages.append(f"--- 第 {i+1} 页 [OCR失败: {e}] ---")
        # 进度显示（每 10 页或最后一页）
        if (i + 1) % 10 == 0 or i == total - 1:
            print(f"  🔍 OCR 进度: {i+1}/{total} 页", flush=True)

    return "\n\n".join(pages)


# ── 智能提取（自动选择策略）───────────────────────────────

def extract_text(pdf_path: Path, force_ocr: bool = False, ocr_dpi: int = 400) -> tuple[str, str]:
    """
    智能提取 PDF 文本。返回 (文本内容, 提取方式标识)。
    策略:
      1. force_ocr → 直接 OCR
      2. pdfplumber → 成功且 >200 字符 → 直接返回 (标记 "direct")
      3. pdftotext  → 成功且 >200 字符 → 返回 (标记 "pdftotext")
      4. 以上都失败或文本太少 → OCR (标记 "ocr")
    """
    if force_ocr:
        text = extract_text_ocr(pdf_path, dpi=ocr_dpi)
        if text and len(text.strip()) > 100:
            return text, "ocr"
        raise RuntimeError(f"OCR 失败: '{pdf_path.name}'")

    # 先尝试直接提取
    text = extract_text_pdfplumber(pdf_path)
    if text and len(text.strip()) > 200:
        return text, "direct"

    text = extract_text_pdftotext(pdf_path)
    if text and len(text.strip()) > 200:
        return text, "pdftotext"

    # 文本太少 → 自动降级到 OCR
    if text and len(text.strip()) > 0:
        print(f"  ℹ 文本量过少 ({len(text.strip())} 字符)，可能为扫描件，自动切换 OCR...")
    else:
        print(f"  ℹ 无法直接提取文本，可能为扫描件，自动切换 OCR...")

    ocr_text = extract_text_ocr(pdf_path, dpi=ocr_dpi)
    if ocr_text and len(ocr_text.strip()) > 100:
        return ocr_text, "ocr"

    raise RuntimeError(
        f"无法提取 '{pdf_path.name}' 的文本内容。\n"
        "  如果 PDF 是扫描件，请确保已安装 OCR 依赖:\n"
        "  apt install tesseract-ocr tesseract-ocr-chi-sim poppler-utils\n"
        "  pip install pytesseract pdf2image Pillow"
    )


# ── 索引管理 ──────────────────────────────────────────────

def load_index() -> dict:
    """加载索引文件，不存在则返回空结构。"""
    if INDEX_FILE.exists():
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"documents": {}, "last_updated": None}


def save_index(index: dict):
    """保存索引文件。"""
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    index["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


# ── 命令实现 ──────────────────────────────────────────────

def cmd_process(file_path: str | None = None, reindex: bool = False,
                force_ocr: bool = False, ocr_dpi: int = 400):
    """处理 PDF 文件：提取文本 → 写入 extracted/ → 更新 index.json"""
    STANDARDS_DIR.mkdir(parents=True, exist_ok=True)
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    index = {} if reindex else load_index()

    if file_path:
        pdfs = [Path(file_path)]
    else:
        pdfs = sorted(STANDARDS_DIR.glob("*.pdf"))

    if not pdfs:
        print("📭 standards/ 目录下没有 PDF 文件。")
        print("  请将标准 PDF 放入 knowledge/standards/")
        return

    success = 0
    failed = 0

    for pdf_path in pdfs:
        if not pdf_path.exists():
            print(f"❌ 文件不存在: {pdf_path}")
            failed += 1
            continue

        safe_name = pdf_path.name.encode("utf-8", errors="surrogateescape").decode("utf-8", errors="replace")
        print(f"\n📄 处理: {safe_name}")
        start_time = time.time()
        try:
            text, method = extract_text(pdf_path, force_ocr=force_ocr, ocr_dpi=ocr_dpi)
        except RuntimeError as e:
            print(f"  ❌ {e}")
            failed += 1
            continue

        elapsed = time.time() - start_time
        txt_name = pdf_path.stem + ".txt"
        txt_path = EXTRACTED_DIR / txt_name
        lines = text.splitlines()
        txt_path.write_text(text, encoding="utf-8")

        method_label = {"direct": "直接提取", "pdftotext": "pdftotext", "ocr": "OCR 识别"}.get(method, method)
        index["documents"][pdf_path.name] = {
            "extracted_txt": txt_name,
            "txt_path": str(txt_path),
            "lines": len(lines),
            "size_kb": round(len(text.encode("utf-8")) / 1024, 1),
            "method": method,
            "note": f"提取方式: {method_label}",
        }
        print(f"  ✅ {method_label} | {len(lines)} 行 / {index['documents'][pdf_path.name]['size_kb']} KB | 耗时 {elapsed:.0f}s")
        success += 1

    save_index(index)
    print(f"\n📋 完成: {success} 成功, {failed} 失败, 共 {len(index['documents'])} 份文档已索引")


def cmd_list():
    """列出已索引的文档。"""
    index = load_index()
    docs = index.get("documents", {})
    if not docs:
        print("📭 暂无已索引文档。")
        print("  1. 将 PDF 放入 knowledge/standards/")
        print("  2. 运行: python3 scripts/process_pdf.py")
        return

    print(f"📚 已索引 {len(docs)} 份文档:\n")
    for pdf_name, info in docs.items():
        draft = "⚠️ 征求意见稿 " if info.get("draft") else ""
        lines = info.get("lines", "?")
        size = info.get("size_kb", "?")
        method = info.get("method", "?")
        note = info.get("note", "")
        print(f"  📄 {pdf_name}")
        print(f"     {draft}{lines} 行 / {size} KB | {note}")
    if index.get("last_updated"):
        print(f"\n  最后更新: {index['last_updated']}")


def cmd_search(query: str, context_lines: int = 3):
    """在 extracted/ 目录中搜索关键词，带上下文。"""
    index = load_index()
    docs = index.get("documents", {})
    if not docs:
        print("📭 请先运行 process_pdf.py 提取 PDF 文本")
        return

    found_any = False
    for pdf_name, info in docs.items():
        txt_path = Path(info["txt_path"])
        if not txt_path.exists():
            continue
        lines = txt_path.read_text(encoding="utf-8").splitlines()
        matches = []
        for i, line in enumerate(lines):
            if query.lower() in line.lower():
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                snippet = []
                for j in range(start, end):
                    prefix = ">>>" if j == i else "   "
                    snippet.append(f"  {prefix} L{j+1}: {lines[j]}")
                matches.append("\n".join(snippet))
        if matches:
            found_any = True
            print(f"\n{'='*60}")
            print(f"📄 {pdf_name} — {len(matches)} 处匹配")
            print(f"{'='*60}")
            for m in matches[:20]:
                print(m)
                print("  ---")
            if len(matches) > 20:
                print(f"  ... 还有 {len(matches) - 20} 处匹配，请缩小搜索范围")

    if not found_any:
        print(f"🔍 未找到匹配 '{query}' 的内容")
        print("  提示: 尝试更短的关键词，比如 '开孔' 而非 '开孔补强计算'")


# ── 环境检查 ──────────────────────────────────────────────

def cmd_check():
    """检查运行环境，列出缺失的依赖。"""
    print("🔧 环境检查\n")

    # Python 依赖
    py_deps = {
        "pdfplumber": "pip install pdfplumber",
        "pytesseract": "pip install pytesseract",
        "pdf2image": "pip install pdf2image",
    }
    print("Python 依赖:")
    for mod, install_cmd in py_deps.items():
        try:
            __import__(mod)
            print(f"  ✅ {mod}")
        except ImportError:
            print(f"  ❌ {mod} — {install_cmd}")

    # 系统依赖
    import subprocess
    sys_deps = {
        "tesseract": "apt install tesseract-ocr",
        "pdftotext": "apt install poppler-utils",
    }
    print("\n系统工具:")
    for cmd, install_hint in sys_deps.items():
        try:
            subprocess.run(["which", cmd], capture_output=True, check=True)
            print(f"  ✅ {cmd}")
        except Exception:
            print(f"  ❌ {cmd} — {install_hint}")

    # Tesseract 语言包
    print("\nTesseract 语言包:")
    if _check_tesseract_chinese():
        print("  ✅ chi_sim (简体中文)")
    else:
        print("  ❌ chi_sim — apt install tesseract-ocr-chi-sim")

    # 检查 PDF 文件
    standards = sorted(STANDARDS_DIR.glob("*.pdf")) if STANDARDS_DIR.exists() else []
    print(f"\nPDF 文件: {len(standards)} 个在 knowledge/standards/")
    for f in standards:
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  📄 {f.name} ({size_mb:.1f} MB)")

    # 检查已索引
    index = load_index()
    docs = index.get("documents", {})
    print(f"\n已索引文档: {len(docs)} 份")


# ── CLI ───────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="压力容器专家 — PDF 标准文档提取与索引工具（支持扫描版 OCR）"
    )
    parser.add_argument("--file", help="处理单个 PDF 文件")
    parser.add_argument("--reindex", action="store_true", help="清空索引后重新提取全部 PDF")
    parser.add_argument("--ocr", action="store_true", help="强制使用 OCR（跳过直接文本提取）")
    parser.add_argument("--ocr-dpi", type=int, default=400,
                        help="OCR 分辨率，默认 400。降低可提速但会降低识别率")
    parser.add_argument("--list", action="store_true", help="列出已索引的文档")
    parser.add_argument("--search", help="搜索关键词（在 extracted/ 中全文搜索）")
    parser.add_argument("--context", type=int, default=3, help="搜索上下文行数（默认 3）")
    parser.add_argument("--check", action="store_true", help="检查环境依赖和 PDF 文件状态")
    args = parser.parse_args()

    if args.check:
        cmd_check()
    elif args.list:
        cmd_list()
    elif args.search:
        cmd_search(args.search, args.context)
    else:
        cmd_process(file_path=args.file, reindex=args.reindex,
                    force_ocr=args.ocr, ocr_dpi=args.ocr_dpi)


if __name__ == "__main__":
    main()