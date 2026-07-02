#!/usr/bin/env python3
"""
承压圈型式选择验证脚本 (仁信 90 kPa 项目复盘)
=================================================================
Sir 2026-06-04 加: 算承压圈前**必先确认设计选型** (型 a/b vs 型 f),
不要"想当然用 L75×10 默认". 错用型式 → 富余完全失真.

本脚本演示:
  - 型 a/b (角钢/包边, 默认) 在 90 kPa 工况下**不足**
  - 型 f (罐壁加厚+顶板延伸, PV 实测) **富余 55%**

用法:
  python3 verify_compression_ring_type.py
"""
import sys
import os

# 允许从同目录导入主计算脚本
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calc_shell_compression_ring import calc


def main():
    # 仁信 90 kPa 项目公共参数
    COMMON = dict(
        D=6500, H=10210, H_a=9450, rho=659.6, p_a=0.09, T=80,
        S_a=189, phi=0.75, CA=2, n_courses=5,
    )

    print("=" * 72)
    print("承压圈型式选择验证 — 仁信 90 kPa 项目 (Sir 2026-06-04)")
    print("=" * 72)
    print("\n关键提醒: 算承压圈前必先看设计图, 确认型 a/b 还是型 f!")
    print("         错用型式 → 富余完全失真 (型 a 算 17% 富余 vs 型 f 实测 55%)\n")

    # === 型 a/b (角钢/包边) — 默认, 旧算法 ===
    print("-" * 72)
    print("型 a/b: 角钢/包边 (假设用 L75×10 角钢 + 8mm 顶板)")
    print("-" * 72)
    r_a = calc(**COMMON, ring_type='a', tq=8, td=8, verbose=False)
    b4 = r_a['B.4']
    print(f"  Q = {b4['Q_kN']:.2f} kN")
    print(f"  Ae_req = {b4['Ae_req']:.0f} mm²")
    print(f"  A_t (含角钢) = {b4['A_t_with_L75']:.0f} mm²")
    print(f"  富余 = {b4['A_t_with_L75']/b4['Ae_req']:.2f}×")
    print(f"  校核: {'✓ 满足' if b4['satisfies'] else '✗ 不足 (与 PV 实测选型不符!)'}")
    print(f"  ⚠️  90 kPa 工况下型 a/b 通常不满足, 需加大或改型")

    # === 型 f (罐壁加厚+顶板延伸) — PV 实测 ===
    print("\n" + "-" * 72)
    print("型 f: 罐壁加厚+顶板延伸 (PV 仁信实测选型)")
    print("-" * 72)
    r_f = calc(**COMMON, ring_type='f',
               t_c=15.7, t_h=15.7, h_thick=200, b_ext=450, L_ext=150,
               R_2=5200, T1_roof=231.17, T2_roof=240.74, T2s_shell=322.98,
               phi_eff=0.547, verbose=False)
    b4f = r_f['B.4']
    print(f"  几何: 罐壁加厚 200×15.7, 顶板延伸 450×150 (t=15.7)")
    print(f"  W_c = {b4f['W_c']:.2f}, W_h = {b4f['W_h']:.2f}, L_h = {b4f['L_h']}")
    print(f"  有效面积: A_c = {b4f['A_c']:.0f}, A_h = {b4f['A_h']:.0f}, A_t = {b4f['A_t']:.0f} mm²")
    print(f"  Q = {b4f['Q_kN']:.2f} kN")
    print(f"  Ae_req (φ_eff=0.547) = {b4f['Ae_req']:.0f} mm²")
    print(f"  富余 = {b4f['A_t_over_Ae']:.2f}×")
    print(f"  校核: {'✓ 满足' if b4f['satisfies'] else '✗ 不足'}")

    print("\n" + "=" * 72)
    print("结论:")
    print(f"  型 a/b: {b4['A_t_with_L75']/b4['Ae_req']*100-100:+.1f}% 富余 (PV 未选此型)")
    print(f"  型 f:   {b4f['A_t_over_Ae']*100-100:+.1f}% 富余 (PV 选型)")
    print("  → 算承压圈前必先看设计图, 不要默认型 a/b!")
    print("=" * 72)


if __name__ == '__main__':
    main()
