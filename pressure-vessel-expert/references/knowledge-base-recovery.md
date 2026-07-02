# 知识库常见问题与恢复

## 1. `get_indexed_names()` 修复（核心 bug，2026-05-18）

**症状**：extracted/ 目录已有正确 txt 文件，index.json 也已注册，但批量脚本仍然重复处理这些文件，导致 OCR 低质量结果覆盖正确数据。

**根因**：`process_pdf_batch.py` 中 `get_indexed_names()` 直接返回 `index.keys()`。由于 JSON 存储时中文文件名经过 `surrogateescape` 编码，key 与 `STANDARDS_DIR.glob("*.pdf")` 返回的文件名不匹配，导致脚本认为这些文件"未处理"。

**修复后的正确逻辑**（已验证写入脚本）：
```python
def get_indexed_names(index):
    """获取已索引的文件名集合（基于 extracted 目录的 txt 文件是否存在）"""
    indexed = set()
    for doc in index.get("documents", {}).values():
        txt = doc.get("extracted_txt", "")
        if txt and (EXTRACTED_DIR / txt).exists():
            indexed.add(txt.replace(".txt", ".pdf"))
    return indexed
```
**关键**：`extracted_txt` 字段是 truth source，它存的是原始未编码的文件名，基于文件存在性判断才是可靠的。

---

## 2. DPI 选择与内存约束（已解决，2026-05-18）

**根因**：原 `convert_from_path(dpi)` 一次性加载全部 PDF 页生成图像缓冲，大文件（如 TEMA 87.5MB PDF）生成 ~1.7GB 图像导致 Python RSS 涨至 1.4GB+，触发 OOM Killer。

**修复方案**（`process_pdf_batch.py` 第 67-82 行）：逐页 OCR + 实时垃圾回收。
```python
images = convert_from_path(pdf_path, dpi=DPI, first_page=page_num, last_page=page_num)
img = images[0]
text = pytesseract.image_to_string(img, lang="chi_sim+eng")
images[0].close()
del images
gc.collect()
```

**实测对比**（DPI 200，逐页处理）：
| 指标 | 修复前（批量加载） | 修复后（逐页） |
|------|------------------|---------------|
| Python RSS | ~545MB（峰值 1.4GB+） | ~55MB（稳态） |
| tesseract RSS | ~117MB | ~117MB |
| 系统可用内存 | 0 → OOM | ~1.4GB 安全 |
| OCR 质量 | 差（被迫 DPI 100） | 好（DPI 200） |

**结论**：逐页处理后，**DPI 200 稳定可用**，质量远优于 DPI 100。

```bash
# 推荐用法（DPI 200，逐页防OOM）
python3 scripts/process_pdf_batch.py --all --dpi 200

# 大文件单独处理
python3 scripts/process_pdf_batch.py --file "大文件.pdf" --dpi 200
```

> ⚠️ `--dpi 100` 仍可工作，但**仅在逐页处理框架内**才有意义（原批量加载无论 DPI 多少都会 OOM）。

---

## 3. index.json  surrogate 编码问题

**症状**：`UnicodeEncodeError: 'utf-8' codec can't encode character '\\udcd3'`

**原因**：中文文件名在写入 JSON 时用 `surrogateescape` 编码，但读取后重新写入时 `surrogatepass` 缺失导致出错。

**安全读写模式**：
```python
# 读取
with open(INDEX_FILE, "r", encoding="utf-8", errors="surrogateescape") as f:
    data = json.load(f)

# 写入
with open(INDEX_FILE, "w", encoding="utf-8", errors="surrogatepass") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

---

## 4. 重建 index（从 extracted/ 扫描，基于 extracted_txt 字段）

**推荐时机**：每次跑批量前，或发现 index 有问题时。

```python
import json, time, os, base64
from pathlib import Path

extracted_dir = Path("~/.hermes/skills/engineering/pressure-vessel-expert/knowledge/extracted")
idx_path = Path("~/.hermes/skills/engineering/pressure-vessel-expert/knowledge/index.json")

actual_txts = sorted([f for f in extracted_dir.iterdir() if f.suffix == ".txt"])

