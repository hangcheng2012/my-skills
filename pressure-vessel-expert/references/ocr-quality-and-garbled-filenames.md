# OCR 质量与乱码文件名处理（2026-05-18）

## ⚠️ 重要: 单张图片 OCR 流程 (2026-06-04 新增)

**适用场景**: Telegram / 微信 / 截图推送的**单张技术标准页**识别 (非 PDF 批处理).

**步骤**:
```python
from PIL import Image
import subprocess

# 1. PIL 预处理: 3× 放大 + 灰度 + 300 DPI
img = Image.open('/path/to/image.jpg')
img = img.resize((img.width*3, img.height*3), Image.LANCZOS)
img = img.convert('L')
img.save('/tmp/enhanced.png', dpi=(300,300))

# 2. tesseract OCR (中文 + 英文, 块模式)
subprocess.run([
    'tesseract', '/tmp/enhanced.png', '/tmp/out',
    '-l', 'chi_sim+eng',  # 必须双语言, 否则下标英文会丢
    '--psm', '6'           # 6 = uniform block of text
])
```

**实测经验**:
- ✅ 中文段落识别率 >90%
- ✅ 公式中数字 + 中文字符识别良好
- ❌ 下标 (W₁/W₂/Aₑ/Tᵢ) OCR 经常丢失或错位 → 必须**领域知识手动还原**
- ❌ 希腊字母 (α, φ, ρ) OCR 容易错位
- ⚠️ 公式编号 (B.2-1) OCR 稳定, 段号识别准确

**关键参数说明**:
- `--psm 6`: 假设单页是均匀文本块 (uniform block of text). 适合标准页/教科书页
- `--psm 3`: 默认全页自动检测. 表格多的页面用这个
- `--psm 4`: 单列文本. 标准页通常不适合
- `-l chi_sim+eng`: 必须中英双语. 否则公式里的英文字母/下标会丢失

## ⚠️ 重要: vision_analyze 不可信 (2026-06-04 新增)

**踩坑**: 用 vision_analyze 识别 SH/T 3167-2012 附录 B P41 时, 工具**完全编造内容**, 把"2000m³ 乙醇罐"算例凭空改成"D=12m Q235-B 汽油罐"虚构算例. 整页文字、数字、公式全错.

**教训**:
- **必须用 tesseract OCR 拿到真实文字** (哪怕粗糙)
- 用**领域知识 (SH/T 3167 标准内容)** 手动校正 OCR 错位
- **不要把 vision_analyze 的"识别"当事实**, 须经 OCR 二次验证
- Sir 推送中文技术标准扫描页时, **默认走 OCR 流程, vision_analyze 仅作辅助**

## OCR 准确率实测（SYT 0608-2014，第 20 页对比）

**测试方法**：对同一 PDF 同一页同时做 OCR（pdf2image + pytesseract）和提取 TXT 文本，逐行对比。

**结论**：
- ✅ **中文正文段落**：识别准确率 >90%，专业术语正常
- ✅ **中文标题**（如 `4.5 结构型钢`、`5.1.4 气相空间`）：识别准确
- ❌ **英文加粗节号标题**（`5.1.2`、`5.1.3`）：100% 错（笔画粘连，扫描版通病）
- ⚠️ **数字/符号**：偶有多余字符（如 `2%%` 代替 `2%`）

**对知识库检索的影响**：可忽略——技术参数、公式、主体中文内容均正确索引。英文节号错不影响语义搜索结果。

## 乱码文件名处理

**症状**：standards/ 目录的 PDF 文件名含乱码（如 `SYT 0608-2014砟⿺ker诎琧d敹畊杮d戙攱剔.pdf`），无法正常 print/repr。

**根因**：PDF 目录在非 UTF-8 文件系统（NAS）上创建，中文文件名编码转换损坏，形成 Unicode surrogate 字符。

**定位方法**（永远不用文件名，用大小）：
```python
import os, glob
files_by_size = {}
for f in glob.glob('knowledge/standards/*.pdf'):
    sz = os.path.getsize(f)
    if sz not in files_by_size:
        files_by_size[sz] = []
    files_by_size[sz].append(f)

# 按大小定位（±100KB 容差）
for t in [int(27.5*1024*1024), int(8.3*1024*1024), int(8.0*1024*1024)]:
    for sz in files_by_size:
        if abs(sz - t) < 100*1024:
            print(f"Found: {sz//1024//1024}MB  path={files_by_size[sz][0]}")
```

**安全操作原则**：
1. 永远不 `print/repr` 含 surrogate 的文件名
2. 用 `hex()` 打印标识：`name[:15].encode('utf-8', errors='replace').hex()`
3. 用文件大小定位，不用文件名匹配
4. 输出文件名时用 hex 或 bytes 格式

**示例 hex 识别**：
- `53595420303630382d32303134` → "SYT 0608-2014"
- `534854333034362d32303234` → "SHT3046-2024"
- `53485420333037342d32303138` → "SHT 3074-2018"
