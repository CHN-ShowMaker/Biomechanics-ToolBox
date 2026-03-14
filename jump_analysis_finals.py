# -*- coding: utf-8 -*-
"""
原地纵跳分析脚本 (适配3.0核心模块，包含曲线保存)
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

def analyze_countermovement_jump(c3d_file_path, output_dir='.', export_opensim=False):
    acq = c3d_utils.read_c3d(c3d_file_path)
    print("文件读取成功！")
    print("="*30)

    force_dict, fs = c3d_utils.get_force_data(acq, c3d_file_path)
    force_raw = force_dict['Fz']
    print(f"垂直力采样率: {fs} Hz")

    force_raw = np.abs(force_raw)
    force_filt = c3d_utils.lowpass_filter(force_raw, fs)
    time = np.arange(len(force_filt)) / fs

    # ---------- 保存归一化曲线 ----------
    interp_func = interpolate.interp1d(time, force_filt, kind='cubic', fill_value='extrapolate')
    norm_time = np.linspace(0, 100, 101)
    norm_force = interp_func(norm_time / 100 * time[-1])
    curve_path = os.path.join(output_dir, os.path.basename(c3d_file_path).replace('.c3d', '_curve.npy'))
    np.save(curve_path, norm_force)

    threshold = config.JUMP_THRESHOLD_RATIO * np.max(force_filt)
    in_flight = force_filt < threshold
    flight_starts = np.where(np.diff(in_flight.astype(int)) == 1)[0] + 1
    flight_ends = np.where(np.diff(in_flight.astype(int)) == -1)[0] + 1

    if len(flight_starts) == 0 or len(flight_ends) == 0:
        print("未检测到腾空区间，可能不是跳跃动作")
        return None

    takeoff_frame = flight_starts[0]
    landing_frame = flight_ends[0]

    pre_window = min(200, takeoff_frame)
    segment_before = force_filt[takeoff_frame - pre_window : takeoff_frame]
    takeoff_peak_frame = takeoff_frame - pre_window + np.argmax(segment_before)
    takeoff_peak_force = force_filt[takeoff_peak_frame]

    post_window = min(200, len(force_filt) - landing_frame)
    segment_after = force_filt[landing_frame : landing_frame + post_window]
    landing_peak_frame = landing_frame + np.argmax(segment_after)
    landing_peak_force = force_filt[landing_peak_frame]

    flight_time = (landing_frame - takeoff_frame) / fs

    events = {
        '离地': takeoff_frame,
        '落地': landing_frame,
        '起跳峰值': takeoff_peak_frame,
        '落地冲击': landing_peak_frame,
    }
    save_path = os.path.join(output_dir, os.path.basename(c3d_file_path).replace('.c3d', '_cmj.png'))
    plot_utils.plot_force_with_events(force_filt, fs, events, '原地纵跳分析', save_path)

    if export_opensim:
        trc_path = os.path.join(output_dir, os.path.basename(c3d_file_path).replace('.c3d', '_markers.trc'))
        mot_path = os.path.join(output_dir, os.path.basename(c3d_file_path).replace('.c3d', '_grf.mot'))
        try:
            c3d_to_trc(c3d_file_path, trc_path)
            c3d_to_grf_mot(c3d_file_path, mot_path)
            print("OpenSim 文件导出成功")
        except Exception as e:
            print(f"OpenSim 导出失败: {e}")

    raw_folder = os.path.dirname(c3d_file_path)
    result = {
        '文件名': os.path.basename(c3d_file_path),
        '动作类型': '原地纵跳',
        '起跳峰值力_N': takeoff_peak_force,
        '腾空时间_s': flight_time,
        '落地冲击力_N': landing_peak_force,
        '离地帧': takeoff_frame,
        '落地帧': landing_frame,
    }
    excel_path = os.path.join(raw_folder, '原地纵跳累计版.xlsx')
    excel_utils.append_to_excel(result, excel_path)

    return result

if __name__ == '__main__':
    test_file = r'你的测试文件路径.c3d'
    test_output = '.'
    res = analyze_countermovement_jump(test_file, test_output, export_opensim=config.EXPORT_OPENSIM)
    if res:
        print("分析完成，结果：", res)