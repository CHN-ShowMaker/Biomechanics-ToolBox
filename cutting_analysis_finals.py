# -*- coding: utf-8 -*-
"""
侧切分析脚本 (适配4.0核心模块，支持多力板，长格式输出)
功能：读取C3D，获取所有力板数据，遍历每块力板进行分析，
      检测冲击峰，计算峰值力和冲量，保存曲线。
      累积Excel输出为长格式：每个力板一行，包含文件名、动作类型、侧别、板号及各指标。
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy import interpolate

import config
import c3d_utils
import plot_utils
import excel_utils
from c3d_to_opensim_finals import c3d_to_trc, c3d_to_grf_mot

plot_utils.setup_chinese_font()

def analyze_cutting(c3d_file_path, output_dir='.', export_opensim=False):
    print("\n" + "="*50)
    print(f"开始分析侧切文件: {os.path.basename(c3d_file_path)}")
    print(f"Starting cutting analysis: {os.path.basename(c3d_file_path)}")
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

        # 检测冲击峰
        min_height = config.FORCE_THRESHOLD
        peaks, _ = find_peaks(force_filt, height=min_height)
        if len(peaks) == 0:
            print("  未检测到冲击峰，可能不是侧切动作 / No impact peak detected. Possibly not a cutting.")
            continue  # 跳过此力板

        peak_frame = peaks[0]
        peak_force = force_filt[peak_frame]
        print(f"  检测到冲击峰: 力值={peak_force:.1f} N, 帧号={peak_frame}")
        print(f"  Impact peak detected: force={peak_force:.1f} N, frame={peak_frame}")

        # 计算冲量（峰附近力大于阈值的区域）
        left = peak_frame
        while left > 0 and force_filt[left] > min_height:
            left -= 1
        right = peak_frame
        while right < len(force_filt)-1 and force_filt[right] > min_height:
            right += 1
        impulse = np.trapz(force_filt[left:right+1], dx=1/fs)
        print(f"  冲量={impulse:.2f} N·s / Impulse={impulse:.2f} N·s")

        # 绘图（按侧别分类）
        events = {'冲击峰 Impact peak': peak_frame}
        img_subdir = os.path.join(output_dir, 'images', side)
        os.makedirs(img_subdir, exist_ok=True)
        img_filename = os.path.basename(c3d_file_path).replace('.c3d', f'_plate{plate_idx+1}_cutting.png')
        save_path = os.path.join(img_subdir, img_filename)
        plot_utils.plot_force_with_events(
            force=force_filt,
            fs=fs,
            events=events,
            title=f'侧切分析 (力板 {plate_idx+1} - {side_display}) / Cutting (Plate {plate_idx+1} - {side_display})',
            save_path=save_path
        )
        print(f"  力曲线图已保存至: {save_path} / Force curve plot saved.")

        # 构建该力板的结果字典（长格式）
        result_row = {
            '文件名 Filename': os.path.basename(c3d_file_path),
            '动作类型 Movement type': '侧切 Cutting',
            '侧别 Side': side,
            '板号 Plate': plate_idx + 1,
            '峰值力_N Peak force (N)': peak_force,
            '冲量_Ns Impulse (N·s)': impulse,
            '峰值帧 Peak frame': peak_frame,
            '左边界帧 Left boundary': left,
            '右边界帧 Right boundary': right,
        }
        all_results.append(result_row)

    # OpenSim 导出（仍只导出第一块力板）
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
    excel_path = os.path.join(raw_folder, '侧切累计版 Cutting cumulative.xlsx')
    for row in all_results:
        excel_utils.append_to_excel(row, excel_path)
    print(f"\n已追加 {len(all_results)} 行结果至: {excel_path} / Appended {len(all_results)} rows to: {excel_path}")

    return all_results

if __name__ == '__main__':
    test_file = r'你的测试文件路径.c3d'
    test_output = '.'
    res = analyze_cutting(test_file, test_output, export_opensim=config.EXPORT_OPENSIM)
    if res:
        print("分析完成，共 {} 块力板。".format(len(res)))