#!/usr/bin/env python3
"""
SH/T 3167 + SY/T 0608 低压储罐 罐壁+承压圈 计算
=================================================================
由 sht-3167-shell-compression-ring skill 提供

用法:
    from calc_shell_compression_ring import calc
    result = calc(D=6500, H=10200, H_a=9450, rho=659.6, p_a=0.09, T=80)
    print(result)

或者命令行:
    python calc_shell_compression_ring.py D=6500 H=10200 H_a=9450 rho=659.6 p_a=0.09 T=80
"""
import math
import json
import sys

# ============================================================
# 默认参数 (SH/T 3167 算例 0.02 MPa 乙二醇罐)
# ============================================================
DEFAULTS = {
    'D': 16400,           # 内直径 (mm)
    'H': 10000,           # 罐壁高度 (mm)
    'H_a': 9000,          # 最高液位 (mm)
    'rho': 1100,          # 介质密度 (kg/m³)
    'p_a': 0.02,          # 设计压力 (MPa)
    'T': 20,              # 设计温度 (℃)
    'S_a': 137,           # 许用应力 (MPa, S30408 @ 20℃)
    'phi': 0.75,          # 焊缝系数 (SH/T 3167 默认, Sir 校对)
    'CA': 0,              # 腐蚀裕量 (不锈钢 0, 碳钢 2)
    'R_roof_factor': 0.85,# 拱顶半径系数 (0.85D, API 620 K.2.2)
    'tq': 8.0,            # 顶板厚度 (mm, 型 a/b 用)
    'td': 8.0,            # 顶圈罐壁厚度 (mm, 型 a/b 用)
    'n_courses': 7,       # 分圈数
    'E': 2.06e5,          # 弹性模量
    'nu': 0.3,            # 泊松比
    'g': 9.81,            # 重力加速度
    'rho_steel': 7850,    # 钢密度
    # 承压圈型式 (Sir 2026-06-04 增)
    'ring_type': 'a',     # 'a'/'b' (角钢/包边, 默认) 或 'f' (罐壁加厚+顶板延伸)
    't_c': 15.7,          # 型 f: 顶部罐壁有效厚 (mm)
    't_h': 15.7,          # 型 f: 顶板有效厚 (mm)
    'h_thick': 200,       # 型 f: 罐壁加厚段高 (mm)
    'b_ext': 450,         # 型 f: 顶板延伸段宽 (mm)
    'L_ext': 150,         # 型 f: 顶板外伸长度 (mm)
    'R_2': 5200,          # 型 f: 罐顶法向半径 (mm)
    'T1_roof': 231.17,    # 型 f: 罐顶经向力 (N/mm², 正压)
    'T2_roof': 240.74,    # 型 f: 罐顶纬向力 (N/mm², 正压)
    'T2s_shell': 322.98,  # 型 f: 罐壁纬向力 (N/mm², 正压)
    'phi_eff': 0.7,       # 型 f: 焊缝组合效率 (PV 校核 0.547, SH/T 3167 严 0.7)
}


