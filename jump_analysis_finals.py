# -*- coding: utf-8 -*-
"""
原地纵跳分析脚本 (适配3.0核心模块，双语版)
功能：读取C3D，检测腾空、起跳峰值、落地冲击，计算指标，绘图，可选导出OpenSim文件，
      并自动保存结果到Excel汇总表。
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import config
import c3d_utils
import plot_utils
import excel_utils
from c3d_to_opensim_finals import c3d_to_trc, c3d_to_grf_mot

plot_utils.setup_chinese_font()

def analyze_countermovement_jump(c3d_file_path, output_dir='.', export_opensim=False):
    # 1. 读取C3D并获取力通道
    acq = c3d_utils.read_c3d(c3d_file_path)
    print("文件读取成功！File loaded successfully!")
    print("="*30)

    force_dict, fs = c3d_utils.get_force_data(acq, c3d_file_path)
    force_raw = force_dict['Fz']  # 垂直力
    print(f"垂直力采样率: {fs} Hz / Vertical force sampling rate: {fs} Hz")

    # 2. 预处理力信号
    force_raw = np.abs(force_raw)
    force_filt = c3d_utils.lowpass_filter(force_raw, fs)
    time = np.arange(len(force_filt)) / fs

    # 3. 检测腾空区间
    threshold = config.JUMP_THRESHOLD_RATIO * np.max(force_filt)
    in_flight = force_filt < threshold
    flight_starts = np.where(np.diff(in_flight.astype(int)) == 1)[0] + 1
    flight_ends   = np.where(np.diff(in_flight.astype(int)) == -1)[0] + 1

    if len(flight_starts) == 0 or len(flight_ends) == 0:
        print("未检测到腾空区间，可能不是跳跃动作 / No flight phase detected. Possibly not a jump movement.")
        return None

    takeoff_frame = flight_starts[0]
    landing_frame = flight_ends[0]
    print(f"检测到腾空区间：离地帧 {takeoff_frame}，落地帧 {landing_frame}")
    print(f"Flight phase detected: takeoff frame {takeoff_frame}, landing frame {landing_frame}")

    # 4. 起跳峰值（离地前200帧内最大值）
    pre_window = min(200, takeoff_frame)
    segment_before = force_filt[takeoff_frame - pre_window : takeoff_frame]
    takeoff_peak_frame = takeoff_frame - pre_window + np.argmax(segment_before)
    takeoff_peak_force = force_filt[takeoff_peak_frame]
    print(f"起跳峰值力: {takeoff_peak_force:.1f} N，帧号 {takeoff_peak_frame}")
    print(f"Takeoff peak force: {takeoff_peak_force:.1f} N, frame {takeoff_peak_frame}")

    # 5. 落地冲击（落地后200帧内最大值）
    post_window = min(200, len(force_filt) - landing_frame)
    segment_after = force_filt[landing_frame : landing_frame + post_window]
    landing_peak_frame = landing_frame + np.argmax(segment_after)
    landing_peak_force = force_filt[landing_peak_frame]
    print(f"落地冲击力: {landing_peak_force:.1f} N，帧号 {landing_peak_frame}")
    print(f"Landing impact force: {landing_peak_force:.1f} N, frame {landing_peak_frame}")

    # 6. 腾空时间
    flight_time = (landing_frame - takeoff_frame) / fs
    print(f"腾空时间: {flight_time:.3f} s / Flight time: {flight_time:.3f} s")

    # 7. 绘图
    events = {
        '离地 Takeoff': takeoff_frame,
        '落地 Landing': landing_frame,
        '起跳峰值 Takeoff peak': takeoff_peak_frame,
        '落地冲击 Landing impact': landing_peak_frame,
    }
    save_path = os.path.join(output_dir,
                             os.path.basename(c3d_file_path).replace('.c3d', '_cmj.png'))
    plot_utils.plot_force_with_events(
        force=force_filt,
        fs=fs,
        events=events,
        title='Countermovement Jump Analysis 原地纵跳分析',
        save_path=save_path
    )
    print(f"力曲线图已保存至: {save_path} / Force curve plot saved to: {save_path}")

    # 8. 导出OpenSim
    if export_opensim:
        trc_path = os.path.join(output_dir, os.path.basename(c3d_file_path).replace('.c3d', '_markers.trc'))
        mot_path = os.path.join(output_dir, os.path.basename(c3d_file_path).replace('.c3d', '_grf.mot'))
        try:
            c3d_to_trc(c3d_file_path, trc_path)
            c3d_to_grf_mot(c3d_file_path, mot_path)
            print("OpenSim 文件导出成功 / OpenSim files exported successfully")
        except Exception as e:
            print(f"OpenSim 导出失败: {e} / OpenSim export failed: {e}")

    # 9. 保存结果
    raw_folder = os.path.dirname(c3d_file_path)
    result = {
        '文件名 Filename': os.path.basename(c3d_file_path),
        '动作类型 Movement type': '原地纵跳 Countermovement jump',
        '起跳峰值力_N Takeoff peak force (N)': takeoff_peak_force,
        '腾空时间_s Flight time (s)': flight_time,
        '落地冲击力_N Landing impact force (N)': landing_peak_force,
        '离地帧 Takeoff frame': takeoff_frame,
        '落地帧 Landing frame': landing_frame,
    }
    excel_path = os.path.join(raw_folder, '原地纵跳累计版 CMJ cumulative.xlsx')
    excel_utils.append_to_excel(result, excel_path)
    print(f"结果已追加至: {excel_path} / Results appended to: {excel_path}")

    return result

if __name__ == '__main__':
    test_file = r'你的测试文件路径.c3d'
    test_output = '.'
    res = analyze_countermovement_jump(test_file, test_output, export_opensim=config.EXPORT_OPENSIM)
    if res:
        print("分析完成，结果：", res)