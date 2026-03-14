# -*- coding: utf-8 -*-
"""
步态分析脚本 (适配3.0核心模块，包含曲线保存)
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import interpolate

import config
import c3d_utils
import plot_utils
import excel_utils
from c3d_to_opensim_finals import c3d_to_trc, c3d_to_grf_mot

plot_utils.setup_chinese_font()

def analyze_gait(c3d_file_path, output_dir='.', export_opensim=False):
    acq = c3d_utils.read_c3d(c3d_file_path)
    print("文件读取成功！")
    print("="*30)

    force_dict, fs = c3d_utils.get_force_data(acq, c3d_file_path)
    force_raw = force_dict['Fz']
    print(f"垂直力采样率: {fs} Hz")

    force_raw = np.abs(force_raw)
    force_filt = c3d_utils.lowpass_filter(force_raw, fs)

    # ---------- 保存归一化曲线 ----------
    time = np.arange(len(force_filt)) / fs
    interp_func = interpolate.interp1d(time, force_filt, kind='cubic', fill_value='extrapolate')
    norm_time = np.linspace(0, 100, 101)
    norm_force = interp_func(norm_time / 100 * time[-1])
    curve_path = os.path.join(output_dir, os.path.basename(c3d_file_path).replace('.c3d', '_curve.npy'))
    np.save(curve_path, norm_force)

    # 事件检测
    hs, to = c3d_utils.detect_gait_events(force_filt, fs)
    threshold = config.GAIT_THRESHOLD_RATIO * np.max(force_filt)
    print(f"动态阈值 ({threshold:.1f} N) 检测到 {len(hs)} 次触地，{len(to)} 次离地")

    # 支撑时间
    if len(hs) > 0 and len(to) > 0:
        n_steps = min(len(hs), len(to))
        stance_times = (to[:n_steps] - hs[:n_steps]) / fs
        avg_stance = np.mean(stance_times)
        print(f"平均支撑时间: {avg_stance:.3f} s")
    else:
        avg_stance = None

    # 峰值力
    peak_force = np.max(force_filt)

    # 绘图
    events = {'触地': hs, '离地': to}
    save_path = os.path.join(output_dir, os.path.basename(c3d_file_path).replace('.c3d', '_gait.png'))
    plot_utils.plot_force_with_events(force_filt, fs, events, '步态事件检测', save_path)

    # OpenSim导出
    if export_opensim:
        trc_path = os.path.join(output_dir, os.path.basename(c3d_file_path).replace('.c3d', '_markers.trc'))
        mot_path = os.path.join(output_dir, os.path.basename(c3d_file_path).replace('.c3d', '_grf.mot'))
        try:
            c3d_to_trc(c3d_file_path, trc_path)
            c3d_to_grf_mot(c3d_file_path, mot_path)
            print("OpenSim 文件导出成功")
        except Exception as e:
            print(f"OpenSim 导出失败: {e}")

    # 累积Excel
    raw_folder = os.path.dirname(c3d_file_path)
    result = {
        '文件名': os.path.basename(c3d_file_path),
        '动作类型': '步态',
        '平均支撑时间_s': avg_stance,
        '峰值力_N': peak_force,
        '触地次数': len(hs),
        '离地次数': len(to),
        '阈值_N': threshold,
    }
    excel_path = os.path.join(raw_folder, '步态分析累计版.xlsx')
    excel_utils.append_to_excel(result, excel_path)
    print(f"结果已追加至 {excel_path}")

    return result

if __name__ == '__main__':
    test_file = r'你的测试文件路径.c3d'
    test_output = '.'
    result = analyze_gait(test_file, test_output, export_opensim=config.EXPORT_OPENSIM)
    print("分析完成，结果：", result)