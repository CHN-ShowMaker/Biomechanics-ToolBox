# -*- coding: utf-8 -*-
"""
通道推荐工具 (suggest_channel.py) 双语版
功能：分析指定文件夹中的第一个C3D文件，找出绝对值最大的前N个模拟通道，
      并生成归一化曲线图，辅助用户选择正确的力通道。
使用方式：
    1. 命令行参数：python suggest_channel.py <文件夹路径> [--top N] [--plot]
    2. 无参数运行：进入交互模式，提示输入文件夹路径和选项
依赖：btk, numpy, matplotlib, plot_utils, scipy
"""

import os
import sys
import argparse
import btk
import numpy as np
from scipy.signal import butter, filtfilt

# 尝试导入绘图相关库
try:
    import matplotlib.pyplot as plt
    import plot_utils
    HAS_PLOT = True
except ImportError:
    HAS_PLOT = False
    print("警告：未安装 matplotlib 或 plot_utils，无法生成曲线图。")
    print("Warning: matplotlib or plot_utils not installed. Plots will not be generated.")

def get_first_c3d(folder_path):
    """获取文件夹中第一个 .c3d 文件路径（按名称排序）"""
    folder_path = os.path.normpath(folder_path)
    if not os.path.isdir(folder_path):
        raise ValueError(f"文件夹不存在: {folder_path} / Folder does not exist: {folder_path}")
    files = [f for f in os.listdir(folder_path) if f.lower().endswith('.c3d')]
    if not files:
        raise ValueError(f"文件夹中没有 .c3d 文件: {folder_path} / No .c3d files in folder: {folder_path}")
    return os.path.join(folder_path, sorted(files)[0])

def compute_channel_stats(c3d_file):
    """读取C3D文件，返回模拟通道的标签、最大值（绝对值）、原始数据、排序索引"""
    reader = btk.btkAcquisitionFileReader()
    reader.SetFilename(c3d_file)
    reader.Update()
    acq = reader.GetOutput()

    analog_labels = []
    analog_max = []
    analog_data = []  # 保存原始数据用于绘图

    for i in range(acq.GetAnalogs().GetItemNumber()):
        analog = acq.GetAnalog(i)
        values = analog.GetValues()
        if values.ndim == 2 and values.shape[1] > 1:
            max_val = np.nanmax(np.abs(values))
            data_1d = values[:, 0]
        else:
            max_val = np.nanmax(np.abs(values.flatten()))
            data_1d = values.flatten()
        analog_labels.append(analog.GetLabel())
        analog_max.append(max_val)
        analog_data.append(data_1d)

    sorted_indices = np.argsort(analog_max)[::-1]
    return analog_labels, analog_max, analog_data, sorted_indices, acq

def plot_channel(data, fs, channel_label, max_val, save_path):
    """生成单个通道的归一化力曲线图"""
    from scipy import interpolate
    cutoff = 50
    nyq = 0.5 * fs
    if cutoff < nyq:
        normal_cutoff = cutoff / nyq
        b, a = butter(4, normal_cutoff, btype='low')
        force_filt = filtfilt(b, a, data)
    else:
        force_filt = data
    force_filt = np.abs(force_filt)

    original_time = np.arange(len(force_filt)) / fs
    interp_func = interpolate.interp1d(original_time, force_filt, kind='cubic',
                                       fill_value='extrapolate', bounds_error=False)
    norm_time = np.linspace(0, 100, 101)
    norm_force = interp_func(norm_time / 100 * original_time[-1])

    plt.figure(figsize=(6, 3))
    plt.plot(norm_time, norm_force, 'b-', linewidth=1.2)
    plt.xlabel('归一化时间 (%) / Normalized time (%)')
    plt.ylabel('力 (N) / Force (N)')
    plt.title(f'{channel_label} (max={max_val:.1f})')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=120)
    plt.close()

def process_folder(folder_path, top_n=3, plot=False):
    try:
        c3d_file = get_first_c3d(folder_path)
        print(f"分析文件: {os.path.basename(c3d_file)} / Analyzing file: {os.path.basename(c3d_file)}")
    except ValueError as e:
        print(e)
        return

    labels, max_vals, data, sorted_indices, acq = compute_channel_stats(c3d_file)
    fs = acq.GetAnalogFrequency()

    print(f"\n模拟通道最大值排序（前{top_n}）：/ Analog channel maximum values (top {top_n}):")
    print("  排名 Rank | 编号 Index | 标签 Label         | 最大值 Max value")
    print("  ----------|------------|-------------------|--------------")
    for rank, idx in enumerate(sorted_indices[:top_n], start=1):
        max_val_str = f"{max_vals[idx]:8.2f}" if not np.isnan(max_vals[idx]) else "     NaN"
        print(f"  {rank:4d}     | {idx:4d}      | {labels[idx]:16s} | {max_val_str}")

    if plot and HAS_PLOT:
        img_dir = os.path.join(folder_path, 'suggest_images')
        os.makedirs(img_dir, exist_ok=True)
        print(f"\n生成曲线图保存至: {img_dir} / Plots saved to: {img_dir}")
        for rank, idx in enumerate(sorted_indices[:top_n], start=1):
            if np.isnan(max_vals[idx]):
                print(f"  跳过 NaN 通道: {labels[idx]} / Skipping NaN channel: {labels[idx]}")
                continue
            save_path = os.path.join(img_dir, f"rank{rank}_{labels[idx]}.png")
            plot_channel(data[idx], fs, labels[idx], max_vals[idx], save_path)
            print(f"  已生成: {os.path.basename(save_path)} / Generated: {os.path.basename(save_path)}")
    elif plot and not HAS_PLOT:
        print("无法生成曲线图：缺少 matplotlib 或 plot_utils")
        print("Cannot generate plots: matplotlib or plot_utils missing")

def main():
    parser = argparse.ArgumentParser(description='通道推荐工具（交互式）', add_help=False)
    parser.add_argument('folder', nargs='?', help='包含C3D文件的文件夹路径')
    parser.add_argument('--top', type=int, default=3, help='显示前N个候选通道（默认3）')
    parser.add_argument('--plot', action='store_true', help='生成候选通道的曲线图')
    args, remaining = parser.parse_known_args()

    if args.folder is None:
        print("通道推荐工具（交互式） / Channel Suggestion Tool (Interactive)")
        folder = input("请输入包含C3D文件的文件夹路径: ").strip()
        print("Enter folder path containing C3D files:")
        folder = folder.strip().lstrip('\u202a').lstrip('\u200e').lstrip('\u200f')
        if not os.path.isdir(folder):
            print("文件夹不存在或路径无效。/ Folder does not exist or invalid path.")
            return
        top_input = input("请输入要显示的候选通道数量 (默认3): ").strip()
        top_n = int(top_input) if top_input.isdigit() else 3
        plot_choice = input("是否生成力曲线图？(y/n, 默认 n): ").strip().lower()
        plot = plot_choice == 'y'
        process_folder(folder, top_n=top_n, plot=plot)
    else:
        folder = args.folder.strip().lstrip('\u202a').lstrip('\u200e').lstrip('\u200f')
        process_folder(folder, top_n=args.top, plot=args.plot)

if __name__ == '__main__':
    main()