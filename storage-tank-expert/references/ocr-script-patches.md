# OCR 脚本补丁记录（process_pdf 系列）

> 维护人：J.A.R.V.I.S. | 2026-06-30 立
> 适用于 `vessel/storage-tank-expert/scripts/`（与 `vessel/pressure-vessel-expert/scripts/` 共享同一份补丁）

---

## 补丁 1：`process_pdf_batch.py` OOM 修复（关键）

**症状**：扫描版大 PDF（>150 页，>20MB）跑 `--ocr` 时，进程被 OOM Killer 杀掉。

**根因**：`extract_with_ocr()` 函数用 `convert_from_path(path, dpi=dpi)`（**无页数限制**）来取总页数。这一行会一次性把整本 PDF 的所有页都解码为 PIL Image 列表。对于 461 页 / 80MB 的 GB150 PDF，单次调用会加载约 5-6 GB 内存，直接 OOM。

**修复**：改用 `pdfinfo` CLI 子进程取总页数（只读 metadata，几 KB 内存）。

```python
# ❌ 错误: 一次性加载所有页只为取页数
total = len(convert_from_path(str(pdf_path), dpi=dpi))

# ✅ 正确: pdfinfo 子进程, 只读 metadata
result = subprocess.run(['pdfinfo', str(pdf_path)], capture_output=True, text=True)
total = 0
for line in result.stdout.split('\n'):
    if line.startswith('Pages:'):
        total = int(line.split(':', 1)[1].strip())
        break
```

**触发条件**：任何 `--ocr` 模式 + PDF 页数 > 150 / 文件 > 20MB。

**验证**：461 页 GB150 PDF 跑 200 DPI OCR 全本（30-60 分钟），峰值 RSS 稳定在 ~150-200 MB（vs 修复前 5-6 GB 直接 OOM）。

---

## 补丁 2：`process_pdf.py` 索引格式兼容（重要）

**症状**：`process_pdf.py --search "<关键词>"` 在条目数 > 1 的索引上崩溃：

```
KeyError: 'txt_path'
```

**根因**：`cmd_search()` 函数硬编码 `info["txt_path"]`，但历史索引条目分两种格式：

- **新格式**（`process_pdf_batch.py` 写入）：`{"txt_path": "...", "extracted_txt": "...", ...}`
- **旧格式**（早期人工或迁移脚本写入）：`{"file": "...txt", "size": ..., "lines": ..., "chars": ..., "encoding": "utf-8"}`

**修复**：3 级 fallback 兼容新旧两种格式（详见源码 `cmd_search` 函数）。

**未来规则**：新写脚本时，所有 `info[...]` 字段访问都应 `info.get("...", default)` + 三级 fallback，**不要硬编码单一字段名**。

---

## 补丁 3：环境依赖

**Python wrapper**（在 `/home/hermes-admin/venv`）：
```bash
uv pip install --python /home/hermes-admin/venv/bin/python pytesseract pdf2image
```

**系统包**（tesseract 二进制 + 中文简体语言包）：
- `tesseract-ocr tesseract-ocr-chi-sim` (apt)
- `poppler-utils`（提供 pdftoppm、pdfinfo）

⚠️ 若是新机器或新 venv，**先装这三个系统包**再装 Python wrapper。

---

## OCR 任务最佳实践

**前置**：
1. 探页数：`pdfinfo` → 461 页
2. 探文件类型：先 `pdftotext -l 3` 看字符数（>200 = 文字型，可直接提取；<200 = 扫描版，必须 OCR）
3. 备份旧 extracted：`.OBSOLETE-<date>` 后缀保留作史鉴

**跑**：
- 单本：`process_pdf_batch.py --file "<pdf>" --ocr --dpi 200`
- 全本：`process_pdf_batch.py --all --ocr --dpi 200`
- 后台跑：terminal `background=true, notify_on_complete=true`，避免阻塞会话

**质量校验**：
```bash
# 抽查特定页内容
awk '/第 50 页/,/第 51 页/' extracted/<file>.txt

# 关键术语命中数（必须 > 0 才算 OCR 成功）
grep -c "开孔补强" extracted/<file>.txt
```

**索引更新**：`process_pdf_batch.py` 自动写 `index.json`，无需手工。
