# -*- coding: utf-8 -*-
"""
跑动双腿跳分析脚本 (适配4.0核心模块，支持多力板，长格式输出)
功能：读取C3D，获取所有力板数据，遍历每块力板进行分析，
      检测腾空、起跳合力峰、落地冲击，计算腾空时间，保存曲线。
      注意：本脚本输出每块力板的原始数据（不求和），
      用户可在Excel中自行求和或单独分析。
      累积Excel输出为长格式：每个力板一行，包含文件名、动作类型、侧别、板号及各指标。
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

def analyze_double_leg_jump(c3d_file_path, output_dir='.', export_opensim=False):
    print("\n" + "="*50)
    print(f"开始分析跑动双腿跳文件: {os.path.basename(c3d_file_path)}")
    print(f"Starting double-leg jump analysis: {os.path.basename(c3d_file_path)}")
    print("="*50)

    acq = c3d_utils.read_c3d(c3d_file_path)
    print("文件读取成功！File loaded successfully!")

    plates_data, fs = c3d_utils.get_force_data(acq, c3d_file_path)
    num_plates = len(plates_data)
    print(f"检测到 {num_plates} 块力板，采样率: {fs} Hz")
    print(f"Detected {num_plates} force plate(s), sampling rate: {fs} Hz")

    if num_plates == 0:
        print("错误：未获取到任何力板数据，终止分析。/ Error: No force plate data, aborting.")
        return None

    # 读取配置文件以获取侧别信息
    config_data = c3d_utils.get_project_config(c3d_file_path)
    plates_config = config_data.get('plates', [])

    all_results = []  # 存储每个力板的结果

    for plate_idx, plate_dict in enumerate(plates_data):
        # 从配置中获取该板的侧别，若无则默认为 unknown
        if plate_idx < len(plates_config):
            side = plates_config[plate_idx].get('side', 'unknown')
        else:
            side = 'unknown'

        # 侧别显示用中英文
        side_display = {'right': '右脚 Right', 'left': '左脚 Left', 'unknown': '未知 Unknown'}.get(side, '未知 Unknown')

        print(f"\n--- 力板 {plate_idx+1} ({side_display}) ---")
        force_raw = plate_dict['Fz']
        if np.all(force_raw == 0):
            print(f"  警告：力板 {plate_idx+1} 垂直力全零，跳过。/ Warning: Plate {plate_idx+1} Fz all zero, skipping.")
            continue

        force_raw = np.abs(force_raw)
        force_filt = c3d_utils.lowpass_filter(force_raw, fs)
        time = np.arange(len(force_filt)) / fs

        # 保存归一化曲线（按侧别分类）
        interp_func = interpolate.interp1d(time, force_filt, kind='cubic', fill_value='extrapolate')
        norm_time = np.linspace(0, 100, 101)
        norm_force = interp_func(norm_time / 100 * time[-1])
        curve_subdir = os.path.join(output_dir, 'curves', side)
        os.makedirs(curve_subdir, exist_ok=True)
        curve_filename = os.path.basename(c3d_file_path).replace('.c3d', f'_plate{plate_idx+1}_curve.npy')
        curve_path = os.path.join(curve_subdir, curve_filename)
        np.save(curve_path, norm_force)
        print(f"  归一化曲线已保存: {curve_path} / Normalized curve saved.")

        # 检测腾空区间
        threshold = config.JUMP_THRESHOLD_RATIO * np.max(force_filt)
        in_flight = force_filt < threshold
        flight_starts = np.where(np.diff(in_flight.astype(int)) == 1)[0] + 1
        flight_ends   = np.where(np.diff(in_flight.astype(int)) == -1)[0] + 1

        if len(flight_starts) == 0 or len(flight_ends) == 0:
            print("  未检测到腾空区间，可能不是跳跃动作 / No flight phase detected. Possibly not a jump.")
            continue  # 跳过此力板

        takeoff_frame = flight_starts[0]
        landing_frame = flight_ends[0]
        print(f"  检测到腾空区间：离地帧 {takeoff_frame}，落地帧 {landing_frame}")
        print(f"  Flight phase detected: takeoff frame {takeoff_frame}, landing frame {landing_frame}")

        # 起跳合力峰检测
        pre_window = min(config.JUMP_PRE_WINDOW, takeoff_frame)
        segment_before = force_filt[takeoff_frame - pre_window : takeoff_frame]
        takeoff_peak_frame = takeoff_frame - pre_window + np.argmax(segment_before)
        takeoff_peak_force = force_filt[takeoff_peak_frame]
        print(f"  起跳合力峰: {takeoff_peak_force:.1f} N，帧号 {takeoff_peak_frame}")
        print(f"  Takeoff resultant peak: {takeoff_peak_force:.1f} N, frame {takeoff_peak_frame}")

        # 落地冲击峰检测
        post_window = min(config.JUMP_POST_WINDOW, len(force_filt) - landing_frame)
        segment_after = force_filt[landing_frame : landing_frame + post_window]
        landing_peak_frame = landing_frame + np.argmax(segment_after)
        landing_peak_force = force_filt[landing_peak_frame]
        print(f"  落地冲击峰: {landing_peak_force:.1f} N，帧号 {landing_peak_frame}")
        print(f"  Landing impact peak: {landing_peak_force:.1f} N, frame {landing_peak_frame}")

        flight_time = (landing_frame - takeoff_frame) / fs
        print(f"  腾空时间: {flight_time:.3f} s / Flight time: {flight_time:.3f} s")

        # 绘图（按侧别分类）
        events = {
            '离地 Takeoff': takeoff_frame,
            '落地 Landing': landing_frame,
            '起跳合力峰 Takeoff peak': takeoff_peak_frame,
            '落地冲击峰 Landing peak': landing_peak_frame,
        }
        img_subdir = os.path.join(output_dir, 'images', side)
        os.makedirs(img_subdir, exist_ok=True)
        img_filename = os.path.basename(c3d_file_path).replace('.c3d', f'_plate{plate_idx+1}_double_jump.png')
        save_path = os.path.join(img_subdir, img_filename)
        plot_utils.plot_force_with_events(
            force=force_filt,
            fs=fs,
            events=events,
            title=f'双腿跳分析 (力板 {plate_idx+1} - {side_display}) / Double‑Leg Jump (Plate {plate_idx+1} - {side_display})',
            save_path=save_path
        )
        print(f"  力曲线图已保存至: {save_path} / Force curve plot saved.")

        # 构建该力板的结果字典（长格式）
        result_row = {
            '文件名 Filename': os.path.basename(c3d_file_path),
            '动作类型 Movement type': '跑动双腿跳 Double‑leg jump',
            '侧别 Side': side,
            '板号 Plate': plate_idx + 1,
            '起跳合力峰_N Takeoff resultant peak (N)': takeoff_peak_force,
            '腾空时间_s Flight time (s)': flight_time,
            '落地冲击峰_N Landing impact peak (N)': landing_peak_force,
            '离地帧 Takeoff frame': takeoff_frame,
            '落地帧 Landing frame': landing_frame,
        }
        all_results.append(result_row)

    # OpenSim 导出（仍只导出第一块力板，保持简单）
    if export_opensim and plates_data:
        trc_path = os.path.join(output_dir, os.path.basename(c3d_file_path).replace('.c3d', '_markers.trc'))
        mot_path = os.path.join(output_dir, os.path.basename(c3d_file_path).replace('.c3d', '_grf.mot'))
        try:
            c3d_to_trc(c3d_file_path, trc_path)
            c3d_to_grf_mot(c3d_file_path, mot_path, plate_index=0)
            print("OpenSim 文件导出成功 (第一块力板) / OpenSim files exported (first plate)")
        except Exception as e:
            print(f"OpenSim 导出失败: {e} / OpenSim export failed: {e}")

    # 将所有力板的结果逐行追加到累积Excel
    raw_folder = os.path.dirname(c3d_file_path)
    excel_path = os.path.join(raw_folder, '双腿跳累计版 Double‑leg cumulative.xlsx')
    for row in all_results:
        excel_utils.append_to_excel(row, excel_path)
    print(f"\n已追加 {len(all_results)} 行结果至: {excel_path} / Appended {len(all_results)} rows to: {excel_path}")

    return all_results

if __name__ == '__main__':
    test_file = r'你的测试文件路径.c3d'
    test_output = '.'
    res = analyze_double_leg_jump(test_file, test_output, export_opensim=config.EXPORT_OPENSIM)
    if res:
        print("分析完成，共 {} 块力板。".format(len(res)))