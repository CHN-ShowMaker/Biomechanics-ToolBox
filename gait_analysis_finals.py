# -*- coding: utf-8 -*-
"""
步态分析脚本 (适配4.0核心模块，支持多力板和侧别配置，长格式输出)
功能：读取C3D，获取所有力板数据，根据配置文件中的 side 字段分配左右脚，
      分别检测触地/离地事件，计算各板的支撑时间、峰值力，并保存归一化曲线及图表。
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

def analyze_gait(c3d_file_path, output_dir='.', export_opensim=False):
    """
    步态分析主函数
    """
    print("\n" + "="*50)
    print(f"开始分析步态文件: {os.path.basename(c3d_file_path)}")
    print(f"Starting gait analysis: {os.path.basename(c3d_file_path)}")
    print("="*50)

    # 读取C3D
    acq = c3d_utils.read_c3d(c3d_file_path)
    print("文件读取成功！File loaded successfully!")

    # 获取多力板数据
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

    # 存储每个力板的结果（用于后续累积Excel）
    all_results = []  # 每个元素是一个力板的结果字典

    for plate_idx, plate_dict in enumerate(plates_data):
        # 从配置中获取该板的侧别，如果未指定则使用默认（板1=右脚，板2=左脚，其他显示板号）
        if plate_idx < len(plates_config):
            side = plates_config[plate_idx].get('side', None)
            if side is None:
                # 未指定侧别，按默认规则
                if plate_idx == 0:
                    side = 'right'
                elif plate_idx == 1:
                    side = 'left'
                else:
                    side = 'unknown'
        else:
            # 无配置信息，按默认规则
            if plate_idx == 0:
                side = 'right'
            elif plate_idx == 1:
                side = 'left'
            else:
                side = 'unknown'

        # 侧别显示用的中英文（用于打印和绘图标题）
        side_display = {'right': '右脚 Right', 'left': '左脚 Left', 'unknown': '未知 Unknown'}.get(side, '未知 Unknown')

        print(f"\n--- 力板 {plate_idx+1} ({side_display}) ---")
        force_raw = plate_dict['Fz']
        if np.all(force_raw == 0):
            print(f"  警告：力板 {plate_idx+1} 垂直力全零，跳过。/ Warning: Plate {plate_idx+1} Fz all zero, skipping.")
            continue

        # 滤波
        force_filt = c3d_utils.lowpass_filter(np.abs(force_raw), fs)
        time = np.arange(len(force_filt)) / fs

        # 保存归一化曲线（每个板单独保存，文件名添加板号）
        interp_func = interpolate.interp1d(time, force_filt, kind='cubic', fill_value='extrapolate')
        norm_time = np.linspace(0, 100, 101)
        norm_force = interp_func(norm_time / 100 * time[-1])
        base_name = os.path.basename(c3d_file_path).replace('.c3d', f'_plate{plate_idx+1}_curve.npy')
        curve_path = os.path.join(output_dir, 'curves', side, base_name)
        os.makedirs(os.path.dirname(curve_path), exist_ok=True)
        np.save(curve_path, norm_force)
        print(f"  归一化曲线已保存: {curve_path} / Normalized curve saved.")

        # 事件检测
        hs, to = c3d_utils.detect_gait_events(force_filt, fs)
        threshold = config.GAIT_THRESHOLD_RATIO * np.max(force_filt)
        print(f"  动态阈值: {threshold:.1f} N / Dynamic threshold: {threshold:.1f} N")
        print(f"  检测到 {len(hs)} 次触地，{len(to)} 次离地 / Detected {len(hs)} foot strikes, {len(to)} toe-offs")

        # 计算支撑时间
        n_steps = min(len(hs), len(to))
        stance_times = (to[:n_steps] - hs[:n_steps]) / fs if n_steps > 0 else []
        avg_stance = np.mean(stance_times) if stance_times else None
        print(f"  平均支撑时间: {avg_stance:.3f} s / Mean stance time: {avg_stance:.3f} s")

        peak_force = np.max(force_filt)
        print(f"  峰值力: {peak_force:.1f} N / Peak force: {peak_force:.1f} N")

        # 为该力板绘图
        events_dict = {'触地 HS': hs, '离地 TO': to}
        # 按侧别分类保存图片
        img_subdir = os.path.join(output_dir, 'images', side)
        os.makedirs(img_subdir, exist_ok=True)
        img_filename = os.path.basename(c3d_file_path).replace('.c3d', f'_plate{plate_idx+1}_gait.png')
        save_path = os.path.join(img_subdir, img_filename)
        plot_utils.plot_force_with_events(
            force=force_filt,
            fs=fs,
            events=events_dict,
            title=f'步态事件检测 (力板 {plate_idx+1} - {side_display}) / Gait Events (Plate {plate_idx+1} - {side_display})',
            save_path=save_path
        )
        print(f"  力曲线图已保存至: {save_path} / Force curve plot saved.")

        # 构建该力板的结果字典（长格式的一行）
        result_row = {
            '文件名 Filename': os.path.basename(c3d_file_path),
            '动作类型 Movement type': '步态 Gait',
            '侧别 Side': side,
            '板号 Plate': plate_idx + 1,
            '平均支撑时间_s Mean stance time (s)': avg_stance,
            '峰值力_N Peak force (N)': peak_force,
            '触地次数 Foot strikes': len(hs),
            '离地次数 Toe-offs': len(to),
            '阈值_N Threshold (N)': threshold,
        }
        all_results.append(result_row)

    # OpenSim 导出（可导出所有板，或只导出第一块，这里示例导出第一块）
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
    excel_path = os.path.join(raw_folder, '步态分析累计版 Gait cumulative.xlsx')
    for row in all_results:
        excel_utils.append_to_excel(row, excel_path)
    print(f"\n已追加 {len(all_results)} 行结果至: {excel_path} / Appended {len(all_results)} rows to: {excel_path}")

    return all_results  # 返回列表，便于批量处理收集

if __name__ == '__main__':
    # 测试用
    test_file = r'你的测试文件路径.c3d'
    test_output = '.'
    results = analyze_gait(test_file, test_output, export_opensim=config.EXPORT_OPENSIM)
    if results:
        print("\n分析完成，共 {} 块力板。".format(len(results)))