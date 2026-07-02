# 压力容器专家 — 知识库

将标准 PDF 文件放入 `standards/` 目录，运行处理脚本即可提取文本并建立索引。

**支持文本型 PDF 和扫描版 PDF（自动 OCR）。**

## 目录结构

```
knowledge/
├── README.md
├── standards/   ← 放置 PDF 标准文件（GB150、ASME、API 650 等）
├── extracted/   ← 自动生成的纯文本（不要手动修改）
└── index.json   ← 知识库索引（自动维护）
```

## 环境准备

### 基础依赖（文本型 PDF）

```bash
pip install pdfplumber
```

### OCR 依赖（扫描版 PDF）

扫描版 PDF 需要额外安装 Tesseract OCR：

```bash
# Python 包
pip install pytesseract pdf2image Pillow

# 系统工具 + 中文语言包
apt install tesseract-ocr tesseract-ocr-chi-sim poppler-utils
```

检查环境是否就绪：

```bash
python3 scripts/process_pdf.py --check
```

## 使用方式

### 1. 添加 PDF 标准文件

将 PDF 标准放入 `knowledge/standards/`:

```
knowledge/standards/
├── GB150-2024.pdf
├── GB50341-2014.pdf
├── ASME_VIII-1_2023.pdf
└── API_650_2020.pdf
```

### 2. 提取文本并建立索引

```bash
# 默认模式（自动识别文本/扫描版）
python3 scripts/process_pdf.py

# 强制 OCR 模式（全部走 OCR）
python3 scripts/process_pdf.py --ocr

# 控制 OCR 质量（默认 400 dpi 质量优先，调低可提速）
python3 scripts/process_pdf.py --ocr --ocr-dpi 300

# 处理单个文件
python3 scripts/process_pdf.py --file knowledge/standards/GB150-2024.pdf

# 重新索引（清空后重新提取）
python3 scripts/process_pdf.py --reindex
```

### 3. 查看已索引的文档

```bash
python3 scripts/process_pdf.py --list
```

### 4. 搜索知识库

```bash
# 搜索关键词（带上下文行）
python3 scripts/process_pdf.py --search "开孔补强"

# 或用 grep 直接搜索
grep -rn "设计压力" knowledge/extracted/
```

## 提取策略

脚本会自动选择最优方式：

| 策略 | 适用场景 | 速度 |
|------|---------|------|
| pdfplumber | 文字型 PDF（直接提取） | ⚡ 快 |
| pdftotext | pdfplumber 失败的备选 | ⚡ 快 |
| Tesseract OCR | 扫描版 PDF（自动识别） | 🐢 慢，但能处理 |

**自动降级逻辑**：如果直接提取的文本少于 200 字符，说明是扫描件，自动切换 OCR。

**强制 OCR**：用 `--ocr` 跳过文本提取，直接走 OCR 管道。

## 支持的标准

- **中国标准**: GB150, GB151, GB50341, GB50128, NB/T 47041, NB/T 47042, HG/T 20580~20585
- **国际标准**: ASME Section VIII, API 650, API 620, API 2000

## OCR 识别精度说明

- Tesseract 对印刷体中英文混合内容识别率较高（>95%）
- 表格区域和特殊符号可能有少量乱码（~1-3%）
- 默认 400 DPI 质量优先，如需提速可降至 300