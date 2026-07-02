# 罐壁内侧底部锚固加强环 — 文献汇总（Sir 2026-06-22 调研）

> **重要前提**：这种构造**不在 GB 50341 / SH/T 3167 / API 650 / API 620 / ASME 任一标准中**。
> 属于**设计院特批**的非标构造，主要用于**高地震烈度 + 短锚栓座 + 大型储罐**工况。
> 本文件汇总学术论文和工业实践，供后续类似项目参照。

---

## 0. 参考图纸归档（仁信 90 kPa 己烷储罐锚栓座）

| 项 | 内容 |
|----|------|
| **图源** | Sir 2026-06-25 提供（CAD 截图） |
| **归档路径** | `references/renxin-90kPa-anchor-chair-detail.jpg` (172 KB, 720×1280) |
| **图面类型** | 罐壁外侧**短锚栓座 (short anchor bolt chair)** II-II 剖视图 |
| **所属项目** | 仁信 90 kPa 己烷储罐（6.5m × 10.2m，SH/T 3167 + SY/T 0608 + API 620） |
| **关联算书** | `pressure-vessel-expert/references/renxin-hexane-tank-sht3167-90kPa.md`（§5.12 锚栓 6 工况） |

### 0.1 图面标号判读

| 标号 | 部件 | 关键尺寸 / 备注 |
|------|------|---------------|
| 18 | 锚栓顶部（M48 锚栓 + 螺母 + 垫板） | 与 6.5m 罐径 × 20 根锚栓方案匹配 |
| 11、12、13 | 锚栓座顶板附件（垫圈/止动件） | — |
| 14 | **锚栓座顶板**（与罐壁焊接） | 厚 14 mm，宽 100 mm |
| 15、16 | **加筋板 / 锚栓座侧板**（gusset stay） | 把锚栓力分散到罐壁 |
| 6O-Ø50 | 顶板 6×Ø50 孔 | 螺母/垫圈配合或注浆排气孔 |
| — | 锚栓座高度 ≈ 508 mm | 短锚栓座 (h_chair ≈ 0.5 m) |
| — | 锚栓中心 → 罐底间隙 50 mm | 灌浆空间 |
| — | 罐壁开孔 ØB200 + Ø1332×2 (壳径) | 与 6.5m 罐径一致 |

### 0.2 关键观察（与文献对应）

- **短锚栓座 (h ≈ 508 mm)** 形态 → 命中 SGH/SMiRT 25 (2019) 4.1 节"小偏心 + 短锚栓座"工况，**罐壁局部应力**是控制点
- **未设内部加强环**（与第 7 节工程实践表结论一致：仁信项目 PVdesktop 用 stiffened chair + 抗剪板，未设内加强环）
- **图面只有外侧锚栓座**，无内加强环 → 印证第 3 节"标准条款缺失"判断
- **后续要做的事**（Sir 06-25 立标）：
  1. 拉 Troitsky 模型 + 4.1 节 SGH 文献，**复核底圈 T1=137.2 MPa / 利用率 96.8%** 是否过临界
  2. 若临界 → 候选加固方案：①加厚底圈 ②加大承压圈 ③**局部内加强环**（每锚栓 ±400 mm L100×100×8）

### 0.3 调用本图的工作流

- 任何仁信项目锚栓座细节校核：先 `view renxin-90kPa-anchor-chair-detail.jpg` 看图面构造
- Troitsky 估算 → 见第 4.4 节公式
- CBFEM 验证 → 见第 4.5 节 + 5.4 节
- 推覆 (pushover) → 见第 4.1 节 SGH/SMiRT 25

---

---

## 1. 构造定义

**罐壁内侧底部锚固加强环** (Internal Anchor Reinforcement Ring at Shell Base):

```
                          ┌─── 罐顶 ───┐
                          │            │
              ┌───────────┤  罐壁       │
              │ 内部加强  │  (5~7 圈)   │  ← 锚栓座位置
              │ 环角钢 ───┤  底圈 10mm  │     ↑
              │ (整圈)    │  ────────── │     │
              │           │   罐底 10mm  │     │
              └───────────┴──────────────┘  ← 基础环梁
                       │
                  16-M48 锚栓
                  + 外侧锚固座
```

