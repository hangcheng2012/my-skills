# 知识库图像处理与 OCR 技巧

## vision_analyze 故障时的 tesseract OCR 备选方案

Telegram 图片上传后存在 `/home/hermes-admin/.hermes/image_cache/`（文件名 `img_*.jpg`），`file` 命令确认为合法 JPEG，但 `vision_analyze` 工具经常返回空结果或报错 "I don't see any image attached"。

**备选工作流**：直接用 tesseract OCR，不依赖 vision 工具。

```python
import subprocess
result = subprocess.run(
    ['tesseract', '/home/hermes-admin/.hermes/image_cache/img_XXXXX.jpg',
     'stdout', '-l', 'chi_sim+eng', '--psm', '6'],
    capture_output=True, text=True, timeout=30
)
print(result.stdout)
```

- `--psm 6`：假设均匀分布的块文本，对中文技术文档效果最好
- `chi_sim+eng`：简体中文 + 英文混合识别
- 依赖：系统安装 tesseract binary（`apt install tesseract-ocr`），Python 端 `pip install pytesseract`

## 添加新 OCR 内容到知识库

### 1. 保存 txt 文件

文件名用纯 ASCII（避免编码问题）：
```
knowledge/extracted/<ascii-name>.txt
```

### 2. 生成 index.json key

```python
import base64
key = base64.b64encode(b"<ascii-filename-without-txt>").decode('ascii')
```

### 3. 更新 index.json

⚠️ **encoding 陷阱**：原有 index.json 保存为 `latin-1`（因历史 garbled bytes），必须用 `encoding='latin-1'` 读写，否则 UTF-8 解码报错 `0xed`：

```python
with open('knowledge/index.json', 'r', encoding='latin-1') as f:
    index = json.load(f)

index[key] = {
    "file": "<filename.txt>",
    "size": <os.path.getsize>,
    "lines": <line count>,
    "chars": <char count>
}

with open('knowledge/index.json', 'w', encoding='latin-1') as f:
    json.dump(index, f, ensure_ascii=False, indent=2)
```
