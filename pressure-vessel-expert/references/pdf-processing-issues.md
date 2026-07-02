# PDF处理已知问题速查

## 依赖安装
两个包都必须装，缺一不可：
```bash
python3 -m pip install pytesseract pdf2image
sudo apt install tesseract-ocr tesseract-ocr-chi-sim
```
缺 `pdf2image` → `ModuleNotFoundError: No module named 'pdf2image'`
缺 `pytesseract` → 同理
`tesseract` CLI 必须系统级安装（不是 pip 包）

## index.json surrogate 双重编码

**症状**：中文件名字符在 `os.listdir()` 和 JSON key 中有不同 surrogate 编码 → key 永远不匹配。

**根因**：`surrogateescape` 在"读→写→读"循环中累积损坏。

**解法**：key 用 base64 编码（详见 `references/knowledge-base-recovery.md`）。

## 后台任务管理

| 操作 | 命令 |
|---|---|
| 启动 | `python3 scripts/process_pdf_batch.py --all --dpi 200`（background=true） |
| 看进度 | `ps aux \| grep tesseract \| grep -v grep`（tesseract 在跑=正常） |
| 杀主进程 | `process kill`（session_id） |
| 杀 orphan tesseract | `pkill -f "tesseract.*process_pdf"` |

**注意**：`--all` 跳过逻辑依赖 index 准确性，**永远只处理 missing PDF**，不跑 `--all`。
