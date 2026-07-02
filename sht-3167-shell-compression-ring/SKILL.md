---
name: sht-3167-shell-compression-ring
description: SH/T 3167 + SY/T 0608 低压储罐**罐壁分圈厚度 + 承压圈（压缩环）**专项计算。计算范围：B.1 自由体分析 + B.2 单元力 (T1/T2) + B.3 罐壁分圈厚度 + B.4 承压圈校核 (型 a/b 角钢、型 f 罐壁加厚+顶板延伸)。**仅做承压环计算，不含锚栓/抗风/地震/罐底**（由 `storage-tank-expert` 处理）。由 `storage-tank-expert` 自动调用。
version: 2.0.0
---

# 如何调用

**触发条件**：
- 用户给"低压储罐 / SH/T 3167 / 拱顶罐"等关键词
- storage-tank-expert 进入"罐壁分圈设计"步骤
- 用户要求"按 SH/T 3167 算承压圈 / 压缩环"

**不调用**：风载/地震/雪压、真空稳定、锚栓/螺栓、开孔补强、罐底（均由主 skill 处理）

# 完整设计输入

| 参数 | 符号 | 单位 | 默认值 | 来源 |
|------|------|------|--------|------|
| 内直径 | D | mm | (必填)| 工艺 |
| 罐壁高度 | H | mm | (必填)| 工艺 |
| 最高液位 | H_a | mm | (必填)| 工艺 |
| 介质密度 | rho | kg/m^3 | (必填)| 工艺 |
| 设计压力 | p_a | MPa | (必填)| 工艺 |
| 设计温度 | T | C | (必填)| 工艺 |
| 许用应力 | S_a | MPa | 189 (Q345R @ 80C) | 显式确认 |
| 焊缝系数 | phi | - | 0.75 | SH/T 3167 默认 |
| 腐蚀裕量 | CA | mm | 2 | 工艺介质 |
| 拱顶半径 | R_roof | mm | 0.85D | API 620 K.2.2 |
| 承压圈型式 | ring_type | - | a (角钢) / f (罐壁加厚+顶板延伸)| 构造设计 |


# 计算流程

```
输入参数 -> B.1 自由体分析 -> B.2 单元力 T1/T2 -> B.3 罐壁分圈厚度 -> B.4 承压圈校核 -> 输出
```

# 公式速查

## B.1 自由体分析

以罐体最下端的平面 1-1 作为给定水平面进行自由体分析。

## B.2 单元力计算

```
T1 = (R/2) x [p + (W+F)/Ae]   (B.2-1)
T2 = p x R                      (B.2-2)
```

**符号约定**：p 取正值（内压向上），(W+F) 取负值（重力向下）
**中间量**：p_total = p_a + p_hydro, W_total = W_liq + W_shell + W_roof + W_bottom, Ae = pi x R_mid^2

## B.3 罐壁分圈厚度

```
t = T2 / (S_a x phi) + CA   (B.3-1)
```

每圈以该圈底部最大压力计算，t_used = max(6mm, ceil(t_calc x 2)/2)

## B.4 承压圈校核

**型 a/b（角钢/包边）**：
```
Wh = 0.6 x sqrt(R_roof x tq)     (B.4-1)  罐顶参与宽
Wc = 0.6 x sqrt(R_mid x td)     (B.4-2)  罐壁参与宽
Q = T1xWh + T2xWc - T3xRxsin(alpha)    (B.4-6)
A_e = |Q| / (S_a x phi)         (B.4-11) 所需面积
A_t = At + Ac                           总有效面积
A_t >= A_e -> OK
```

**型 f（罐壁加厚+顶板延伸）**：
- 罐壁加厚段 h=200mm, d=18mm；顶板延伸 b=450mm, t=18mm, L=150mm
- 有效宽度 W_c=135.53mm, W_h=171.44mm
- 总有效面积 A=7536mm^2, A_req=4849mm^2 -> 富余+55%

**关键：算承压圈前必须先确认设计选型，不要默认 L75x10**

# 关键命名约定

| 本 skill 符号 | 含义 | 区别 |
|------|------|----------|
| Wh | 罐顶参与宽 (mm) | ≠ 标准 W1 (重量)|
| Wc | 罐壁参与宽 (mm) | ≠ 标准 W2 (重量)|
| T1 | 单元力 (轴向)| 单位力 N/mm^2 |
| T2 | 单元力 (环向 pR)| 单位力 N/mm^2 |
| T3 | 单元力 (Rp_a)| 单位力 N/mm^2 |


# 关键坑

## 坑 1: W1/W2 是重量项，不是几何宽度
几何宽度必须用 Wh/Wc（罐顶/罐壁参与宽），不要与标准 W1/W2 重量项混淆。

## 坑 2: 焊缝系数 phi = 0.75（不是 0.85）
SH/T 3167 默认 phi=0.75（局部 RT），GB 150/API 620 通常 0.85，差 13.3%。

## 坑 3: 自由体 (W+F) 重力方向取负
公式中的 (W+F) 代入负值，代数效果等效 p - |W+F|/Ae。

## 坑 4: Q 符号约定
Q < 0 -> 需承压圈（压缩环）；Q > 0 -> 需抗拉环（罕见）。

## 坑 5: Ae 双重含义
B.2 中 Ae = 罐壁横截面积 = pi x R^2_mid；B.4-11 中 Ae = 所需承压圈有效面积。

## 坑 6: 承压圈型式需确认
算承压圈前必须先确认设计选型（型 a/b/f），不要默认 L75x10。

## 坑 7: 算例参数 != 项目参数
每次计算前核对 5 项：P_design / V / 介质 / 材料 / 地点。标准算例只能作模板。

## 坑 8: B.3 层底最大压力
p_hydro_i = rho x g x (H_a - z_bot_i)，用 H_a 减 z_bot（不是直接用 z_bot）。

## 坑 9: 单位换算 H_a mm -> MPa 要 /1e9
p_hydro [MPa] = rho x g x H_a / 1e9（不是 /1e6）。

## 坑 10: Q345R @ 80C S_ts = 189 MPa
不用 159 MPa。温度对应值必须显式确认。

## 坑 11: CA 约定差异
SH/T 3167 公式含 CA：t = T2/(Sxphi) + CA；PVdesktop 不含 CA。

## 坑 12: 真空稳定（Von Mises 短圆筒）
p_cr = 2.6 x E x (t/2.65R)^2.5 / R，SF >= 3.0

## 坑 13: 底圈轴向膜应力（90 kPa 等级）
在高设计压力下，T1 轴向膜应力可能接近极限（96.8% util），必须专项校核。


# 参考文件

- `../storage-tank-expert/references/sht-3167-calculation-example.md` — SH/T 3167 完整算例
- `../storage-tank-expert/references/sh-t3167-low-pressure-tank-pitfalls.md` — 关键坑汇总
- `../storage-tank-expert/references/api-620-low-pressure-tank.md` — API 620 对比
- `./scripts/calc_shell_compression_ring.py` — 核心计算脚本
- `./scripts/verify_compression_ring_type.py` — 承压圈型式验证脚本

---

*子 skill，由 storage-tank-expert 自动调用。*
*创建：2026-06-04。版本：2.0.0（2026-07-01 精简）。*