- **位置**：罐壁**内侧**底部，锚栓座高度处（通常距罐底 200~500mm）
- **形式**：**整圈连续角钢**（L 型，沿圆周满焊）
- **方向**：角钢长肢贴罐壁，短肢朝向罐内
- **规格**（基于工程经验 + 文献综合）：
  - D=15~30m: L75×75×6 ~ L100×100×8
  - D=30~50m: L100×100×8 ~ L125×125×10
  - D=50~80m: L125×125×10 ~ L150×150×12
  - D>80m: L150×150×12 + 补强板

---

## 2. 何时设置（触发条件）

| 场景 | 工况 | 典型工程背景 |
|------|------|------------|
| ① **大型储罐 + 强风** | D ≥ 30m 或 H ≥ 18m，ω₀ ≥ 0.5 kPa | 沿海/内陆大风区 |
| ② **高地震烈度 + 锚固承载** | 抗震 ≥ 8 度（0.20g）+ 锚栓承载型 + D ≥ 20m | 核电厂、战略储备库 |
| ③ **低压储罐/微内压储罐 + 锚固** | p_a = 5~18 kPa（GB 50341 附录 A）+ D ≥ 15m | 浮力工况锚栓承载 |
| ④ **大型浮顶储罐** | 5万m³、10万m³ 浮顶罐 | API 650 / GB 50341 抗风圈 + 内加强 |

**力学目的**（4 个）：
1. 把单点锚固应力沿圆周分散为"线载荷"
2. 防止底圈罐壁在锚固点处局部屈曲
3. 抵抗罐内液压 / 温度应力
4. 抗风/抗震加强（与外侧抗风圈形成"夹心"加强）

---

## 3. 标准定位（确认非标）

| 标准 | 章节 | 名称 | 位置 |
|------|------|------|------|
| **GB 50341-2014** | 附录 B.5 | **底部加强圈** | 罐壁**外侧**底部 |
| GB 50341-2014 | 6.4 | 抗风圈（顶部+中间） | 罐壁**外侧** |
| API 650 | 5.10.5 | Intermediate/Top Wind Girder | 罐壁**外侧** |
| API 620 | 5.10.5 | Stiffening Ring | 罐壁**外侧** |
| SH/T 3167 | 6.4 | 抗风圈/加强圈 | 罐壁**外侧** |
| **内部锚固加强环** | — | **无标准条款** | 罐壁**内侧**底部 |

> **Sir 2026-06-22 确认**：标准的"加强圈/抗风圈"几乎都在罐壁**外侧**。
> 图纸上确实是**内侧、一整圈角钢**，则属项目特批。

---

## 4. 关键文献

### 4.1 SGH/SMiRT 25 (2019) — 短锚栓座抗震评估

| 项 | 内容 |
|----|------|
| **标题** | Seismic Fragility Evaluation of Metal Flat-Bottom Storage Tanks with Short Anchor Bolt Chairs |
| **作者** | Abhinav Anup, Ho Jung Lee, Philip Hashimoto, Robert Kennedy |
| **机构** | Simpson Gumpertz & Heger Inc. (Newport Beach, CA) |
| **会议** | 25th Conference on Structural Mechanics in Reactor Technology (SMiRT 25), Charlotte, NC |
| **PDF** | https://repository.lib.ncsu.edu/bitstreams/696c7efe-6727-47cb-8008-73ca0ca53893/download |

**核心结论**：
- 标准 EPRI (1991) 方法**过保守** — 非线性分析揭示真实承载力是 EPRI 预测的 **2 倍**
- **短锚栓座**（h_chair 较小）罐壁局部承载受限
- **小偏心**（锚栓中心线靠近罐壁）→ 罐壁局部应力降低
- **大偏心**（传统锚栓座高 h_chair=300~500mm）→ 罐壁应力集中
- 失效模式判为**延性**而非 EPRI (1994) 的"非延性"
- → **当锚栓座高度不足时, 罐壁内侧需补强**（增加 h_chair 或加内加强环）

**SGH/SMiRT 25 (2019) 第二篇** — 环墙基础锚固储罐抗震易损性:
- 网址: https://repository.lib.ncsu.edu/bitstreams/b2f3ac60-6556-4aa6-b7b0-832f4af2aa05/download
- 核心: 环墙基础上, 罐体倾覆能力受管嘴位移限制 (1.3 in), 非罐壁屈曲
- **SAP2000 推覆 (pushover) 模型**: 罐壁壳单元 + 锚栓弹簧 + 环墙梁单元