def calc(D=None, H=None, H_a=None, rho=None, p_a=None, T=None, S_a=None,
         phi=None, CA=None, R_roof=None, tq=None, td=None, n_courses=None,
         E=None, nu=None, g=None, rho_steel=None, R_roof_factor=None,
         ring_type=None, t_c=None, t_h=None, h_thick=None, b_ext=None,
         L_ext=None, R_2=None, T1_roof=None, T2_roof=None, T2s_shell=None,
         phi_eff=None, verbose=True):
    """
    SH/T 3167 + SY/T 0608 罐壁+承压圈 完整计算

    返回 dict: {B.2, B.3, B.4, geometry}
    """
    # 合并参数 (用户提供优先, 否则用默认)
    p = DEFAULTS.copy()
    user_args = {k: v for k, v in locals().items() if v is not None and k != 'p' and k != 'verbose'}
    p.update(user_args)

    D = p['D']; H = p['H']; H_a = p['H_a']; rho = p['rho']
    p_a = p['p_a']; T = p['T']; S_a = p['S_a']; phi = p['phi']; CA = p['CA']
    tq = p['tq']; td = p['td']; n_courses = p['n_courses']
    E = p['E']; nu = p['nu']; g = p['g']; rho_steel = p['rho_steel']

    R_inner = D / 2
    R_mid = R_inner + 5  # 估算 (中线)
    if R_roof is None:
        R_roof = p['R_roof_factor'] * D
    c = 0  # 顶部腐蚀裕量

    # 拱顶
    h_rise = R_roof - math.sqrt(R_roof**2 - (D/2)**2)
    alpha_deg = math.degrees(math.asin((D/2) / R_roof))
    sin_alpha = math.sin(math.radians(alpha_deg))
    cos_alpha = math.cos(math.radians(alpha_deg))

    # === 自由体总重力 (估算) ===
    # V in m³, ρ in kg/m³, m = V·ρ kg, W = m·g N
    V_liq = math.pi * R_inner**2 * H_a / 1e9  # mm³ → m³
    W_liquid = V_liq * rho * g
    t_shell_avg = (tq + td) / 2  # mm
    # V_shell (m³) = π·D(m)·H(m)·t(m) = π·(D/1000)·(H/1000)·(t/1000)
    W_shell = math.pi * (D/1000) * (H/1000) * (t_shell_avg/1000) * rho_steel * g
    A_roof_m2 = 2 * math.pi * R_roof * h_rise / 1e6  # mm² → m²
    W_roof = A_roof_m2 * (tq/1000) * rho_steel * g
    V_bottom = math.pi * (R_inner/1000)**2 * 0.008  # m³
    W_bottom = V_bottom * rho_steel * g
    W_attach = 0.05 * (W_shell + W_roof + W_bottom)
    W_total = W_liquid + W_shell + W_roof + W_bottom + W_attach

    # === B.2 单元力 (1-1 平面) ===
    Ae = math.pi * R_mid**2
    p_hydro_1_1 = rho * g * (H_a/1000) / 1e6
    p_total_1_1 = p_a + p_hydro_1_1
    T1 = (R_mid/2) * (p_total_1_1 - W_total/Ae)
    T2 = p_total_1_1 * R_mid

    if verbose:
        print(f"\n{'='*70}")
        print(f"SH/T 3167-2012 罐壁+承压圈计算")
        print(f"{'='*70}")
        print(f"D = {D} mm, H = {H} mm, H_a = {H_a} mm")
        print(f"ρ = {rho} kg/m³, p_a = {p_a} MPa, T = {T}℃")
        print(f"S_a = {S_a} MPa, φ = {phi}, CA = {CA} mm")
        print(f"\n[B.2 单元力] 1-1 平面")
        print(f"  p_hydro = {p_hydro_1_1*1000:.3f} kPa, p_total = {p_total_1_1*1000:.3f} kPa")
        print(f"  W_total = {W_total/1e3:.1f} kN, Ae = {Ae/1e6:.3f} × 10⁶ mm²")
        print(f"  T1 = {T1:.2f} N/mm² (轴向)")
        print(f"  T2 = {T2:.2f} N/mm² (环向 p·R)")

    # === B.3 罐壁分圈厚度 ===
    plate_width = H / n_courses
    courses = []
    if verbose:
        print(f"\n[B.3 罐壁 {n_courses} 圈 × {plate_width:.0f} mm]")
        print(f"{'圈号':<4} {'高 (mm)':<12} {'p_total':<10} {'T2':<10} {'t_calc':<8} {'t_选用':<6}")
    for i in range(n_courses, 0, -1):
        h_bot = min((i-1) * plate_width, H_a)
        h_top = min(i * plate_width, H_a)
        # 🚨 修复 (2026-06-04): 用 (H_a - h_bot) 反算"该圈底部液柱高度" = 水深
        # 旧版用 h_bot 错把"z 坐标"当水深, 导致底圈 p_h=0、顶圈 p_h 反而最大 (反向)
        h_liq_above = max(H_a - h_bot, 0)           # 该圈底部以上液柱高度 (mm)
        p_h = rho * g * (h_liq_above/1000) / 1e6    # MPa, 该圈底部的液柱静压
        p_t = p_a + p_h                              # 该圈底部总压力 (设计+静压)
        T2_i = p_t * R_mid                           # 该圈 T2 = p·R (用最大压力)
        t_calc = T2_i / (S_a * phi) + CA
        t_used = max(6, math.ceil(t_calc * 2) / 2)
        courses.append({'no': i, 'h_bot': h_bot, 'h_top': h_top,
                        'p_total': p_t, 'T2': T2_i,
                        't_calc': t_calc, 't_used': t_used})
        if verbose:
            print(f"{i:<4} {h_bot:>5.0f}~{h_top:>5.0f}  {p_t*1000:<10.2f} {T2_i:<10.2f} {t_calc:<8.2f} {t_used:<6.1f}")

    # === B.4 承压圈 ===
    # 承压圈型式 (Sir 2026-06-04 增加):
    #   'a' / 'b' (默认): 角钢/包边型 — Wh = 0.6√(R_roof·tq), Wc = 0.6√(R·td)
    #   'f':              罐壁顶部加厚 + 顶板延伸型 — Wh = 0.6√(R_2·t_h), Wc = 0.6√(R_c·t_c)
    ring_type = p.get('ring_type', 'a')
    if ring_type == 'f':
        # 型 f: 罐壁加厚 + 顶板延伸
        t_c = p.get('t_c', 15.7)            # 顶部罐壁有效厚 (mm)
        t_h = p.get('t_h', 15.7)            # 顶板有效厚 (mm)
        h_thick = p.get('h_thick', 200)     # 罐壁加厚段高 (mm)
        b_ext = p.get('b_ext', 450)         # 顶板延伸段宽 (mm)
        L_ext = p.get('L_ext', 150)         # 顶板外伸长度 (mm)
        R_2 = p.get('R_2', 5200)            # 罐顶法向半径 (mm)
        # 有效宽度
        W_c_f = 0.6 * math.sqrt(R_inner * t_c) if R_inner > 0 else 0
        W_h_f = 0.6 * math.sqrt(R_2 * t_h)
        L_h_f = L_ext
        # 有效面积
        A_c_f = W_c_f * t_c
        A_h_f = (W_h_f + L_h_f) * t_h
        A_t_f = A_c_f + A_h_f
        # 单元力 (按 PV 报告: 3 工况, 此处仅给正压控制值)
        # 用户可手动覆盖 T1_roof, T2_roof, T2s_shell
        T1_roof = p.get('T1_roof', 231.17)
        T2_roof = p.get('T2_roof', 240.74)
        T2s_shell = p.get('T2s_shell', 322.98)
        # 总环向力 Q (SH/T 3167 5.5.2.3-1, 型 f 适用)
        Q_f = T1_roof * W_h_f + T2_roof * W_c_f - T2_roof * R_inner * sin_alpha
        # 所需面积 (PV 用 φ_eff ≈ 0.547, 含焊缝组合效应; SH/T 3167 严, 用 0.7)
        phi_eff = p.get('phi_eff', 0.7)
        Ae_req_f = abs(Q_f) / (S_a * phi_eff)
        margin_f = A_t_f / Ae_req_f if Ae_req_f > 0 else float('inf')
        ring_result = {
            'type': 'f',
            'W_c': W_c_f, 'W_h': W_h_f, 'L_h': L_h_f,
            'A_c': A_c_f, 'A_h': A_h_f, 'A_t': A_t_f,
            'T1_roof': T1_roof, 'T2_roof': T2_roof, 'T2s_shell': T2s_shell,
            'Q_N': Q_f, 'Q_kN': Q_f/1000,
            'Ae_req': Ae_req_f, 'A_t_over_Ae': margin_f,
            'satisfies': A_t_f > Ae_req_f,
            'phi_eff': phi_eff,
        }
        if verbose:
            print(f"\n[B.4 承压圈 (型 f — 罐壁加厚+顶板延伸, SH/T 3167 5.5.3.4)]")
            print(f"  几何: 罐壁加厚 {h_thick}×t_c={t_c}, 顶板延伸 {b_ext}×{L_ext} (t={t_h})")
            print(f"  R_2 (罐顶法向半径) = {R_2} mm")
            print(f"  有效宽: W_c = {W_c_f:.2f}, W_h = {W_h_f:.2f}, L_h = {L_h_f}")
            print(f"  有效面积: A_c = {A_c_f:.1f}, A_h = {A_h_f:.1f}, A_t = {A_t_f:.1f} mm²")
            print(f"  单元力: T1_roof={T1_roof}, T2_roof={T2_roof}, T2s_shell={T2s_shell} N/mm²")
            print(f"  Q = {Q_f:.0f} N = {Q_f/1000:.2f} kN")
            print(f"  φ_eff = {phi_eff} (PV 校核值约 0.547, SH/T 3167 严取值 0.7)")
            print(f"  Ae_req = {Ae_req_f:.1f}, A_t/Ae = {margin_f:.2f}× {'✓ 满足' if A_t_f > Ae_req_f else '✗ 不足'}")
    else:
        # 型 a/b: 角钢/包边型 (默认, 旧公式)
        Wh = 0.6 * math.sqrt(R_roof * tq)
        Wc = 0.6 * math.sqrt(R_mid * td)
        T1_top = (R_mid/2) * (p_a - W_total/Ae)
        T2_top = R_mid * p_a - T1_top
        T3_top = R_mid * p_a
        Q = T1_top*Wh + T2_top*Wc - T3_top*R_mid*sin_alpha
        Ae_req = abs(Q) / (S_a * phi) if Q != 0 else 0
        At = (Wh + 150) * tq
        Ac = Wc * td
        A_t = At + Ac
        # 角钢面积 (L75x10, 1 个)
        A_L75 = 2*75*10 - 100  # =1400 mm²
        # 实际总有效 (含角钢, 如有)
        ring_result = {
            'type': 'a/b',
            'Wh': Wh, 'Wc': Wc, 'T1': T1_top, 'T2': T2_top, 'T3': T3_top,
            'Q_N': Q, 'Q_kN': Q/1000, 'Ae_req': Ae_req,
            'At': At, 'Ac': Ac, 'A_t': A_t,
            'A_L75': A_L75, 'A_t_with_L75': A_t + A_L75,
            'A_t_over_Ae': A_t/Ae_req if Ae_req > 0 else float('inf'),
            'satisfies': A_t > Ae_req,
        }
        if verbose:
            print(f"\n[B.4 承压圈 (型 a/b — 角钢/包边)]")
            print(f"  几何: Wh = {Wh:.2f} mm, Wc = {Wc:.2f} mm")
            print(f"  单元力 (局部 p = {p_a} MPa):")
            print(f"    T1 = {T1_top:.2f} N/mm², T2 = {T2_top:.2f}, T3 = {T3_top:.2f}")
            print(f"  Q = T1·Wh + T2·Wc − T3·R·sinα")
            print(f"    = {T1_top*Wh:.0f} + {T2_top*Wc:.0f} − {T3_top*R_mid*sin_alpha:.0f}")
            print(f"    = {Q:.0f} N = {Q/1000:.2f} kN")
            print(f"  Q {'< 0 → 需承压圈' if Q < 0 else '> 0 → 需抗拉环'}")
            print(f"  Ae_req = |Q|/(S_a·φ) = {Ae_req:.1f} mm²")
            print(f"  实际: At = {At:.1f}, Ac = {Ac:.1f}, A_t = {A_t:.1f} mm²")
            margin = A_t/Ae_req if Ae_req > 0 else float('inf')
            print(f"  富余 = {margin:.2f}× {'✓ 满足' if A_t > Ae_req else '✗ 不足!'}")

    return {
        'B.2': {
            'p_total_1_1': p_total_1_1, 'W_total': W_total, 'Ae': Ae,
            'T1': T1, 'T2': T2,
        },
        'B.3': {'n_courses': n_courses, 'plate_width': plate_width,
                'courses': courses},
        'B.4': ring_result,
        'geometry': {
            'D': D, 'H': H, 'H_a': H_a,
            'R_inner': R_inner, 'R_mid': R_mid, 'R_roof': R_roof,
            'h_rise': h_rise, 'alpha_deg': alpha_deg,
            'sin_alpha': sin_alpha, 'cos_alpha': cos_alpha,
            'tq': tq, 'td': td,
        },
        'inputs': p,
    }


if __name__ == '__main__':
    # 命令行: python calc_shell_compression_ring.py key=val key=val ...
    args = {}
    for a in sys.argv[1:]:
        if '=' in a:
            k, v = a.split('=', 1)
            try: args[k] = float(v) if '.' in v else int(v)
            except: args[k] = v
    result = calc(**args, verbose=True)
    print('\n--- JSON 输出 ---')
    print(json.dumps(result, ensure_ascii=False, indent=2))
