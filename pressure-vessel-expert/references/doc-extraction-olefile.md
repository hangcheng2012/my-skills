# .doc 文件文本提取（olefile + UTF-16LE）

## 背景

标准文件有时以 Word 97-2003 格式（`.doc`，非 `.docx`）分发。  
`process_pdf.py` 脚本无法处理 `.doc`，`textract` 需要外部工具（`antiword`/`catdoc`），
且群晖环境无 root 权限，无法 `apt-get install`。

## 可用方案

### 方案A：olefile + UTF-16LE 直接解析（推荐，无需额外依赖）

`.doc` 文件内部是 OLE/COM 结构，文本存储在 `WordDocument` 流中，以 **UTF-16LE** 编码。

```python
import olefile, re

doc_bytes_name = b'GB 50341-20XX...doc'   # 文件名含 surrogate pair，必须用 bytes 路径

ole = olefile.OleFileIO(doc_bytes_name)
word_stream = ole.openstream('WordDocument').read()
ole.close()

# 扫描 UTF-16LE 字符序列
text_parts = []
i = 0
buffer = bytearray()
in_text = False

while i < len(word_stream) - 1:
    lo, hi = word_stream[i], word_stream[i+1]
    w = (hi << 8) | lo

    # 有效字符：ASCII 可打印、中文、常用标点
    if (0x0020 <= w <= 0x007E) or (0x3000 <= w <= 0x303F) or \
       (0x4E00 <= w <= 0x9FFF) or (0xFF00 <= w <= 0xFFEF):
        if not in_text:
            in_text = True
        buffer.append(lo)
        buffer.append(hi)
    else:
        if in_text and len(buffer) >= 4:
            text = buffer.decode('utf-16le', errors='replace').strip()
            text = re.sub(r'\s+', ' ', text)
            if is_valid_text(text):          # 自定义过滤
                text_parts.append(text)
            buffer = bytearray()
        in_text = False
        buffer = bytearray()
    i += 2

def is_valid_text(t):
    if len(t) < 3: return False
    chinese = sum(1 for c in t if '\u4e00' <= c <= '\u9fff')
    if chinese >= len(t) * 0.3: return True
    ascii_p = sum(1 for c in t if c.isprintable() and not c.isspace())
    if ascii_p >= len(t) * 0.7 and len(t) > 5: return True
    return False

# 去重保序
seen = set()
cleaned = []
for t in text_parts:
    t2 = ' '.join(t.split())
    if t2 not in seen and is_valid_text(t2):
        seen.add(t2)
        cleaned.append(t2)

with open('output.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(cleaned))
```

**输出结果**（GB 50341-20XX 实测）：
- 4,671 个文本段落
- 约 116,750 字符，含约 84,000 中文字符
- 文件大小 296 KB

### 方案B：uv pip install textract（需要系统工具）

```bash
uv pip install textract

# textract 自动调用 antiword（需提前安装）
python3 -c "import textract; print(textract.process('file.doc'))"
```

**注意**：此方案依赖 `antiword` / `wvWare` 等系统命令，无 root 时不可用。

### 方案C：LibreOffice headless（最通用但环境可能无此工具）

```bash
soffice --headless --convert-to txt:"Text" file.doc
```

## 文件名含 surrogate pair 的处理

中文文件名在 bytes 模式下用 `surrogateescape` 编码：

```python
# 正确
with open(doc_bytes_name, 'rb') as f:   # bytes 路径
    data = f.read()

# 错误（混用 str/bytes）
os.path.join(cwd, doc_str)   # ❌ surrogate pair 会破坏
```

获取 bytes 文件名：
```python
import os
files = os.listdir('.')
doc = [f for f in files if f.lower().endswith('.doc')]
for f in doc:
    b = f.encode('utf-8', errors='surrogateescape')
    print(f'bytes: {repr(b)}')   # 复制此 bytes 字面量备用
```

## 判断 .doc 是否值得处理

```python
import olefile
ole = olefile.OleFileIO(doc_bytes_name)
try:
    word_stream = ole.openstream('WordDocument').read()
    ole.close()
    size_kb = len(word_stream) / 1024
    print(f"WordDocument 流: {size_kb:.0f} KB")
    # >500 KB 的 .doc 通常内容丰富
except:
    print("不是有效 .doc 或无 Word 流")
```

## 关键经验

| 问题 | 解决方案 |
|------|---------|
| textract 报 FileNotFoundError: antiword | 用方案A（olefile）绕过 |
| 中文文件名无法在 str 路径打开 | 用 bytes 路径 |
| 无 root 无法 apt-get install | 用 uv pip 或方案A |
| .doc 内部是 UTF-16LE 非 ANSI | 必须用 UTF-16LE 解码 |
| 提取结果有乱码段落 | 用 `is_valid_text()` 过滤 |