### 4.2 EPFL WCEE2012 — Shell-to-Base 连接疲劳分析

| 项 | 内容 |
|----|------|
| **标题** | Fatigue Analysis of Unanchored Steel Liquid Storage Tank Shell-to-Base Connections during Earthquake Induced Uplift |
| **作者** | G.S. Prinz, A. Nussbaumer, G. Cortes (EPFL 洛桑联邦理工) |
| **PDF** | https://www.iitk.ac.in/nicee/wcee/article/WCEE2012_1121.pdf |

**模型**:
- 轴对称有限元 (CAX4R, ABAQUS)
- 罐底边界：铰接 + 弹簧（Winkler-Pasternak 模拟土壤）
- Reinforcing Ring 厚度 = 12 mm（与罐底板同厚度）
- 焊趾圆角 = 1 mm（避免几何突变）

**关键发现**:
- 疲劳断裂起源于**焊趾上方母材**（远离 HAZ）
- Reinforcing Ring 显著降低 shell-to-base 连接的低周疲劳损伤
- Eurocode 8 (1998) 限值 0.2 rad 偏保守

### 4.3 API 650 Ballot 650-1121 — FEA 替代方法

| 项 | 内容 |
|----|------|
| **标题** | Using FEA as an Alternate Method to Verify Anchorage Requirements Due to High Seismic Loads |
| **类型** | API 650 官方征求意见稿 |
| **核心** | 高地震荷载下, 允许用 FEA 替代 EPRI 传统方法 |

**替代方法适用条件**:
- 高地震设防（如核电厂 SPRA）
- 传统公式保守度过高
- 业主同意

**替代方法内容**:
- 3D 实体单元 + 非线性材料
- 静力 pushover / 动力时程
- 校核：罐壁局部应力 + 整体稳定性 + 锚栓应力

### 4.4 Troitsky 局部应力模型（经典）

