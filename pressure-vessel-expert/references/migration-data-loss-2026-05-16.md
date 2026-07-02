# 迁移数据丢失记录 — 2026-05-16

## 事件概述

2026-05-16 从 OpenClaw 迁移到 Hermes 时，`pressure-vessel-expert` 技能的知识库 OCR 提取文件全部丢失。

## 丢失内容

`index.json` 中记录的 17 个标准的 `.txt` 提取文件：

| PDF 源文件 | 提取方式 | 预期行数 | 状态 |
|-----------|---------|---------|------|
| API STD 620-2013 大型焊接低压储罐（中文版） | direct | 29,038 | ❌ 缺失 |
| API-Std-650-13th2020.03 钢制焊接石油储罐 | direct | 30,365 | ❌ 缺失 |
| API650-2020 焊接石油储罐（中英文对照） | direct | 44,532 | ❌ 缺失 |
| AQ 3063-2025 化工企业可燃液体常压储罐区安全 | direct | 2,148 | ❌ 缺失 |
| GBT 14976-2025 输送流体用不锈钢无缝钢管 | direct | 2,482 | ❌ 缺失 |
| **GBT 150.1~4-2024 压力容器** | **OCR** | 24,845 | ❌ 缺失 |
| **GBT 151-2026 热交换器** | **OCR** | 18,106 | ❌ 缺失 |
| GBT 4732.1~6-2024 压力容器分析设计 | direct | 34,593 | ❌ 缺失 |
| GBT 50128-2014 立式圆筒形钢制焊接储罐施工 | direct | 118 | ❌ 缺失（疑似空文件） |
| GBT 50341-2014 立式圆筒形钢制焊接油罐设计 | direct | 10,480 | ❌ 缺失 |
| GBT 9948-2025 石化和化工装置用无缝钢管 | direct | 3,112 | ❌ 缺失 |
| HGT 20678-2023 化工设备衬里钢壳设计 | direct | 2,069 | ❌ 缺失 |
| NBT 47041 塔式容器释义和算例 | direct | 20,034 | ❌ 缺失 |
| NBT 47041-2014 塔式容器 | direct | 6,840 | ❌ 缺失 |
| NBT 47042 卧式容器释义和算例 | direct | 11,148 | ❌ 缺失 |
| NBT 47042-2014 卧式容器 | direct | 2,441 | ❌ 缺失 |
| SHT 3075-2024 石油化工钢制压力容器材料 | direct | 3,035 | ❌ 缺失 |
| TEMA 11th 2023 | direct | 22,327 | ❌ 缺失 |

**注**：`GBT 150` 和 `GBT 151` 是通过 Tesseract OCR 识别的（非直接提取），丢失影响最大。

## 根因分析

1. **迁移工具局限性**：`hermes claw migrate` 仅迁移了技能目录结构、`SKILL.md`、`index.json` 元数据，未扫描迁移 `knowledge/extracted/` 子目录下的 `.txt` 文件
2. **源目录已清理**：迁移完成后，`/home/hermes-admin/openclaw-backup` 源目录已被删除，无法回溯原始提取文件
3. **备份目录无数据**：迁移备份目录 `/home/hermes-admin/.hermes/migration/openclaw/20260516T140331/backups/` 中也无 `.txt` 文件

## 恢复步骤

1. **确认 PDF 源文件位置**
   - 检查 NAS、云盘、本地其他备份
   - 原始 PDF 应在 `/home/hermes-admin/openclaw-backup/`（已不存在）

2. **如有 PDF 源文件**
   ```bash
   # 将 PDF 放入技能目录
   cp /path/to/GBT150.pdf ~/.hermes/skills/engineering/pressure-vessel-expert/knowledge/standards/

   # 重新 OCR 提取
   python3 ~/.hermes/skills/engineering/pressure-vessel-expert/scripts/process_pdf.py --ocr

   # 验证
   python3 ~/.hermes/skills/engineering/pressure-vessel-expert/scripts/process_pdf.py --check
   ```

3. **如 PDF 源文件也丢失**
   - 需重新获取标准文档（购买/下载）
   - 重新放入 `knowledge/standards/` 并运行提取

## 教训

- **迁移前必须验证**：迁移后应运行 `--check` 验证所有引用文件是否实际存在
- **OCR 文件需单独备份**：`.txt` 提取文件体积大（总计约 8MB+），迁移工具不会自动包含
- **index.json 可能"虚假繁荣"**：元数据存在 ≠ 数据存在，必须交叉验证
