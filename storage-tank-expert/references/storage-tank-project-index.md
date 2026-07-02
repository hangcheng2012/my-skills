# 储罐项目计算书索引

> 本目录存放历史储罐设计算书（多为 PVdesktop 比对版），供后续类似项目快速参考。
> **新项目触发时**：直接 `search_files target=files path=.../references/` 找关键字相同的计算书。

## 计算书清单

| 文件 | 项目代号 | 设备类型 | 容积 | 设计压力 | 主要标准 | 状态 | 备注 |
|------|---------|---------|------|---------|---------|------|------|
| `3000m3-MTBE-internal-floating-roof-calculation-vs-PVdesktop.md` | 海尔希 3000m³ MTBE | 内浮顶+自支撑拱顶 | 3000 m³ | 5 kPa 常压 | SH/T 3046-2024 + GB 50341 + API 650 | ✅ v1.0 已完成 | **陕西榆林**，MTBE 介质 |
| `renxin-hexane-tank-sht3167-90kPa.md` | 仁信 粗溶剂罐 | 立式拱顶 | 300 m³ | 90 kPa 低压 | SH/T 3167 + SY/T 0608 + API 620 | ✅ v1.0 已完成 | 90 kPa 接近 API 620 上限，锚栓 6 工况 |
| `sht-3167-calculation-example.md` | SH/T 3167 标准算例 | 立式拱顶 | 2000 m³ | 20 kPa 低压 | SH/T 3167 + SY/T 0608 | 参考模板 | 乙醇，标准附录 B 完整算例 |
| `sh-t3167-low-pressure-tank-pitfalls.md` | — | 立式拱顶 | — | 低压 | SH/T 3167 + SY/T 0608 | 坑总结 | W1/W2 重量项 vs Wh/Wc 几何宽度 等 |
| `api-620-low-pressure-tank.md` | — | 立式拱顶 | — | 18~100 kPa | API 620 | 参考 | API 620 5.12.4 承压圈 + 90 kPa 工况 |
| `api620-compression-ring.md` | — | 立式拱顶 | D6.5m | 90 kPa | API 620 5.12.4 | 参考 | 承压圈（压缩环）详细设计 |
| `hexane-tank-sht3167-calculation.md.OBSOLETE-0.02MPa-error` | — | 立式拱顶 | — | 20 kPa | SH/T 3167 | ⚠️ 错误算例（已重命名保留作史鉴） | 0.02 MPa 错用为项目参数，整份废 |
| `anchor-bolt-reinforcement-pad.md` | — | 锚栓/补强圈 | — | — | NB/T 11025 | 参考 | 锚栓+补强圈选型 |
| `../sht-3167-shell-compression-ring/references/renxin-90kPa-anchor-chair-detail.jpg` | 仁信 90 kPa | 短锚栓座 II-II 剖视 | — | 90 kPa | API 620 + SH/T 3167 | 🖼️ 06-25 归档 | Sir 提供的参考图，详见 `internal-anchor-reinforcement-ring.md` §0 |
| `../sht-3167-shell-compression-ring/references/internal-anchor-reinforcement-ring.md` | — | 罐壁内加强环 | — | — | 非标（设计院特批） | 📚 文献汇总 | 仁信锚栓座详设主参考 |

## 关键项目参数对照（快速参考）

| 项目 | 容积 | D (mm) | H (mm) | P (kPa) | 介质 | 地区 | 抗震 | 锚栓 | 备注 |
|------|------|--------|--------|---------|------|------|------|------|------|
| 海尔希 MTBE | 3000 | 17000 | 15862 | 5 | MTBE 725 | 陕北 | 7度 0.10g II 类 | 24 M36 | ✅ 常压内浮顶自支撑拱顶 |
| 仁信 粗溶剂 | 300 | 6500 | 10210 | 90 | 己烷 | — | — | 20 M48 | ✅ 低压 API 620 拱顶 |
| SH/T 3167 例 | 2000 | — | — | 20 | 乙醇 | 惠州 | — | — | 📖 标准附录 B |

## 选取参考计算书的工作流

1. **新项目进来** → 确认压力范围（常压 P≤18 kPa / 低压 18<P≤100 kPa / 压力容器 P>0.1 MPa）
2. **确认业主行业**（石化 → SH/T 3046 或 SH/T 3167 主；其他 → 看合同）
3. **找对应计算书**：
   - 3000m³ 内浮顶自支撑拱顶常压 → `3000m3-MTBE-internal-floating-roof-calculation-vs-PVdesktop.md`
   - 90 kPa 拱顶 API 620 → `renxin-hexane-tank-sht3167-90kPa.md`
   - 2000m³ 拱顶低压 → `sht-3167-calculation-example.md`
4. **复用计算书的输入参数表、公式编号、单位约定**，但**禁止直接套算例参数到项目**（**算例≠项目铁律**）

## 计算书版本规则

- **v0.x**：草稿，可能含错误（参考 `hexane-tank-sht3167-calculation.md.OBSOLETE` 史鉴）
- **v1.0**：完整计算书，已与 PVdesktop 逐项比对
- 任何含 `.OBSOLETE-` 后缀的计算书**禁止作为参考**，仅作错误案例研究

---

*索引维护：2026-06-04*