| 项 | 内容 |
|----|------|
| **来源** | Petroblog "Cálculo de Anel de Ancoragem" (PDF: https://www.petroblog.com.br/wp-content/uploads/C%C3%A1lculo-de-Anel-de-ancoragem.pdf) |
| **核心理念** | "Chair must be high enough to distribute anchor bolt load to shell or column without overstressing it" |

**局部应力公式**:
```
σ_circ (罐壁周向) = F_bolt × h_chair / (Z_eff × D)
其中: Z_eff = t² × √(D·t) / 2.6

σ_bend (弯曲) = ± 6 × F_bolt × e / (t² × π × √(D·t))
其中: e = h_chair − t_shell/2  (锚栓中心到罐壁中线偏心)
```

**校核**: σ_circ + σ_bend ≤ [σ]_shell

### 4.5 ScienceDirect 论文（2015）— 锚栓座处局部应力 3 方法

| 项 | 内容 |
|----|------|
| **标题** | Determination of localized stresses in the shell above anchor bolt chairs attachments of anchored storage tanks |
| **期刊** | Thin-Walled Structures (Elsevier) |
| **链接** | https://www.sciencedirect.com/science/article/abs/pii/S0263823115301427 |

**三种方法**:
1. **数学方程** (Troitsky 模型)
2. **应力线性化** (ASME VIII-2 5.5.2)
3. **应力外推** (ASME VIII-2 应力外推法)

---

## 5. 计算模型与方法选择

### 5.1 快速估算（Troitsky 数学方程）

适用：初步设计、单锚栓座局部应力估算

```
输入: F_bolt, h_chair, t_shell, D
输出: σ_circ, σ_bend
校核: σ_circ + σ_bend ≤ S_a × φ
```

### 5.2 应力线性化（ASME VIII-2）

适用：API 620 高压罐、核电容器

```
路径: P1, P2, P3, P4 沿罐壁厚度取 4 条应力路径
线性化: P_m (膜应力), P_b (弯曲应力)
校核: P_m ≤ S_m; P_m + P_b ≤ 1.5 S_m
```

### 5.3 应力外推（峰值应力）

```
路径: P_a (内表面), P_b (t/4 处), P_c (t/2 中线)
外推至表面: σ_surface
校核: σ_peak ≤ 3 S_m
```

### 5.4 CBFEM（构件有限元）

来源: STRUCTURE Magazine, Richard T. Morgan
https://www.structuremag.org/article/analysis-of-anchoring-attachments-using-finite-element-modeling

```
建模:
  锚栓: 仅受拉弹簧
  混凝土: Winkler-Pasternak 受压弹簧
  焊缝: 板单元间连接约束
  内加强环: 板壳单元

分析:
  ① 锚栓受力
  ② 焊缝应力
  ③ 罐壁局部应力
  ④ 加固前后对比
```

### 5.5 非线性 Pushover (SGH 法)

```
模型: SAP2000 / ABAQUS
  - 罐壁: 壳单元（含锚栓座 + 内加强环）
  - 锚栓: 仅受拉弹簧 k = EA/L
  - 罐底: 受压弹簧（土壤 + 液体压载）
  - 阻尼: 2% (固定基础)

加载: 位移控制 pushover, 每步校核
输出: 推覆曲线 + 极限上拔容量 vs 地震需求
```

---

## 6. 规格推荐（综合工程经验 + 文献）

| 罐径 D | 内加强环规格 | 沿壁向长度 | 焊接 | 检验 |
|--------|------------|----------|------|------|
| 15~30 m | L75×75×6 或 12mm 补强板 | 每锚栓 ±300mm 局部 | 双面角焊 K=6mm | 100% MT + 20% UT |
| 30~50 m | L100×100×8 或 16mm 补强板 | 每锚栓 ±500mm 局部 | 双面角焊 K=8mm | 100% MT + 20% UT |
| 50~80 m | L125×125×10 或 20mm 补强板 | **整圈连续** | 双面角焊 K=10mm | 100% MT + 20% UT |
| > 80 m | L150×150×12 + 25mm 补强板 + 立板 | **整圈连续** | 双面角焊 K=12mm + 间断塞焊 | 100% MT + 100% UT |

**焊接要求**:
- 角钢与罐壁：双面连续角焊缝
- 角钢对接：整圈对接接头错开 ≥ 500mm，K 形坡口全焊透
- 距焊缝最小距离：150mm
- 排液孔（如果水平铺板）：16~20mm

**与锚栓座错开**:
- 锚栓座（外侧）位置必须与内加强圈错开
- 避免焊接应力集中

---

## 7. 国内工程实践案例

| 项目 | 罐径 | 介质 | 设计压力 | 风/地震 | 是否设内加强环 | 来源 |
|------|------|------|---------|---------|--------------|------|
| 仁信 (Renxin) | 6.5m | 己烷 | 90 kPa | 7 度 0.15g | **未设**（PVdesktop 用 stiffened chair + 抗剪板） | 2026-06-04 仁信算例 |
| 中石油某 5万m³ 浮顶 | ~60m | 原油 | 常压 | 沿海 0.85 kPa | **未设**（仅外侧抗风圈） | — |
| 中石化某 10万m³ | ~80m | 原油 | 常压 | 7 度 | **外侧设加强环** | — |
| 国内 90 kPa 大型低压罐 | ~10m | 高 RVP 介质 | 90 kPa | 7 度 | **个别设**（项目特批） | 行业经验 |

> **结论**：国内常规工程**不设**内部加强环，靠外侧抗风圈 + 锚栓座详设 + 加厚底圈解决。
> **仅在**特定工况（D > 50m + 强震/强风 + 锚栓承载）**才特批**内部加强环。

---

## 8. Sir 待决问题（仁信项目）

1. **是否需要内部加强环**？
   - 当前 90 kPa + D=6.5m → 不属于"必须设"工况
   - 但 PVdesktop 显示底圈 T1=137.2 MPa 利用率 96.8% → 需要加固
   - 加固方案：加厚底圈（有限）/ 加大承压圈（减小 T1）/ 内加强环（综合）

2. **如果设**：
   - 规格：L100×100×8 + 12mm 补强板（每锚栓 ±400mm 局部）
   - 计算方法：CBFEM 或 Pushover 验证

3. **如果不设**：
   - 接受底圈 T1 高利用率（96.8%）
   - 或改设计（如降 p_a 至 80 kPa）

---

*整理：Sir 2026-06-22 调研*
*用途：后续类似项目（非标特批构造）参照模板*
*下次遇到锚栓座详设问题，先看本文件第 4 节（关键文献），再展开*