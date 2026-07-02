#!/usr/bin/env python3
"""
压力容器专家 — PDF 分批处理脚本
逐个处理 PDF 并实时保存 index，避免大文件一次性处理导致 OOM。
适合扫描版大 PDF（>20MB）或大量文件批量处理。

用法:
  python3 scripts/process_pdf_batch.py --all --dpi 200    # 处理所有未索引的 PDF
  python3 scripts/process_pdf_batch.py --file xxx.pdf     # 处理单个文件
  python3 scripts/process_pdf_batch.py --all --ocr --dpi 150  # 强制 OCR，降低 DPI 提速

中断后可重新运行，已处理的文件会自动跳过。
"""
import json, time, sys, subprocess
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
STANDARDS_DIR = SKILL_ROOT / "knowledge" / "standards"
EXTRACTED_DIR = SKILL_ROOT / "knowledge" / "extracted"
INDEX_FILE = SKILL_ROOT / "knowledge" / "index.json"

EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)


def load_index():
    if INDEX_FILE.exists():
        with open(INDEX_FILE, "r", encoding="utf-8", errors="surrogateescape") as f:
            return json.load(f)
    return {"documents": {}, "last_updated": None}


def save_index(index):
    index["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    # 修复: 使用 surrogateescape 处理含特殊字符的中文文件名
    safe_docs = {}
    for k, v in index.get("documents", {}).items():
        safe_docs[sanitize_key(k)] = v
    index["documents"] = safe_docs
    with open(INDEX_FILE, "w", encoding="utf-8", errors="surrogateescape") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def get_indexed_names(index):
    """获取已索引的文件名集合（基于 extracted 目录的 txt 文件是否存在）"""
    indexed = set()
    for doc in index.get("documents", {}).values():
        txt = doc.get("extracted_txt", "")
        if txt and (EXTRACTED_DIR / txt).exists():
            indexed.add(txt.replace(".txt", ".pdf"))
    return indexed


def extract_with_pdftotext(pdf_path):
    """用 pdftotext 提取文本（适用于文字型 PDF）"""
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", str(pdf_path), "-"],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0 and len(result.stdout.strip()) > 200:
            return result.stdout, "pdftotext"
    except Exception:
        pass
    return None, None


def extract_with_ocr(pdf_path, dpi=200):
    """用 Tesseract OCR 提取扫描版 PDF（逐页处理，避免大文件 OOM）"""
    import pytesseract
    from pdf2image import convert_from_path
    import gc
    images = convert_from_path(str(pdf_path), dpi=dpi, first_page=1, last_page=1)
    total = len(convert_from_path(str(pdf_path), dpi=dpi))  # 先拿总页数
    pages = []
    for page_num in range(1, total + 1):
        images = convert_from_path(str(pdf_path), dpi=dpi, first_page=page_num, last_page=page_num)
        img = images[0]
        text = pytesseract.image_to_string(img, lang="chi_sim+eng", config="--psm 6")
        pages.append(f"--- 第 {page_num} 页 ---\n{text.strip()}")
        del img, images
        gc.collect()
        if page_num % 10 == 0 or page_num == total:
            print(f"  OCR 进度: {page_num}/{total} 页", flush=True)
    return "\n\n".join(pages), "ocr"


def sanitize_key(k):
    """将含 surrogate 的字符串安全地转为可 JSON 序列化的形式"""
    return k.encode("utf-8", errors="surrogateescape").decode("utf-8", errors="replace")

def process_one(pdf_path, force_ocr=False, dpi=200):
    """处理单个 PDF，返回是否成功"""
    safe_name = sanitize_key(pdf_path.name)
    size_mb = pdf_path.stat().st_size / 1024 / 1024
    print(f"\n📄 处理: {safe_name} ({size_mb:.1f} MB)")

    text = None
    method = None

    if not force_ocr:
        text, method = extract_with_pdftotext(pdf_path)

    if not text:
        print(f"  ℹ pdftotext 失败/文本太少，切换 OCR...")
        text, method = extract_with_ocr(pdf_path, dpi=dpi)

    if not text or len(text.strip()) < 100:
        print(f"  ❌ 提取失败")
        return False

    txt_name = pdf_path.stem + ".txt"
    txt_path = EXTRACTED_DIR / txt_name
    txt_path.write_text(text, encoding="utf-8")

    index = load_index()
    index["documents"][safe_name] = {
        "extracted_txt": txt_name,
        "txt_path": str(txt_path),
        "lines": len(text.splitlines()),
        "size_kb": round(len(text.encode("utf-8")) / 1024, 1),
        "method": method,
    }
    save_index(index)

    print(f"  ✅ {method} | {len(text.splitlines())} 行 / {index['documents'][safe_name]['size_kb']} KB")
    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="压力容器专家 — PDF 分批处理（逐个处理，实时保存 index，避免 OOM）"
    )
    parser.add_argument("--file", help="处理单个 PDF 文件")
    parser.add_argument("--ocr", action="store_true", help="强制使用 OCR（跳过 pdftotext）")
    parser.add_argument("--dpi", type=int, default=200,
                        help="OCR 分辨率，默认 200。降低可提速但会降低识别率")
    parser.add_argument("--all", action="store_true", help="处理所有未索引的 PDF")
    args = parser.parse_args()

    index = load_index()
    indexed_safe = get_indexed_names(index)

    # 构建 safe_name -> real_path 映射（处理文件名 surrogate 问题）
    safe_to_real = {}
    for f in STANDARDS_DIR.glob("*.pdf"):
        safe = f.name.encode("utf-8", errors="surrogateescape").decode("utf-8", errors="replace")
        safe_to_real[safe] = f

    if args.file:
        pdfs = [Path(args.file)]
    elif args.all:
        pdfs = [safe_to_real[s] for s in safe_to_real if s not in indexed_safe]
    else:
        pdfs = sorted(STANDARDS_DIR.glob("*.pdf"))

    if not pdfs:
        print("📭 没有需要处理的 PDF。")
        sys.exit(0)

    print(f"待处理: {len(pdfs)} 个 PDF\n{'='*60}")

    success = 0
    failed = 0
    for pdf_path in pdfs:
        if not pdf_path.exists():
            print(f"❌ 文件不存在: {pdf_path.name}")
            failed += 1
            continue
        if process_one(pdf_path, force_ocr=args.ocr, dpi=args.dpi):
            success += 1
        else:
            failed += 1
        # 每处理一个短暂休息，释放内存
        time.sleep(1)

    print(f"\n{'='*60}")
    print(f"📋 完成: {success} 成功, {failed} 失败")
