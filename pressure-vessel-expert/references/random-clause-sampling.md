# 知识库随机抽样工作流

## 何时用

用户要求"随机给我两条标准条文"、"随机抽一条"、"从知识库随机选一条"等场景。

## 工作流

### 步骤 1：确认 extracted/ 有文件

```python
import os
files_dir = '/home/hermes-admin/.hermes/skills/engineering/pressure-vessel-expert/knowledge/extracted'
all_files = [f for f in os.listdir(files_dir) if f.endswith('.txt')]
print(f"Total files: {len(all_files)}")
```

### 步骤 2：扫描英文/双语文件（按 EN ratio 定位）

文件名编码已损坏（如 `\udca2\udcf8`），不能靠文件名判断语言。扫描前 500 字符的英文字母比例：

```python
import re
high_en_files = []
for i, f in enumerate(all_files):
    path = os.path.join(files_dir, f)
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            first_500 = fh.read(500)
        eng_count = len(re.findall(r'[A-Za-z]', first_500))
        total = len(re.findall(r'\w', first_500))
        eng_ratio = eng_count / max(total, 1)
        if eng_ratio >= 0.90:
            high_en_files.append((i, f, eng_ratio))
    except:
        pass
```

### 步骤 3：构造候选集（带章节编号的正规条文）

```python
import re, random

def find_good_clauses(path, min_word_count=12):
    with open(path, 'r', encoding='utf-8') as fh:
        lines = fh.readlines()
    candidates = []
    for i, line in enumerate(lines):
        s = line.strip()
        if len(s) < 70:
            continue
        english_chars = len(re.findall(r'[A-Za-z]', s))
        if english_chars < 60:
            continue
        # 必须有章节编号，如 5.1、4.3.2、3.11.4.1
        if not re.search(r'\b\d+\.\d+', s):
            continue
        # 公式过多的行跳过
        formula_ratio = len(re.findall(r'[=<>+\-*/\d]', s)) / max(len(s), 1)
        if formula_ratio > 0.25:
            continue
        word_count = len(re.findall(r'[A-Za-z]{4,}', s))
        if word_count < min_word_count:
            continue
        candidates.append((i+1, s))
    return candidates
```

### 步骤 4：抽样并输出

```python
# API 650 英语版（索引 #11）
api_file = all_files[11]
candidates = find_good_clauses(os.path.join(files_dir, api_file))
clause = random.choice(candidates)

print(f"[标准名称], Line {clause[0]}")
print(f'"{clause[1]}"')
print(f"\n**译文：**[翻译内容]\n**出处：** [标准号], Line {clause[0]}")
```

## 输出格式模板

```
=== CLAUSE ===
[标准名称, 版本, Line N]
"英文原文"

**译文：**
[翻译内容]

**出处：** [标准号] [版本], Line [行号]
```

## 已知 EN ratio ≥ 90% 的文件索引

| 索引 | 标准 | EN% | 备注 |
|------|------|-----|------|
| #11 | API-Std-650-13th2020.03-钢制焊接石油储罐En.txt | 97% | API 650 英文版 |
| #15 | TEMA 11th 2023.txt | 100% | 管壳式换热器规范 |
| #7 | ASME Section I 2025 | 94% | 锅炉规范 |
| #8 | ASME BPVC Section IX 2025 | 95% | 焊接评定标准 |
| #16 | ASME BPVC Section III Div 1 | 92% | 核容器 |
| #22 | ASME BPVC Section VIII-2 2025 | 98% | 压力容器分析设计 |
| #18 | API-Std-650-13th2020.03-钢制焊接石油储罐En (变体) | 95% | 同 #11 另一副本 |

## 陷阱

- **不要用文件名判断语言**：extracted/ 文件名编码已损坏
- **不要用 index.json 的 base64 key 匹配文件**：key 与实际文件名无法对应
- **不要筛选含大量数学符号的行**：公式行会淹没正常条文
- **不要选 EN ratio < 90% 的文件抽英文条款**：抽到的几乎全是乱码或数字表格