new_docs = {}
for txt in actual_txts:
    size_kb = txt.stat().st_size / 1024
    try:
        with open(txt, encoding="utf-8", errors="surrogateescape") as f:
            lines = len(f.readlines())
    except:
        lines = 0
    # 用 base64 编码 key 避免 surrogate 问题
    key = base64.b64encode(txt.name.encode("utf-8", errors="surrogateescape")).decode("ascii") + ".txt"
    new_docs[key] = {
        "extracted_txt": txt.name,
        "txt_path": str(txt),
        "lines": lines,
        "size_kb": round(size_kb, 1),
        "method": "user-provided",
        "note": "来源: 用户提供的识别文本"
    }

new_data = {"documents": new_docs, "last_updated": time.strftime("%Y-%m-%dT%H:%M:%S")}
with open(idx_path, "w", encoding="utf-8", errors="surrogatepass") as f:
    json.dump(new_data, f, ensure_ascii=False, indent=2)
```

---

## 5. 用户提供预识别文本时的完整流程

**三步走，永远不跑裸 `--all`**：

```bash
# Step 1: 重建 index（见上面脚本）
# Step 2: 确认 missing PDF
python3 -c "
import json, base64, os
from pathlib import Path
std = Path('~/.hermes/skills/engineering/pressure-vessel-expert/knowledge/standards')
ext = Path('~/.hermes/skills/engineering/pressure-vessel-expert/knowledge/extracted')
idx = Path('~/.hermes/skills/engineering/pressure-vessel-expert/knowledge/index.json')
with open(idx, 'rb') as f:
    data = json.loads(f.read().decode('utf-8', errors='replace'))
covered = {base64.b64decode(k.replace('.txt','')).decode('utf-8', errors='surrogateescape').replace('.txt','.pdf') for k in data['documents']}
pdfs = sorted([f.name for f in std.iterdir() if f.suffix == '.pdf'])
missing = [p for p in pdfs if p not in covered]
print(f'Missing: {len(missing)}')
for p in missing: print(f'  {p}')
"

# Step 3: 只对 missing 跑批量（dpi 200，逐页处理不会OOM）
python3 scripts/process_pdf_batch.py --all --dpi 200
```

---

## 6. 逐个处理缺失 PDF（推荐方式，2026-05-18）

**背景**：跑裸 `--all` 会重复处理已完成的 PDF；`--file "文件名"` 参数因编码问题无法精确匹配文件名。正确做法：**按字节大小定位缺失文件，逐个处理**。

```python
import os, glob
standards_dir = '/home/hermes-admin/.hermes/skills/engineering/pressure-vessel-expert/knowledge/standards'
files_by_size = {}
for f in glob.glob(f'{standards_dir}/*.pdf'):
    sz = os.path.getsize(f)
    if sz not in files_by_size:
        files_by_size[sz] = []
    files_by_size[sz].append(f)

# 根据已知缺失文件的大小定位（单位：字节，±100KB 容差）
targets = {}
for t in [int(27.5*1024*1024), int(8.3*1024*1024), int(8.0*1024*1024)]:
    for sz in files_by_size:
        if abs(sz - t) < 100*1024:
            targets[t] = files_by_size[sz][0]
            break

for t, path in sorted(targets.items()):
    print(f"{t//1024//1024}MB: {os.path.basename(path)[:20]}")
```

**逐个处理流程**：
1. 先 `pdftotext -layout` 探测（>5KB → 文字型，直接用）
2. `<5KB` → 启动逐页 OCR（`first_page=N, last_page=N` + `gc.collect()`）
3. 每完成一个 → 立即写 index.json（`surrogatepass` 模式）
4. 参考 `/tmp/proc_one.py`

## 7. exit code 137 的含义

不是"程序崩溃"，是 **OOM Killer（SIGKILL）** 在系统内存不足时主动杀死进程。

**2026-05-18 更新**：脚本已修复为逐页处理，exit 137 应已消失。如果仍然出现：
1. 确认使用的是**修复后的脚本**（逐页 `first_page=N, last_page=N`）
2. 检查 `/tmp/tess_*` 临时文件是否有残留
3. 确认系统没有其他进程大量占用内存
